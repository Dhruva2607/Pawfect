"""
LangGraph State Machine definition with MongoDBSaver checkpointer persistence.
[FROM MARKDOWN] matches Step 2.1, Step 2.2, Step 2.3, Step 2.4, and Step 3.3.
"""

import logging
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.mongodb import MongoDBSaver

from app.database.connection import get_sync_client
from app.services.state import MatchmakerState
from app.services.nodes import (
    conversational_intake_node,
    hybrid_retrieval_node,
    reasoning_scoring_node,
)

logger = logging.getLogger(__name__)


def should_continue_to_retrieval(state: MatchmakerState) -> str:
    """
    Conditional edge router:
    If critical lifestyle dimensions are gathered (is_complete == True), proceeds to hybrid retrieval.
    Otherwise, halts and awaits user's response to the follow-up question.
    """
    if state.get("is_complete") is True:
        return "hybrid_retrieval"
    return END


_checkpointer: Optional[Any] = None


def get_checkpointer() -> Any:
    """
    Returns the persistent checkpointer.
    Uses MongoDBSaver [FROM MARKDOWN: Step 3.3] for cross-session persistence in MongoDB Atlas,
    falling back to in-memory MemorySaver if MongoDB client is not reachable.
    """
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    try:
        client = get_sync_client()
        _checkpointer = MongoDBSaver(client)
        logger.info("Initialized MongoDBSaver checkpointer for session persistence.")
        return _checkpointer
    except Exception as e:
        logger.warning("Could not initialize MongoDBSaver (%s). Falling back to MemorySaver.", e)
        _checkpointer = MemorySaver()
        return _checkpointer


_compiled_graph: Optional[Any] = None


def build_matchmaker_graph(checkpointer: Optional[Any] = None) -> Any:
    """
    Builds and compiles the AI Pet Matchmaker LangGraph StateGraph.
    Flow:
      START
        ↓
      conversational_intake
        ↓ (conditional)
        ├── is_complete == False ──→ END (prompt follow-up question)
        └── is_complete == True
              ↓
            hybrid_retrieval (MQL Pre-filters + Vector Search)
              ↓
            reasoning_scoring (Gemini Compatibility Analysis: 0-100%, pros, caveats)
              ↓
            END
    """
    workflow = StateGraph(MatchmakerState)

    # Register nodes
    workflow.add_node("conversational_intake", conversational_intake_node)
    workflow.add_node("hybrid_retrieval", hybrid_retrieval_node)
    workflow.add_node("reasoning_scoring", reasoning_scoring_node)

    # Set entry point
    workflow.set_entry_point("conversational_intake")

    # Add edges
    workflow.add_conditional_edges(
        "conversational_intake",
        should_continue_to_retrieval,
        {
            "hybrid_retrieval": "hybrid_retrieval",
            END: END
        }
    )
    workflow.add_edge("hybrid_retrieval", "reasoning_scoring")
    workflow.add_edge("reasoning_scoring", END)

    cp = checkpointer if checkpointer is not None else get_checkpointer()
    compiled_app = workflow.compile(checkpointer=cp)
    logger.info("Compiled AI Pet Matchmaker LangGraph StateGraph with checkpointer successfully.")
    return compiled_app


def get_matchmaker_graph() -> Any:
    """Returns singleton instance of the compiled LangGraph matchmaker."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_matchmaker_graph()
    return _compiled_graph


def run_matchmaker_turn(
    session_id: str,
    user_message: str,
    conversation_history: Optional[list] = None,
    prior_constraints: Optional[dict] = None
) -> Dict[str, Any]:
    """
    Executes a single conversational turn through the LangGraph State Machine.
    Persists checkpoints seamlessly via MongoDBSaver [FROM MARKDOWN: Step 3.3].
    """
    graph = get_matchmaker_graph()

    initial_state: MatchmakerState = {
        "session_id": session_id,
        "user_message": user_message,
        "conversation_history": conversation_history or [],
        "extracted_constraints": prior_constraints or {},
        "candidate_matches": [],
        "evaluations": [],
        "is_complete": False,
        "response_message": "",
        "quick_replies": [],
    }

    config = {"configurable": {"thread_id": session_id}}
    result_state = graph.invoke(initial_state, config=config)
    return result_state
