# src/harmony_engine.py

from src.rag_engine import query_knowledge_base
from src.coaching_agent import generate_coaching_response
from src.simulation_engine import suggest_simulation
from src.goal_tracker import get_active_goals

class HarmonyEngine:
    @staticmethod
    def respond(user_id: str, message: str, context: dict) -> dict:
        intent = context.get("intent", "coaching")
        emotion = context.get("emotional_state", "neutral")
        category = context.get("category", "general")

        # Step 1: Retrieve relevant knowledge (RAG)
        rag_results = query_knowledge_base(message, category)

        # Step 2: Generate coaching response based on knowledge + emotion
        coaching_output = generate_coaching_response(message, rag_results, emotion)

        # Step 3: Optional simulation suggestion
        sim = suggest_simulation(message)

        # Step 4: Fetch active goals (if any)
        goals = get_active_goals(user_id)

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
