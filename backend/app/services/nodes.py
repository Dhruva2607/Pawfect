"""
LangGraph Nodes: Conversational Intake, Hybrid Retrieval, and Reasoning & Scoring.
[FROM MARKDOWN] matches Step 2.2, Step 2.3, Step 2.4, Step 6.1, and Step 6.2.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.services.state import MatchmakerState, LifestyleConstraints
from app.services.llm import get_chat_llm
from app.services.retrieval import get_newest_available_pets, hybrid_search_pets
from app.services.matching_schema import get_chat_question_flow, get_intake_prompt_dimensions_block

logger = logging.getLogger(__name__)


# ── Pydantic Output Models for LLM Structured Extraction & Scoring ───

class IntakeAnalysisOutput(BaseModel):
    """Structured extraction returned by Conversational Intake Node."""
    extracted_constraints: LifestyleConstraints
    is_sufficient_for_search: bool = Field(
        ...,
        description="True if we have enough info (species, living space, energy/activity level, family setup) to find matches"
    )
    is_unsupported_or_irrelevant: bool = Field(
        default=False,
        description="True if the user is asking for pets other than cats/dogs (e.g. parrots, birds, reptiles, fish, rabbits, etc.) or asking off-topic/irrelevant questions."
    )
    follow_up_question: str = Field(
        ...,
        description=(
            "Warm, conversational follow-up question. "
            "CRITICAL: MUST ASK EXACTLY ONE FOCUSED QUESTION at a time. "
            "Never combine multiple questions. "
            "If is_unsupported_or_irrelevant is True, inform the user that PawFect is only an adoption center for cats and dogs, and ask if they are looking to adopt a dog or cat instead."
        )
    )
    suggested_quick_replies: List[str] = Field(
        default_factory=list,
        description=(
            "Concise suggested quick-reply chips for mobile UI. "
            "CRITICAL: Must provide direct, complete options that fully answer the ONE question asked in follow_up_question, "
            "so the user can tap a suggestion instead of typing. "
            "For example, if asking species: ['Looking for a Dog', 'Looking for a Cat', 'Open to either']. "
            "If asking home: ['Apartment', 'House with yard', 'House without yard']. "
            "If asking activity: ['Calm / low energy', 'Moderate daily walks', 'Active & energetic']. "
            "If asking kids/pets: ['No kids or pets', 'Have children', 'Have other pets', 'Have kids and pets']."
        )
    )
    search_query: str = Field(
        default="",
        description="Synthesized descriptive semantic query summarizing adopter's ideal companion"
    )


class SinglePetCompatibility(BaseModel):
    """Grounded compatibility evaluation for a candidate pet."""
    pet_id: str
    pet_name: str
    compatibility_score: int = Field(..., ge=0, le=100, description="Match score from 0 to 100%")
    pros: List[str] = Field(..., description="Exact alignment points with adopter's lifestyle")
    caveats: List[str] = Field(..., description="Watch-outs, behavioral considerations, or potential frictions")
    reasoning_summary: str = Field(..., description="1-2 sentence warm, grounded explanation")
    comparison_to_hero: Optional[str] = Field(
        default=None,
        description="For candidate matches ranked below the #1 top Hero pet, provide a clear 1-sentence comparison explaining specifically why this pet is not as perfect a match compared to the top Hero pet (e.g. higher activity/exercise requirement, requires a yard unlike the apartment-friendly hero pet, or needs specialized training). Must be null for the #1 top match itself."
    )


class MultiPetScoringOutput(BaseModel):
    """Structured collection of evaluations for top candidates."""
    evaluations: List[SinglePetCompatibility]
    overall_response: str = Field(
        ...,
        description="Warm, empathetic message introducing the top pet match (Hero Pet) and briefly noting the alternative matches along with why each is not as perfect a match compared to the top pet (e.g. 'Meet Bella, your #1 match! While Charlie and Max are also wonderful, Charlie requires significantly more yard space and Max has higher energy demands than your apartment routine.')."
    )


def _apply_species_override(constraints: Dict[str, Any], user_message: str) -> Dict[str, Any]:
    """
    The newest user message wins when it explicitly names a single species.
    Prevents a previous 'dog' recommendation from sticking when the user later asks for a cat.
    """
    text = (user_message or "").lower()
    mentions_dog = re.search(r"\bdogs?\b", text) is not None
    mentions_cat = re.search(r"\bcats?\b", text) is not None

    if mentions_dog == mentions_cat:
        return constraints

    updated = dict(constraints)
    updated["species"] = "dog" if mentions_dog else "cat"
    return updated


_SIGNUP_FIELD_KEYWORDS = {
    "housing_type": ("apartment", "house", "yard", "living space", "home type", "where do you live"),
    "has_children": ("children", "kids", "toddler", "family"),
    "has_other_pets": ("other pets", "resident pets", "existing pets", "already have a dog", "already have a cat"),
    "energy_budget": ("energy", "activity level", "exercise", "daily routine", "active"),
}

_CHAT_QUESTION_FLOW = get_chat_question_flow()


def _next_missing_question(constraints: Dict[str, Any]) -> tuple[str, List[str]]:
    """Return the next unanswered question and quick replies, skipping already-known fields."""
    for field, question, quick_replies in _CHAT_QUESTION_FLOW:
        if constraints.get(field) is None:
            return question, quick_replies
    return (
        "Do you or anyone in your home have pet allergies or need a low-shedding pet?",
        ["No allergies", "Yes, need low-shedding"],
    )


def _repeats_known_signup_field(question: str, prior_constraints: Dict[str, Any]) -> bool:
    """Detect whether a generated follow-up question re-asks a field already known from sign-up."""
    q_lower = (question or "").lower()
    for field, keywords in _SIGNUP_FIELD_KEYWORDS.items():
        if prior_constraints.get(field) is not None and any(kw in q_lower for kw in keywords):
            return True
    return False


# ── Deterministic constraint merging & extraction (P2) ───────────────
#
# The intake LLM does not reliably echo every previously-known constraint back
# on each turn, and a prompt instruction alone cannot stop it re-asking an
# answered question. Two deterministic helpers below enforce the contract:
#
#   1. merge_constraints() never lets a later blank erase an earlier answer.
#   2. extract_from_replies() maps the exact quick-reply chips the mobile UI
#      sends back to canonical values, so a tapped answer is always recorded
#      even if the LLM omits it.

def merge_constraints(prior: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge extracted constraints over prior ones without losing known values.

    A key is only overwritten when the new value is meaningful (not None and not
    an empty string). This is the core fix for the repeat-question loop: LLM
    responses that omit a field can no longer wipe it from the session.
    """
    merged: Dict[str, Any] = {
        k: v for k, v in (prior or {}).items() if v is not None and v != ""
    }
    for key, value in (new or {}).items():
        if value is None or value == "":
            continue
        merged[key] = value
    return merged


