"""
Coach Agent for PokerPy
Provides conversational AI coaching and translates technical analysis into plain English
"""

import json
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentMessage, AgentCapability

class CoachAgent(BaseAgent):
    """
    Conversational AI coach that provides personalized poker coaching
    Translates technical analysis into beginner-friendly explanations
    """
    
    def __init__(self):
        super().__init__(
            agent_id="coach",
            name="AI Poker Coach",
            description="Provides conversational AI coaching and plain English explanations"
        )
        
        # Coaching personality and style
        self.coaching_style = "encouraging"  # encouraging, direct, analytical
        self.user_skill_levels = {}  # user_id -> skill_level
        self.conversation_history = {}  # user_id -> conversation_history
        
        # Response templates for different scenarios
        self.response_templates = {
            "hand_analysis": {
                "beginner": [
                    "Let me break this down in simple terms...",
                    "Here's what happened in your hand...",
                    "Don't worry, this is a common spot. Here's how to think about it..."
                ],
                "intermediate": [
                    "Looking at this hand, there are a few key concepts to consider...",
                    "This is a great learning opportunity. Let's analyze...",
                    "You're on the right track, but here's how to improve..."
                ],
                "advanced": [
                    "This hand presents some interesting strategic considerations...",
                    "Let's dive into the theory behind this decision...",
                    "From a GTO perspective, while considering exploitative adjustments..."
                ]
            },
            "encouragement": [
                "You're making great progress!",
                "That's exactly the right way to think about it!",
                "I can see your game improving already!",
                "Don't get discouraged - even pros make these mistakes!",
                "You're asking all the right questions!"
            ],
            "mistake_explanation": [
                "No worries - this is actually a really common mistake.",
                "I see why you made that play, but here's a better approach...",
                "This is a great learning moment. Here's what to do instead...",
                "Don't beat yourself up about this - let's turn it into a lesson!"
            ]
        }
        
        # Common poker concepts in plain English
        self.plain_english_concepts = {
            "equity": "your chances of winning the hand",
            "pot_odds": "the price you're getting to call",
            "implied_odds": "potential future winnings if you hit your hand",
            "reverse_implied_odds": "potential future losses if you make a weak hand",
            "position": "where you sit relative to the dealer button",
            "range": "all the possible hands someone could have",
            "polarized": "having either very strong or very weak hands",
            "merged": "having a mix of strong and medium-strength hands",
            "c_bet": "betting after you raised before the flop",
            "float": "calling with a weak hand planning to bluff later",
            "barrel": "betting again on the next street",
            "value_bet": "betting because you think you have the best hand",
            "bluff": "betting with a weak hand to make opponents fold better hands"
        }
    
    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="explain_analysis",
                description="Convert technical poker analysis into plain English explanations",
                input_schema={
                    "type": "object",
                    "properties": {
                        "technical_analysis": {"type": "object"},
                        "user_id": {"type": "string"},
                        "skill_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                        "explanation_style": {"type": "string", "enum": ["simple", "detailed", "conversational"]}
                    },
                    "required": ["technical_analysis", "user_id"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "plain_english_explanation": {"type": "string"},