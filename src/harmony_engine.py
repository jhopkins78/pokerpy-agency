# src/harmony_engine.py

from Agentic_Rag.rag.knowledge_base import PokerKnowledgeBase
from src.models.coach import CoachAgent
from src.agents.base_agent import AgentMessage
import asyncio
from src.simulation_engine import suggest_simulation
from src.goal_tracker import get_active_goals
from datetime import datetime
import logging
import os

logger = logging.getLogger("PokerPy.RAG")

class HarmonyEngine:
    @staticmethod
    def respond(user_id: str, message: str, context: dict) -> dict:
        intent = context.get("intent", "coaching")
        emotion = context.get("emotional_state", "neutral")
        category = context.get("category", "general")

        # Step 1: Set up RAG system components
        kb = PokerKnowledgeBase()
        from Agentic_Rag.rag.vector_store import VectorStore, EmbeddingService
        from src.models.orchestrator import AgentOrchestrator
        from Agentic_Rag.rag.rag_orchestrator import RAGOrchestrator

        embedding_service = EmbeddingService(model_name="tfidf", cache_embeddings=True)
        vector_store = VectorStore(embedding_service=embedding_service)
        agent_orchestrator = AgentOrchestrator()
        rag_orchestrator = RAGOrchestrator(
            agent_orchestrator=agent_orchestrator,
            knowledge_base=kb,
            vector_store=vector_store
        )

        # Step 2: RAG retrieval (for logging and fallback)
        rag_results = kb.search_documents(query=message, tags=[category])
        source_count = len(rag_results) if rag_results else 0
        titles = [doc.get("title", "") for doc in rag_results] if rag_results else []
        logger.info(f"RAG: Retrieved {source_count} docs for user {user_id} | Titles: {titles}")

        # Step 3: Generate coaching response with RAG enhancement
        coach_agent = CoachAgent(rag_orchestrator=rag_orchestrator)
        agent_message = AgentMessage(
            id=f"msg_{datetime.now().timestamp()}",
            sender="harmony_engine",
            recipient="rag_coach",
            message_type="coaching_request",
            content={
                "query": message,
                "rag_results": rag_results,
                "emotion": emotion,
                "context": context
            },
            timestamp=datetime.now()
        )
        # Use asyncio to run the agent's process_message coroutine
        coaching_response = asyncio.run(coach_agent.process_message(agent_message))
        coaching_output = coaching_response.content.get("response") if coaching_response else "Error: No response from coach agent."
        sources = coaching_response.content.get("sources", []) if coaching_response else []

        # Step 4: Optional simulation suggestion (dynamic)
        sim = suggest_simulation(user_id, context)
        used_simulation = bool(sim)

        # Step 5: Fetch active goals (dynamic)
        goals = get_active_goals(user_id)
        if goals and isinstance(goals[0], dict) and "goal" in goals[0]:
            goals = [g["goal"] for g in goals]

        # Step 6: Return harmonized reply
        result = {
            "response": coaching_output,
            "sources": sources,
            "suggested_simulation": sim,
            "active_goals": goals,
            "context_used": {
                "intent": intent,
                "emotion": emotion,
                "category": category
            }
        }

        # Add rag_debug in development mode
        if os.environ.get("FLASK_DEBUG", "False").lower() == "true":
            result["rag_debug"] = {
                "source_count": len(sources),
                "used_simulation": used_simulation
            }

        return result