# Quick-reply chip text -> canonical adopter value, keyed by adopter field.
# Chips come from matching_schema.MATCHING_DIMENSIONS.chat_quick_replies and are
# sent verbatim by the Android client when tapped.
_REPLY_VALUES: Dict[str, Dict[str, Any]] = {
    "species": {
        "looking for a dog": "dog",
        "looking for a cat": "cat",
        "open to either": "any",
    },
    "preferred_age_group": {
        "puppy or kitten": "puppy_or_kitten",
        "kitten": "puppy_or_kitten",
        "puppy": "puppy_or_kitten",
        "young (1-3 yrs)": "young",
        "adult (3-7 yrs)": "adult",
        "senior (7+ yrs)": "senior",
        "any age": "any",
    },
    "preferred_size": {
        "small": "small",
        "medium": "medium",
        "large": "large",
        "any size": "any",
    },
    "grooming_tolerance": {
        "low maintenance": "low",
        "moderate brushing": "moderate",
        "high grooming is fine": "high",
    },
    "noise_tolerance": {
        "quiet (minimal barking/meowing)": "quiet",
        "quiet": "quiet",
        "vocal pets are fine": "vocal",
        "moderate": "moderate",
    },
    "daily_alone_hours": {
        "0-3 hours": 2,
        "4-6 hours": 5,
        "6+ hours": 7,
    },
    "experience_level": {
        "first-time owner": "first_time",
        "first time owner": "first_time",
        "experienced owner": "experienced",
    },
    "housing_type": {
        "house with yard": "house_with_yard",
        "house without yard": "house_without_yard",
        "apartment": "apartment",
    },
    "energy_budget": {
        "calm & low energy": 2,
        "calm and low energy": 2,
        "moderate daily walks": 3,
        "high energy & active": 5,
        "high energy and active": 5,
    },
    "has_children": {
        "no children": False,
        "have young children": True,
        "have children": True,
    },
    "has_other_pets": {
        "no other pets": False,
        "have other pets": True,
    },
    "allergies": {
        "no allergies": False,
        "yes, need low-shedding": True,
        "yes, need low shedding": True,
    },
}

