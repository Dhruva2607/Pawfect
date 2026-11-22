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
from app.services.retrieval import hybrid_search_pets

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


# ── Node 1: Conversational Intake Node ───────────────────────────────

def conversational_intake_node(state: MatchmakerState) -> Dict[str, Any]:
    """
    Step 2.2: Conversational Intake Node.
    Ingests natural language dialogue, extracts lifestyle parameters, and evaluates
    whether critical dimensions (species, living space, activity, family) have been gathered.
    """
    user_msg = state.get("user_message", "")
    history = state.get("conversation_history", [])
    prior_constraints = state.get("extracted_constraints", {})

    logger.info("Executing Conversational Intake Node. User message: '%s'", user_msg)

    # Format dialogue history
    dialogue_snippets = []
    for turn in history[-6:]:  # Keep recent context
        dialogue_snippets.append(f"{turn.get('role', 'user').capitalize()}: {turn.get('content', '')}")
    if user_msg:
        dialogue_snippets.append(f"User: {user_msg}")
    dialogue_text = "\n".join(dialogue_snippets)

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
        "CRITICAL ONE-QUESTION-AT-A-TIME & MATCHING SUGGESTIONS RULE:\n"
        "- When requesting more information, ask EXACTLY ONE focused question at a time. NEVER combine multiple questions into one message.\n"
        "- Provide 2 to 4 concise suggested_quick_replies that DIRECTLY and FULLY answer that ONE question, so the adopter can simply tap an option instead of typing.\n"
        "- Example mappings for questions and their matching suggestions:\n"
        "  * Missing Species: follow_up_question='Are you looking to adopt a dog or a cat?' -> suggested_quick_replies=['Looking for a Dog', 'Looking for a Cat', 'Open to either']\n"
        "  * Missing Housing: follow_up_question='What kind of living space do you have?' -> suggested_quick_replies=['Apartment', 'House with yard', 'House without yard']\n"
        "  * Missing Activity/Energy: follow_up_question='What activity level fits your daily routine best?' -> suggested_quick_replies=['Calm & low energy', 'Moderate daily walks', 'High energy & active']\n"
        "  * Missing Household/Pets: follow_up_question='Do you have any children or other pets at home?' -> suggested_quick_replies=['No children or other pets', 'Have young children', 'Have other pets', 'Have children & pets']\n\n"
        "CRITICAL DIMENSIONS NEEDED BEFORE MATCHING:\n"
        "1. Desired Species: Dog, Cat, or either?\n"
        "2. Living Environment: Apartment, house with private yard, house without yard?\n"
        "3. Household Composition: Any young children or elderly residents?\n"
        "4. Resident Pets: Are there currently other dogs or cats in the home?\n"
        "5. Activity & Energy Budget: Daily walking/exercise routine, or preferred couch snuggle vibe?\n"
        "6. Allergies / Sensitivities: Any need for low-shedding or hypoallergenic pets?\n\n"
        "INSTRUCTIONS:\n"
        "- Merge all previously extracted constraints with any newly shared facts in the conversation.\n"
        "- The newest user message ALWAYS wins: if the user asks for a different species than before, update species to the newly requested one (only 'dog', 'cat', or 'any').\n"
        "- Determine if we have at least 3-4 core dimensions (specifically species, housing, and energy/family).\n"
        "- If NOT sufficient yet, ask EXACTLY ONE natural, conversational question covering the most important missing detail with matching quick replies.\n"
        "- If SUFFICIENT and RELEVANT, set is_sufficient_for_search=True and synthesize a comprehensive semantic search_query summarizing their lifestyle."
    )

    human_prompt = (
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

        updated_constraints = analysis.extracted_constraints.model_dump(exclude_none=True)
        # Merge with prior, then let an explicit species request in the newest message win
        merged_constraints = {**prior_constraints, **updated_constraints}
        merged_constraints = _apply_species_override(merged_constraints, user_msg)

        if analysis.is_sufficient_for_search:
            search_query = analysis.search_query or (
                f"{merged_constraints.get('species', 'pet')} suitable for "
                f"{merged_constraints.get('housing_type', 'home')} with "
                f"energy level {merged_constraints.get('energy_budget', 3)}/5"
            )
            species = merged_constraints.get("species")
            if species and species.lower() not in search_query.lower():
                search_query = f"{species} {search_query}"
            return {
                "extracted_constraints": merged_constraints,
                "is_complete": True,
                "search_queries": [search_query],
                "response_message": "Thank you! I have a wonderful picture of your lifestyle. Searching our shelters for your ideal companion...",
                "quick_replies": [],
                "next_node": "hybrid_retrieval"
            }
        else:
            return {
                "extracted_constraints": merged_constraints,
                "is_complete": False,
                "response_message": analysis.follow_up_question,
                "quick_replies": analysis.suggested_quick_replies,
                "next_node": "await_user"
            }

    except Exception as e:
        logger.error("Error in conversational intake node: %s. Using graceful heuristic fallback.", e)
        # Smart heuristic fallback: ask for the first missing dimension with matching suggestions
        if not prior_constraints.get("species"):
            fallback_q = "Are you looking to adopt a dog or a cat?"
            fallback_qr = ["Looking for a Dog", "Looking for a Cat", "Open to either"]
        elif not prior_constraints.get("housing_type"):
            fallback_q = "What kind of home do you have?"
            fallback_qr = ["Apartment", "House with yard", "House without yard"]
        elif not prior_constraints.get("energy_budget"):
            fallback_q = "What activity level fits your lifestyle best?"
            fallback_qr = ["Calm & low energy", "Moderate daily walks", "High energy & active"]
        else:
            fallback_q = "Do you have any children or other pets at home?"
            fallback_qr = ["No children or pets", "Have young children", "Have other pets", "Have children & pets"]

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
    """
    constraints = state.get("extracted_constraints", {})
    queries = state.get("search_queries", [])
    query_text = queries[0] if queries else "loving companion pet"

    logger.info("Executing Hybrid Retrieval Node for query: '%s'", query_text)

    candidates = hybrid_search_pets(
        query_text=query_text,
        constraints=constraints,
        top_k=3
    )

    return {
        "candidate_matches": candidates,
        "next_node": "reasoning_scoring"
    }


# ── Node 3: Reasoning & Scoring Node ─────────────────────────────────

def reasoning_scoring_node(state: MatchmakerState) -> Dict[str, Any]:
    """
    Step 2.4: Reasoning & Scoring Node.
    Evaluates candidate pets against adopter lifestyle.
    Enforces strict grounding (0.1 temp) [FROM MARKDOWN: Step 6.1] and structured Pydantic output.
    """
    constraints = state.get("extracted_constraints", {})
    candidates = state.get("candidate_matches", [])[:3]

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
            "energy_level": pet.get("energy_level"),
            "housing_requirement": pet.get("housing_requirement"),
            "good_with_kids": pet.get("good_with_kids"),
            "good_with_other_pets": pet.get("good_with_other_pets"),
            "temperament": pet.get("temperament"),
            "exercise_needs": pet.get("exercise_needs"),
            "quirks": pet.get("quirks"),
            "triggers": pet.get("triggers"),
            "bio_text": pet.get("bio_text")
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
        "7. Overall response: Warm, encouraging message presenting the #1 Hero Match to the adopter, and briefly summarizing the alternative matches explaining why each is not quite as perfect a fit compared to the hero pet."
    )

    human_prompt = (
        f"Adopter Lifestyle Constraints:\n{json.dumps(constraints, indent=2)}\n\n"
        f"Candidate Shelter Pets Dossier:\n{json.dumps(dossier_entries, indent=2)}\n\n"
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
            "quick_replies": [f"Learn more about {top_match_name}", "See alternative matches", "Start Adoption Application"]
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

