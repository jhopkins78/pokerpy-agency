# src/simulation_engine.py

import os
import uuid
import logging
from typing import Dict
from dotenv import load_dotenv
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/simulation_engine.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Load environment variables from .env if not already loaded
load_dotenv(override=True)

logger = logging.getLogger("simulation_engine")
logger.setLevel(logging.INFO)

import json

def build_prompt(context: dict) -> str:
    """
    Builds a prompt for the LLM based on the provided context.
    """
    return (
        "Given the following context, suggest a poker simulation scenario for a poker training tool. "
        "Return a scenario description, a recommended stack size (e.g., '50bb'), and a recommended action (e.g., 'Call', 'Fold', 'Raise').\n"
        f"Context:\n{json.dumps(context, indent=2)}"
    )

def suggest_simulation(user_id: str, context: dict, rag_docs: list = None) -> dict:
    """
    Suggest a poker simulation and provide strategic guidance based on structured context.
    Injects RAG docs into the prompt if provided.
    """
    engine_mode = os.getenv("SIMULATION_ENGINE", "STATIC")
    logging.debug(f"SIMULATION_ENGINE={engine_mode}")
    logging.debug(f"Context received: {context}")

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logging.error("OPENAI_API_KEY not found in environment.")
        return {
            "scenario": "This is a test simulation output.",
            "stack_size": "50bb",
            "action": "Call",
            "guidance": "No LLM available. This is a static fallback.",
            "rag_debug": []
        }

    def context_to_fields(ctx: dict) -> str:
        # Compose a fielded description of the hero's situation
        fields = []
        if ctx.get("position"):
            fields.append(f"Position: {ctx['position']}")
        if ctx.get("hand"):
            fields.append(f"Hand: {ctx['hand']}")
        if ctx.get("villain_style"):
            fields.append(f"Villains: {ctx['villain_style']}")
        if ctx.get("stack_size"):
            fields.append(f"Stack Size: {ctx['stack_size']}")
        if ctx.get("flop_concern"):
            fields.append(f"Concern: {ctx['flop_concern']}")
        return "\n".join(fields)

    if engine_mode.lower() == "llm":
        try:
            openai.api_key = openai_key

            situation = context_to_fields(context)
            prompt = (
                "You are Coach Charlie, an elite poker coach. A player has asked for help on a specific hand. Below is their situation:\n\n"
                f"{situation}\n"
            )

            # Inject RAG docs in required format
            rag_debug = []
            if rag_docs and len(rag_docs) > 0:
                prompt += "\nUse the following poker knowledge base to guide your answer:\n\n[START KNOWLEDGE BASE]\n"
                for doc in rag_docs:
                    prompt += doc.strip() + "\n\n"
                    rag_debug.append(doc.strip())
                prompt += "[END KNOWLEDGE BASE]\n"
            else:
                logging.warning("No RAG docs found for simulation prompt.")

            prompt += (
                "Please provide a personalized coaching response that includes both strategic logic and practical guidance. "
                "Do not make up fictional characters or irrelevant details.\n"
                "Respond in this format:\nScenario: <description>\nRecommended Action: <action>\nStrategic Guidance: <guidance>"
            )

            logging.debug(f"LLM prompt: {prompt}")
            print("[DEBUG] Reached OpenAI call")
            logging.debug("Reached OpenAI call")

            from openai import OpenAI
            client = OpenAI()

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )

            scenario_text = response.choices[0].message.content
            logging.debug(f"LLM raw output: {scenario_text}")
            print("[LLM raw output]", scenario_text)

            # Parse the response for scenario, action, and guidance
            scenario, action, guidance = "", "", ""
            for line in scenario_text.splitlines():
                if line.lower().startswith("scenario:"):
                    scenario = line.split(":", 1)[1].strip()
                elif line.lower().startswith("recommended action:"):
                    action = line.split(":", 1)[1].strip()
                elif line.lower().startswith("strategic guidance:"):
                    guidance = line.split(":", 1)[1].strip()
            if not scenario:
                scenario = scenario_text

            return {
                "scenario": scenario,
                "stack_size": context.get("stack_size", "75bb"),
                "action": action if action else "Call",
                "guidance": guidance if guidance else scenario_text,
                "rag_debug": rag_debug
            }

        except Exception as e:
            logging.exception("LLM generation failed with an unhandled exception.")
            print("[LLM ERROR]", e)

    # Fallback
    fallback = {
        "scenario": "This is a test simulation output.",
        "stack_size": "50bb",
        "action": "Call",
        "guidance": "No LLM available. This is a static fallback.",
        "rag_debug": rag_docs if rag_docs else []
    }
    logging.debug(f"Fallback simulation used: {fallback}")
    return fallback