# Chips whose text names more than one dimension.
_COMBINED_REPLIES: Dict[str, Dict[str, Any]] = {
    "have children & pets": {"has_children": True, "has_other_pets": True},
    "have children and pets": {"has_children": True, "has_other_pets": True},
    "no children or pets": {"has_children": False, "has_other_pets": False},
    "no children or other pets": {"has_children": False, "has_other_pets": False},
    "no kids or pets": {"has_children": False, "has_other_pets": False},
}


def _normalize_reply(text: str) -> str:
    """Lowercase and collapse whitespace so chip text compares reliably."""
    return " ".join((text or "").lower().split())


# Keywords that identify which dimension a follow-up question is asking about.
# Used to stop the model re-asking an already-answered question.
_DIMENSION_QUESTION_KEYWORDS: Dict[str, tuple] = {
    "species": ("dog or a cat", "dog or cat", "which species"),
    "preferred_age_group": ("age group", "how old", "puppy or kitten"),
    "preferred_size": ("what size", "size pet", "size preference"),
    "grooming_tolerance": ("grooming", "brushing", "coat upkeep"),
    "noise_tolerance": ("noise", "barking", "meowing", "vocal"),
    "daily_alone_hours": ("hours a day", "spend alone", "left alone"),
    "experience_level": ("owned a pet", "first-time", "first time owner", "experience"),
    "housing_type": ("living space", "what kind of home", "apartment or house"),
    "energy_budget": ("activity level", "energy", "daily walks"),
    "has_children": ("children", "kids"),
    "has_other_pets": ("other pets", "resident pets"),
    "allergies": ("allerg", "low-shedding", "shedding"),
}


def _repeats_known_constraint(question: str, constraints: Dict[str, Any]) -> bool:
    """
    True when the question asks about a dimension that already has an answer.

    This operates on the merged constraints (not just sign-up fields), so a
    question the adopter already answered in chat is also suppressed.
    """
    q_lower = (question or "").lower()
    if not q_lower:
        return False

    for field, keywords in _DIMENSION_QUESTION_KEYWORDS.items():
        if constraints.get(field) is None:
            continue
        if any(kw in q_lower for kw in keywords):
            return True
    return False


def extract_from_replies(message: str) -> Dict[str, Any]:
    """
    Extract constraints from a message that is (or contains) quick-reply chip text.

    Chips are sent verbatim by the client, so an exact normalized match is safe.
    Substring matching is restricted to distinctive multi-word chips to avoid
    false positives such as "large" inside "large yard".
    """
    text = _normalize_reply(message)
    if not text:
        return {}

    found: Dict[str, Any] = {}

    for phrase, values in _COMBINED_REPLIES.items():
        if text == phrase:
            found.update(values)

    for field, mapping in _REPLY_VALUES.items():
        if field in found:
            continue
        for phrase, value in mapping.items():
            if text == phrase or (len(phrase) >= 12 and phrase in text):
                found[field] = value
                break

    return found


# ── Node 1: Conversational Intake Node ───────────────────────────────

