# src/harmony_engine.py

from Agentic_Rag.rag.knowledge_base import PokerKnowledgeBase
from Agentic_Rag.coach_rag_enhanced import RAGEnhancedCoachAgent
from src.agents.base_agent import AgentMessage
import asyncio
from src.simulation_engine import suggest_simulation
from src.goal_tracker import get_active_goals
from datetime import datetime

class HarmonyEngine:
    @staticmethod
    def respond(user_id: str, message: str, context: dict) -> dict:
        intent = context.get("intent", "coaching")
        emotion = context.get("emotional_state", "neutral")
        category = context.get("category", "general")

        # Step 1: Retrieve relevant knowledge (RAG)
        kb = PokerKnowledgeBase()
        rag_results = kb.search_documents(query=message, tags=[category])

        # Step 2: Generate coaching response based on knowledge + emotion
        coach_agent = RAGEnhancedCoachAgent()
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
        coaching_response = asyncio.run(coach_agent.process_message(agent_message))
        coaching_output = coaching_response.content.get("response") if coaching_response else "Error: No response from coach agent."

        # Step 3: Optional simulation suggestion
        sim = suggest_simulation(user_id, context)

        # Step 4: Fetch active goals (if any)
        goals = get_active_goals(user_id)
        # Convert list of goal objects to list of strings if needed
        if goals and isinstance(goals[0], dict) and "goal" in goals[0]:
            goals = [g["goal"] for g in goals]

        # Step 5: Return harmonized reply
        return {
            "response": coaching_output,
            "sources": rag_results,
            "suggested_simulation": sim,
            "active_goals": goals,
            "context_used": {
                "intent": intent,
                "emotion": emotion,
                "category": category
            }
        }
