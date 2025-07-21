# src/simulation_engine.py

import os
import uuid
import logging
from typing import Dict
from dotenv import load_dotenv

# Load environment variables from .env if not already loaded
load_dotenv(override=True)

try:
    import openai
except ImportError:
    openai = None

logger = logging.getLogger("simulation_engine")
logger.setLevel(logging.INFO)

def suggest_simulation(user_id: str, context: dict) -> dict:
    """
    Suggests a poker simulation scenario for the user.
    If SIMULATION_ENGINE=llm, uses OpenAI to generate a dynamic scenario.
    Otherwise, returns a static placeholder.
    Always returns a dict with keys: simulation_id, scenario, stack_size, action (all as strings).
    """
    # Environment config
    sim_engine = os.getenv("SIMULATION_ENGINE", "llm").lower()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    dev_mode = os.getenv("FLASK_ENV", "").lower() == "development" or os.getenv("DEV_MODE", "0") == "1"

    # Extract context fields
    position = context.get("position", "middle position")
    hand = context.get("hand", "Ah Kh")
    stack_size_val = context.get("stack_size", 50)
    skill_level = context.get("skill_level", "beginner")

    # Always coerce stack_size to string with "bb" suffix
    def format_stack_size(val):
        try:
            if isinstance(val, str) and val.endswith("bb"):
                return val
            return f"{int(val)}bb"
        except Exception:
            return "50bb"

    # Fallback static simulation
    def static_simulation(fallback_reason=None):
        if fallback_reason:
            logger.warning(f"Falling back to static simulation: {fallback_reason}")
        logger.info("Simulation engine used: static")
        return {
            "simulation_id": "sim_placeholder",
            "scenario": "This is a test simulation output.",
            "stack_size": format_stack_size(stack_size_val),
            "action": "Call"
        }

    if sim_engine != "llm" or not openai or not openai_api_key:
        return static_simulation("LLM engine not enabled or OpenAI not available")

    logger.info("Simulation engine used: llm")

    # LLM-based simulation
    prompt = (
        f"You are a poker simulation engine. Generate a realistic poker scenario for a player with the following details:\n"
        f"- Position: {position}\n"
        f"- Hand: {hand}\n"
        f"- Stack size: {format_stack_size(stack_size_val)}\n"
        f"- Skill level: {skill_level}\n"
        f"Output a JSON object with keys: simulation_id, scenario, stack_size, action. "
        f"All values must be strings. stack_size should be like '50bb'. "
        f"Make the scenario unique and actionable. Example:\n"
        f'{{"simulation_id": "...", "scenario": "...", "stack_size": "50bb", "action": "Call"}}, '
        f'but do not repeat the example, generate a new one each time.'
    )

    if dev_mode:
        logger.info(f"[DEV] LLM Simulation Prompt: {prompt}")

    try:
        openai.api_key = openai_api_key
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a poker simulation engine."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=300,
        )
        content = response.choices[0].message.content.strip()
        import json
        # Try to parse the LLM output as JSON
        sim = json.loads(content)
        # Ensure required keys and types
        required_keys = ["simulation_id", "scenario", "stack_size", "action"]
        for k in required_keys:
            if k not in sim:
                logger.warning(f"LLM simulation missing key: {k}. Falling back to static.")
                return static_simulation(f"Missing key: {k}")
            if not isinstance(sim[k], str):
                sim[k] = str(sim[k])
        # Coerce stack_size to correct format
        sim["stack_size"] = format_stack_size(sim["stack_size"])
        return sim
    except Exception as e:
        logger.error(f"OpenAI simulation generation failed: {e}")
        return static_simulation(f"OpenAI error: {e}")