def conversational_intake_node(state: MatchmakerState) -> Dict[str, Any]:
    """
    Step 2.2: Conversational Intake Node.
    Ingests natural language dialogue, extracts lifestyle parameters, and evaluates
    whether critical dimensions (species, age, size, grooming, noise, etc.) have been gathered
    without repeating fields already captured during sign-up.
    """
    user_msg = state.get("user_message", "")
    history = state.get("conversation_history", [])
    prior_constraints = state.get("extracted_constraints", {})

    logger.info("Executing Conversational Intake Node. User message: '%s'", user_msg)

    # Fast-path for "New arrivals / just listed" requests
    msg_lower = (user_msg or "").lower()
    if "new arrival" in msg_lower or "just listed" in msg_lower or "newest" in msg_lower:
        updated_constraints = _apply_species_override(dict(prior_constraints), user_msg)
        updated_constraints["sort_by"] = "newest"
        return {
            "extracted_constraints": updated_constraints,
            "is_complete": True,
            "search_queries": ["newly listed available pets"],
            "response_message": "Let me pull up the newest arrivals from our partner shelters for you!",
            "quick_replies": [],
            "next_node": "hybrid_retrieval",
        }

    # Format dialogue history
    dialogue_snippets = []
    for turn in history[-6:]:  # Keep recent context
        dialogue_snippets.append(f"{turn.get('role', 'user').capitalize()}: {turn.get('content', '')}")
    if user_msg:
        dialogue_snippets.append(f"User: {user_msg}")
    dialogue_text = "\n".join(dialogue_snippets)

    already_known_keys = [k for k, v in prior_constraints.items() if v is not None]

    system_prompt = (
        "You are an empathetic, expert Pet Adoption Counselor for 'PawFect'.\n"
        "Your mission is to understand an adopter's real lifestyle to ensure a long-term, stable pet adoption.\n\n"
        "STRICT CENTER SCOPE & RELEVANCE RULE:\n"
        "- PawFect is EXCLUSIVELY an adoption center for CATS and DOGS.\n"
        "- We do NOT have, shelter, adopt, or sell any other animals (such as parrots, birds, reptiles, rabbits, hamsters, turtles, fish, ferrets, etc.).\n"
        "- If the user asks an irrelevant question (e.g. trivia, coding, off-topic banter) OR asks if we have or adopt non-cat/non-dog pets (like parrots, birds, reptiles, rabbits, etc.):\n"
        "  1. Set is_unsupported_or_irrelevant=True and is_sufficient_for_search=False.\n"
        "  2. In follow_up_question, state politely and clearly that PawFect is only an adoption center for cats and dogs, and ask if they are looking to adopt a dog or a cat instead.\n"
        "  3. Set suggested_quick_replies to ['Looking for a Dog', 'Looking for a Cat'].\n"
        "  4. Do NOT set species constraint to any unsupported animal.\n\n"
        "CRITICAL SIGN-UP & NO-REPEAT RULE:\n"
        "- Fields already present in Prior Extracted Constraints (such as housing_type, has_children, has_other_pets, energy_budget from sign-up) are ALREADY KNOWN.\n"
        "- NEVER ask about housing_type, has_children, has_other_pets, or energy_budget if they are already set in Prior Extracted Constraints.\n"
        "- NEVER repeat any question for a dimension that is already present in Prior Extracted Constraints.\n\n"
        "CRITICAL ONE-QUESTION-AT-A-TIME & MATCHING SUGGESTIONS RULE:\n"
        "- When requesting more information, ask EXACTLY ONE focused question at a time. NEVER combine multiple questions into one message.\n"
        "- Provide 2 to 4 concise suggested_quick_replies that DIRECTLY and FULLY answer that ONE question.\n"
        "- Focus on gathering the missing pet & lifestyle preferences not set during sign-up:\n"
        f"{get_intake_prompt_dimensions_block()}\n"
        "  (Only ask housing_type, energy_budget, has_children, or has_other_pets if they are missing from Prior Extracted Constraints.)\n\n"
        "INSTRUCTIONS:\n"
        "- Merge all previously extracted constraints with any newly shared facts in the conversation.\n"
        "- The newest user message ALWAYS wins: if the user asks for a different species than before, update species to the newly requested one (only 'dog', 'cat', or 'any').\n"
        "- Set is_sufficient_for_search=True once we have species PLUS at least 3 of the chat-specific dimensions (preferred_age_group, preferred_size, grooming_tolerance, noise_tolerance, daily_alone_hours, experience_level, allergies) alongside the sign-up constraints.\n"
        "- If NOT sufficient yet, ask EXACTLY ONE natural, conversational question covering the next missing dimension with matching quick replies.\n"
        "- If SUFFICIENT and RELEVANT, set is_sufficient_for_search=True and synthesize a comprehensive semantic search_query summarizing their sign-up profile and chat preferences."
    )

    human_prompt = (
        f"Already Known Fields (DO NOT ASK ABOUT THESE): {json.dumps(already_known_keys)}\n"
        f"Prior Extracted Constraints: {json.dumps(prior_constraints)}\n\n"
        f"Conversation So Far:\n{dialogue_text}\n\n"
        "Extract the updated constraints and decide whether we are ready to retrieve pet matches."
    )

    llm = get_chat_llm(temperature=0.1)
    structured_llm = llm.with_structured_output(IntakeAnalysisOutput)

    try:
        analysis: IntakeAnalysisOutput = structured_llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": human_prompt}
        ])

        if analysis.is_unsupported_or_irrelevant:
            response_msg = analysis.follow_up_question
            lower_resp = response_msg.lower()
            if "cat" not in lower_resp or "dog" not in lower_resp:
                response_msg = (
                    "PawFect is exclusively an adoption center for cats and dogs! "
                    "We do not have parrots, birds, or other animals available for adoption. "
                    "Would you like help finding a loving dog or cat to adopt?"
                )
            quick_replies = analysis.suggested_quick_replies or ["Looking for a Dog", "Looking for a Cat"]
            return {
                "extracted_constraints": prior_constraints,
                "is_complete": False,
                "response_message": response_msg,
                "quick_replies": quick_replies,
                "next_node": "await_user"
            }

        llm_constraints = analysis.extracted_constraints.model_dump(exclude_none=True)
        # Record answers that arrived as quick-reply chips even when the LLM omits them.
        chip_constraints = extract_from_replies(user_msg)
        # Merge without ever letting a blank response erase a known constraint.
        merged_constraints = merge_constraints(prior_constraints, llm_constraints)
        merged_constraints = merge_constraints(merged_constraints, chip_constraints)
        # The newest message wins for an explicitly named species.
        merged_constraints = _apply_species_override(merged_constraints, user_msg)

        if analysis.is_sufficient_for_search:
            search_query = analysis.search_query or (
                f"{merged_constraints.get('species', 'pet')} "
                f"{merged_constraints.get('preferred_age_group', '')} "
                f"{merged_constraints.get('preferred_size', '')} "
                f"grooming {merged_constraints.get('grooming_tolerance', 'any')} "
                f"noise {merged_constraints.get('noise_tolerance', 'any')} "
                f"suitable for {merged_constraints.get('housing_type', 'home')} with "
                f"energy level {merged_constraints.get('energy_budget', 3)}/5"
            ).strip()
            species = merged_constraints.get("species")
            if species and species.lower() not in search_query.lower():
                search_query = f"{species} {search_query}"
            return {
                "extracted_constraints": merged_constraints,
                "is_complete": True,
                "search_queries": [search_query],
                "response_message": "Thank you! I have a wonderful picture of your lifestyle and preferences. Searching our shelters for your ideal companion...",
                "quick_replies": [],
                "next_node": "hybrid_retrieval"
            }
        else:
            follow_up_q = analysis.follow_up_question
            quick_replies = analysis.suggested_quick_replies
            # Only replace the model's question when it is asking for something we
            # already know; never override an otherwise useful follow-up.
            if _repeats_known_constraint(follow_up_q, merged_constraints):
                follow_up_q, quick_replies = _next_missing_question(merged_constraints)
            return {
                "extracted_constraints": merged_constraints,
                "is_complete": False,
                "response_message": follow_up_q,
                "quick_replies": quick_replies,
                "next_node": "await_user"
            }

    except Exception as e:
        logger.error("Error in conversational intake node: %s. Using graceful heuristic fallback.", e)
        fallback_q, fallback_qr = _next_missing_question(prior_constraints)

        return {
            "extracted_constraints": prior_constraints,
            "is_complete": False,
            "response_message": fallback_q,
            "quick_replies": fallback_qr,
            "next_node": "await_user"
        }


