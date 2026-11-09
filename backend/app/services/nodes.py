"""
LangGraph Nodes: Conversational Intake, Hybrid Retrieval, and Reasoning & Scoring.
[FROM MARKDOWN] matches Step 2.2, Step 2.3, Step 2.4, Step 6.1, and Step 6.2.
"""

import json
import logging
from typing import Dict, Any, List
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
    follow_up_question: str = Field(
        ...,
        description="Warm, conversational follow-up question asking about missing dimensions, or empty string if ready"
    )
    suggested_quick_replies: List[str] = Field(
        default_factory=list,
        description="2-4 concise suggested quick-reply chips for mobile UI"
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


class MultiPetScoringOutput(BaseModel):
    """Structured collection of evaluations for top candidates."""
    evaluations: List[SinglePetCompatibility]
    overall_response: str = Field(
        ...,
        description="Warm, empathetic message introducing the top pet match and highlights"
    )


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
        "CRITICAL DIMENSIONS NEEDED BEFORE MATCHING:\n"
        "1. Desired Species: Dog, Cat, or either?\n"
        "2. Living Environment: Apartment, house with private yard, house without yard?\n"
        "3. Household Composition: Any young children or elderly residents?\n"
        "4. Resident Pets: Are there currently other dogs or cats in the home?\n"
        "5. Activity & Energy Budget: Daily walking/exercise routine, or preferred couch snuggle vibe?\n"
        "6. Allergies / Sensitivities: Any need for low-shedding or hypoallergenic pets?\n\n"
        "INSTRUCTIONS:\n"
        "- Merge all previously extracted constraints with any newly shared facts in the conversation.\n"
        "- Determine if we have at least 3-4 core dimensions (specifically species, housing, and energy/family).\n"
        "- If NOT sufficient yet, ask ONE natural, warm, conversational question covering the most important missing details.\n"
        "- Provide 2-4 short quick-reply options (e.g. ['Dog', 'Cat', 'Either is fine'] or ['Apartment', 'House with yard']).\n"
        "- If SUFFICIENT, set is_sufficient_for_search=True and synthesize a comprehensive semantic search_query summarizing their lifestyle."
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

        updated_constraints = analysis.extracted_constraints.model_dump(exclude_none=True)
        # Merge with prior
        merged_constraints = {**prior_constraints, **updated_constraints}

        if analysis.is_sufficient_for_search:
            search_query = analysis.search_query or (
                f"{merged_constraints.get('species', 'pet')} suitable for "
                f"{merged_constraints.get('housing_type', 'home')} with "
                f"energy level {merged_constraints.get('energy_budget', 3)}/5"
            )
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
        # Graceful heuristic fallback
        return {
            "extracted_constraints": prior_constraints,
            "is_complete": False,
            "response_message": "Tell me a little about your living space (apartment or house with a yard) and how much time you spend on daily walks!",
            "quick_replies": ["Apartment, moderate walks", "House with yard, very active", "Apartment, calm cuddles"],
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
        top_k=4
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
    candidates = state.get("candidate_matches", [])

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
        "1. Use ONLY the pet profile data provided in the candidate dossier. Do NOT invent medical conditions, behavioral traits, or training.\n"
        "2. Compatibility Score must be between 0 and 100%:\n"
        "   - 85-99%: High alignment across housing, energy, kids, and pets.\n"
        "   - 70-84%: Good alignment with minor lifestyle adjustments needed.\n"
        "   - Below 70%: Noticeable mismatch on energy, space, or household safety.\n"
        "3. Pros: Provide 2-3 specific, exact statements (e.g., 'Your activity level matches his energy', 'Family setup is ideal for his gentle nature').\n"
        "4. Caveats: Provide 1-2 realistic watch-outs based directly on pet's exercise needs or known triggers.\n"
        "5. Overall response: Warm, encouraging message presenting the #1 top match to the adopter."
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

        return {
            "evaluations": fallback_evals,
            "response_message": f"I found wonderful companion matches for your lifestyle! Meet {top_name}, your top candidate.",
            "quick_replies": [f"View {top_name}", "See other matches", "Apply to Adopt"]
        }

