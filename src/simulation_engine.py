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

def suggest_simulation(user_id: str, context: dict) -> dict:
    engine_mode = os.getenv("SIMULATION_ENGINE", "STATIC")
    logging.debug(f"SIMULATION_ENGINE={engine_mode}")
    logging.debug(f"Context received: {context}")

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logging.error("OPENAI_API_KEY not found in environment.")
        return {
            "scenario": "This is a test simulation output.",
            "stack_size": "50bb",
            "action": "Call"
        }

    if engine_mode.lower() == "llm":
        try:
            openai.api_key = openai_key

            prompt = f"Simulate a poker scenario. Context: {context}"
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

            return {
                "scenario": scenario_text,
                "stack_size": context.get("player_stack", "75bb"),
                "action": "Call"
            }

        except Exception as e:
            logging.exception("LLM generation failed with an unhandled exception.")
            print("[LLM ERROR]", e)

    # Fallback
    fallback = {
        "scenario": "This is a test simulation output.",
        "stack_size": "50bb",
        "action": "Call"
    }
    logging.debug(f"Fallback simulation used: {fallback}")
    return fallback