# ── Node 2: Hybrid Retrieval Node ────────────────────────────────────

def hybrid_retrieval_node(state: MatchmakerState) -> Dict[str, Any]:
    """
    Step 2.3: Hybrid Retrieval Node.
    Executes MQL pre-filters alongside Vector Search over candidate bios.
    When species is 'any' (or unspecified), retrieves top matches for both dogs and cats.
    """
    constraints = state.get("extracted_constraints", {})
    queries = state.get("search_queries", [])
    query_text = queries[0] if queries else "loving companion pet"

    logger.info("Executing Hybrid Retrieval Node for query: '%s'", query_text)

    if constraints.get("sort_by") == "newest":
        candidates = get_newest_available_pets(constraints=constraints, top_k=5)
        return {
            "candidate_matches": candidates,
            "next_node": "reasoning_scoring",
        }

    species = (constraints.get("species") or "").lower()
    if species in ("dog", "cat"):
        candidates = hybrid_search_pets(
            query_text=query_text,
            constraints=constraints,
            top_k=3
        )
    else:
        dog_candidates = hybrid_search_pets(
            query_text=query_text,
            constraints={**constraints, "species": "dog"},
            top_k=3
        )
        cat_candidates = hybrid_search_pets(
            query_text=query_text,
            constraints={**constraints, "species": "cat"},
            top_k=3
        )
        candidates = sorted(
            dog_candidates + cat_candidates,
            key=lambda p: p.get("score", 0.0),
            reverse=True,
        )

    return {
        "candidate_matches": candidates,
        "next_node": "reasoning_scoring"
    }


# ── Node 3: Reasoning & Scoring Node ─────────────────────────────────

RELAXED_MATCH_SCORE_CAP = 84


def _apply_relaxed_match_disclosure(
    evaluations: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Enforce honest scoring for near-match candidates.

    Retrieval may drop soft constraints (size, grooming, noise, housing, energy)
    to fill the candidate list. Prompt instructions alone are not a guarantee, so
    the cap and the caveat are applied deterministically here:
      - score is capped at RELAXED_MATCH_SCORE_CAP
      - a caveat naming the relaxed preference is appended if the model omitted it
    """
    by_id = {c.get("_id"): c for c in candidates}
    by_name = {c.get("name"): c for c in candidates}

    for ev in evaluations:
        pet = by_id.get(ev.get("pet_id")) or by_name.get(ev.get("pet_name"))
        if not pet or not pet.get("is_relaxed_match"):
            continue

        relaxed_fields = pet.get("relaxed_fields") or []
        if ev.get("compatibility_score", 0) > RELAXED_MATCH_SCORE_CAP:
            ev["compatibility_score"] = RELAXED_MATCH_SCORE_CAP

        if relaxed_fields:
            human = [f.replace("_", " ") for f in relaxed_fields]
            note = f"Near match: your {', '.join(human)} preference differs from this pet."
            caveats = list(ev.get("caveats") or [])
            if not any(note.lower()[:30] in (c or "").lower() for c in caveats):
                caveats.append(note)
            ev["caveats"] = caveats

        ev["is_relaxed_match"] = True
        ev["relaxed_fields"] = relaxed_fields

    return evaluations


def reasoning_scoring_node(state: MatchmakerState) -> Dict[str, Any]:
    """
    Step 2.4: Reasoning & Scoring Node.
    Evaluates candidate pets against adopter lifestyle.
    Enforces strict grounding (0.1 temp) [FROM MARKDOWN: Step 6.1] and structured Pydantic output.
    """
    constraints = state.get("extracted_constraints", {})
    candidates = state.get("candidate_matches", [])[:6]

    if not candidates:
        logger.warning("No candidate pets found for scoring.")
        return {
            "evaluations": [],
            "response_message": "I searched our shelter database, but couldn't find a pet strictly matching all criteria. Let's adjust a few preferences!",
            "quick_replies": ["Broaden species", "Allow any housing requirement"]
        }

    logger.info("Executing Reasoning & Scoring Node for %d candidate pets.", len(candidates))

    # Build pet profile grounding dossier
    dossier_entries = []
    for pet in candidates:
        dossier_entries.append({
            "id": pet.get("_id"),
            "name": pet.get("name"),
            "species": pet.get("species"),
            "breed": pet.get("breed"),
            "age_months": pet.get("age_months"),
            "age_group": pet.get("age_group"),
            "size": pet.get("size"),
            "weight_lbs": pet.get("weight_lbs"),
            "energy_level": pet.get("energy_level"),
            "grooming_needs": pet.get("grooming_needs"),
            "shedding_level": pet.get("shedding_level"),
            "noise_level": pet.get("noise_level"),
            "alone_time_tolerance": pet.get("alone_time_tolerance"),
            "experience_level_required": pet.get("experience_level_required"),
            "training_level": pet.get("training_level"),
            "coat_type": pet.get("coat_type"),
            "special_needs": pet.get("special_needs"),
            "housing_requirement": pet.get("housing_requirement"),
            "good_with_kids": pet.get("good_with_kids"),
            "good_with_other_pets": pet.get("good_with_other_pets"),
            "temperament": pet.get("temperament"),
            "exercise_needs": pet.get("exercise_needs"),
            "quirks": pet.get("quirks"),
            "triggers": pet.get("triggers"),
            "bio_text": pet.get("bio_text"),
            "hypoallergenic": pet.get("hypoallergenic"),
            # Present when this pet was only returned because a constraint was
            # dropped to fill the candidate list (see retrieval.hybrid_search_pets).
            "is_relaxed_match": pet.get("is_relaxed_match", False),
            "relaxed_fields": pet.get("relaxed_fields", []),
            "shelter_name": pet.get("shelter_name"),
            "shelter_city": pet.get("shelter_city"),
            "adoption_fee": pet.get("adoption_fee"),
            "vaccinated": pet.get("vaccinated"),
            "neutered": pet.get("neutered"),
            "microchipped": pet.get("microchipped"),
            "requires_yard": pet.get("requires_yard"),
            "min_experience": pet.get("min_experience"),
            "not_suitable_for_young_children": pet.get("not_suitable_for_young_children"),
            "ideal_adopter_notes": pet.get("ideal_adopter_notes"),
        })

    system_prompt = (
        "You are the Lead Adoption Counselor and Compatibility Engine for PawFect.\n"
        "Your task is to analyze candidate shelter pets and calculate grounded, explainable compatibility scores.\n\n"
        "STRICT GROUNDING RULES [GUARDRAILS - NO HALLUCINATIONS]:\n"
        "1. Use ONLY the pet profile data provided in the candidate dossier. Do NOT invent traits.\n"
        "2. Compatibility Score must be between 0 and 100%:\n"
        "   - 85-99%: High alignment across housing, energy, kids, and pets.\n"
        "   - 70-84%: Good alignment with minor lifestyle adjustments needed.\n"
        "   - Below 70%: Noticeable mismatch on energy, space, or household safety.\n"
        "3. Pros: Provide 1-2 concise bullet points.\n"
        "4. Caveats: Provide 1 concise bullet point.\n"
        "5. Reasoning summary: 1 brief sentence.\n"
        "6. Comparison to #1 Hero Match: For candidate rank #1 (the Hero Pet), comparison_to_hero MUST be None. For all other candidate matches (rank #2 and lower), provide 1 clear, objective sentence in comparison_to_hero explaining specifically why they are not as perfect a match compared to the #1 Hero Pet (e.g., energy level differences, specific space/housing constraints, or behavioral needs).\n"
        "7. Overall response: Warm, encouraging message presenting the #1 Hero Match to the adopter, and briefly summarizing the alternative matches explaining why each is not quite as perfect a fit compared to the hero pet.\n"
        "8. NEAR-MATCH DISCLOSURE: A candidate may carry \"is_relaxed_match\": true with \"relaxed_fields\" listing adopter preferences the search had to drop (for example housing_type or energy_budget). For such pets you MUST: (a) cap the score at 84, (b) name the relaxed preference as a caveat in plain language (e.g. \"your household profile differs on living space\"), and (c) NEVER describe the pet as fitting a preference that appears in relaxed_fields. Honesty about a near-match is mandatory."
    )

    relaxed_pairs = [
        (e.get("name"), e.get("relaxed_fields"))
        for e in dossier_entries
        if e.get("is_relaxed_match") and e.get("relaxed_fields")
    ]
    relaxed_note = ""
    if relaxed_pairs:
        relaxed_note = (
            "\n\nNEAR-MATCH CANDIDATES (constraints relaxed to fill the list):\n"
            + "\n".join(f"- {name}: relaxed {', '.join(fields)}" for name, fields in relaxed_pairs)
        )

    human_prompt = (
        f"Adopter Lifestyle Constraints:\n{json.dumps(constraints, indent=2)}\n\n"
        f"Candidate Shelter Pets Dossier:\n{json.dumps(dossier_entries, indent=2)}"
        f"{relaxed_note}\n\n"
        "Generate grounded compatibility evaluations for each candidate and highlight the best match."
    )

    llm = get_chat_llm(temperature=0.1)
    structured_llm = llm.with_structured_output(MultiPetScoringOutput)

    try:
        scoring_result: MultiPetScoringOutput = structured_llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": human_prompt}
        ])

        evaluations_dict = [e.model_dump() for e in scoring_result.evaluations]
        evaluations_dict = _apply_relaxed_match_disclosure(evaluations_dict, candidates)
        # Sort evaluations by compatibility score descending
        evaluations_dict.sort(key=lambda x: x["compatibility_score"], reverse=True)

        top_match_name = evaluations_dict[0]["pet_name"] if evaluations_dict else "your match"

        # Guarantee comparison_to_hero rules: rank #1 has None, rank #2+ has comparative reason
        for idx, ev in enumerate(evaluations_dict):
            if idx == 0:
                ev["comparison_to_hero"] = None
            elif not ev.get("comparison_to_hero"):
                caveat = (ev.get("caveats") or ["higher activity or space needs"])[0]
                ev["comparison_to_hero"] = f"Compared to {top_match_name}, {ev['pet_name']} has {caveat.lower()}."

        return {
            "evaluations": evaluations_dict,
            "response_message": scoring_result.overall_response,
            "quick_replies": [f"Learn more about {top_match_name}", "See alternative matches", "Show new arrivals", "Start Adoption Application"]
        }

    except Exception as e:
        logger.error("Error in reasoning & scoring node: %s. Using heuristic scoring fallback.", e)
        # Fallback scoring
        fallback_evals = []
        for p in candidates:
            score = int(p.get("score", 0.7) * 100)
            score = max(50, min(98, score))
            fallback_evals.append({
                "pet_id": p.get("_id"),
                "pet_name": p.get("name"),
                "compatibility_score": score,
                "pros": [
                    f"Matches your housing requirement ({p.get('housing_requirement')})",
                    f"Temperament tags: {', '.join(p.get('temperament', []))}"
                ],
                "caveats": [
                    f"Exercise needs: {p.get('exercise_needs', 'Standard daily activity')}"
                ],
                "reasoning_summary": f"{p.get('name')} is a wonderful {p.get('breed')} well-suited for your lifestyle."
            })

        fallback_evals = _apply_relaxed_match_disclosure(fallback_evals, candidates)
        fallback_evals.sort(key=lambda x: x["compatibility_score"], reverse=True)
        top_name = fallback_evals[0]["pet_name"] if fallback_evals else "your match"

        for idx, ev in enumerate(fallback_evals):
            if idx == 0:
                ev["comparison_to_hero"] = None
            else:
                caveat = (ev.get("caveats") or ["higher exercise needs"])[0]
                ev["comparison_to_hero"] = f"Compared to {top_name}, {ev['pet_name']} has {caveat.lower()}."

        if len(fallback_evals) > 1:
            alt_notes = [f"{ev['pet_name']} ({ev['comparison_to_hero']})" for ev in fallback_evals[1:]]
            alt_text = f" While other options like {', '.join(alt_notes)} are also available, {top_name} remains your best overall match!"
        else:
            alt_text = ""

        return {
            "evaluations": fallback_evals,
            "response_message": f"I found wonderful companion matches for your lifestyle! Meet {top_name}, your top candidate.{alt_text}",
            "quick_replies": [f"View {top_name}", "See other matches", "Apply to Adopt"]
        }

