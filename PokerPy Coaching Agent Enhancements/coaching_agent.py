import openai
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass

import sys
import os
import importlib.util

# Dynamically import simulation_engine from src/simulation_engine.py
sim_engine_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'simulation_engine.py'))
spec = importlib.util.spec_from_file_location("simulation_engine", sim_engine_path)
sim_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim_engine)
suggest_simulation = sim_engine.suggest_simulation

logger = logging.getLogger(__name__)

@dataclass
class CoachingResponse:
    message: str
    context: Dict
    suggestions: List[str]
    emotional_tone: str
    follow_up_questions: List[str]

import re

def parse_poker_context(message: str) -> dict:
    """
    Extract structured poker context from a user message.
    Returns a dict with keys: hand, position, table_size, villain_style, stack_size, flop_concern.
    Uses regex and keyword scanning.
    """
    context = {}

    # Hand (e.g., AKs, QJo, pocket aces, etc.)
    hand_match = re.search(r"\b([2-9TJQKA]{2}[so]?|pocket\s+[2-9TJQKA]{1,2}s?)\b", message, re.IGNORECASE)
    if hand_match:
        context["hand"] = hand_match.group(1).upper().replace("POCKET ", "")

    # Position (UTG, MP, CO, BTN, SB, BB, etc.)
    positions = ["UTG", "MP", "CO", "BTN", "SB", "BB", "early position", "middle position", "cutoff", "button", "small blind", "big blind"]
    for pos in positions:
        if re.search(rf"\b{pos}\b", message, re.IGNORECASE):
            context["position"] = pos.upper() if len(pos) <= 3 else pos.title()
            break

    # Table size (6-max, 9-handed, 8 players, etc.)
    table_match = re.search(r"(\d+)[-\s]?(max|handed|players|player table)", message, re.IGNORECASE)
    if table_match:
        context["table_size"] = int(table_match.group(1))
    else:
        # fallback: look for "full ring"
        if "full ring" in message.lower():
            context["table_size"] = 9

    # Villain style (aggressive, loose, tight, 3-bettor, etc.)
    villain_styles = ["aggressive", "loose", "tight", "passive", "3-bettor", "maniac", "nit", "calling station"]
    found_styles = []
    for style in villain_styles:
        if style in message.lower():
            found_styles.append(style)
    if found_styles:
        context["villain_style"] = ", ".join(found_styles)

    # Stack size (e.g., 100bb, 50bb, 200bb, short stack, deep stack)
    stack_match = re.search(r"(\d+)\s*bb", message, re.IGNORECASE)
    if stack_match:
        context["stack_size"] = f"{stack_match.group(1)}bb"
    else:
        for stack_word in ["short stack", "deep stack"]:
            if stack_word in message.lower():
                context["stack_size"] = stack_word

    # Flop concern (missing flop, out of position, etc.)
    flop_keywords = ["missed the flop", "missing flop", "out of position", "draw heavy", "wet board", "dry board", "scary board"]
    found_flop = []
    for kw in flop_keywords:
        if kw in message.lower():
            found_flop.append(kw)
    if found_flop:
        context["flop_concern"] = ", ".join(found_flop)

    return context

class PokerCoachingAgent:
    def __init__(self, rag_system, memory_manager):
        self.rag_system = rag_system
        self.memory_manager = memory_manager
        self.client = openai.OpenAI()
        
        # Coaching personas and styles
        self.coaching_styles = {
            "supportive": "Encouraging, empathetic, focuses on building confidence",
            "analytical": "Data-driven, logical, focuses on technical improvement",
            "motivational": "High-energy, inspiring, focuses on mindset and goals",
            "philosophical": "Deep, reflective, connects poker to life lessons",
            "practical": "Direct, actionable, focuses on immediate improvements"
        }
        
        # Question categories for psychological profiling
        self.profiling_questions = {
            "risk_tolerance": [
                "How do you typically handle uncertainty in your daily life?",
                "When facing a difficult decision, do you prefer to act quickly or take time to analyze?",
                "Tell me about a time you took a calculated risk. How did it feel?"
            ],
            "emotional_regulation": [
                "How do you usually respond when things don't go as planned?",
                "What helps you stay calm under pressure?",
                "How do you handle criticism or feedback?"
            ],
            "learning_style": [
                "Do you prefer learning through practice or studying theory first?",
                "How do you best remember new information?",
                "What motivates you to improve at something new?"
            ],
            "goals_motivation": [
                "What does success mean to you in poker and in life?",
                "What drives you to keep improving?",
                "How do you celebrate your achievements?"
            ]
        }
        
    def generate_response(self, user_id: str, message: str, context: Dict, user_profile: Optional[Dict] = None) -> Dict:
        """Generate a coaching response based on user input and context, with simulation if poker context is detected"""
        try:
            # Get user profile and conversation history
            if not user_profile:
                user_profile = self.memory_manager.get_user_profile(user_id)
            
            conversation_history = self.memory_manager.get_recent_conversations(user_id, limit=5)
            
            # --- NEW: Parse poker context from message ---
            parsed_context = parse_poker_context(message)
            # Merge with any provided context (context param may have session info)
            merged_context = {**context, **parsed_context} if context else parsed_context

            # --- RAG retrieval using parsed context as query ---
            context_query = " ".join(str(v) for v in parsed_context.values() if v)
            rag_docs = []
            try:
                if context_query:
                    rag_results = self.rag_system.search(context_query, category="all", limit=2)
                else:
                    rag_results = []
                if rag_results and isinstance(rag_results, list):
                    for doc in rag_results:
                        if isinstance(doc, dict):
                            # Prefer summary, then key_points, then content
                            doc_text = doc.get("summary") or doc.get("key_points") or doc.get("content") or ""
                        else:
                            doc_text = str(doc)
                        if doc_text:
                            rag_docs.append(doc_text)
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")
                rag_docs = []

            # --- If poker context detected, run simulation with RAG docs ---
            simulation_result = None
            if any(k in parsed_context for k in ["hand", "position", "stack_size"]):
                simulation_result = suggest_simulation(user_id, parsed_context, rag_docs=rag_docs)

            # Determine coaching style based on user profile and context
            coaching_style = self._determine_coaching_style(user_profile, merged_context)
            
            # Use RAG docs as knowledge_context for system prompt (or empty list)
            knowledge_context = rag_docs if rag_docs else []

            # Build system prompt
            system_prompt = self._build_system_prompt(coaching_style, user_profile, knowledge_context)
            
            # Build conversation context
            conversation_context = self._build_conversation_context(conversation_history, message, merged_context)
            
            # Generate response using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": conversation_context}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content

            # --- NEW: Integrate simulation result into response ---
            if simulation_result:
                sim_text = (
                    f"\n---\nPoker Simulation:\n"
                    f"Scenario: {simulation_result.get('scenario')}\n"
                    f"Recommended Action: {simulation_result.get('action')}\n"
                    f"Strategic Guidance: {simulation_result.get('guidance')}\n"
                    f"Stack Size: {simulation_result.get('stack_size')}\n"
                )
                response_text = sim_text + "\n" + response_text
            
            # Parse response and extract components
            parsed_response = self._parse_response(response_text)
            
            # Update user profile based on interaction
            self._update_user_insights(user_id, message, parsed_response, user_profile)
            
            response_dict = {
                "message": parsed_response.message,
                "context": parsed_response.context,
                "suggestions": parsed_response.suggestions,
                "emotional_tone": parsed_response.emotional_tone,
                "follow_up_questions": parsed_response.follow_up_questions
            }
            # Add rag_debug if present in simulation_result
            if simulation_result and "rag_debug" in simulation_result:
                response_dict["rag_debug"] = simulation_result["rag_debug"]
            return response_dict
            
        except Exception as e:
            logger.error(f"Error generating coaching response: {str(e)}")
            return {
                "message": "I'm here to help you improve your poker game and mindset. What would you like to work on today?",
                "context": {},
                "suggestions": ["Tell me about your recent poker sessions", "What specific skills do you want to improve?"],
                "emotional_tone": "supportive",
                "follow_up_questions": []
            }
    
    def _determine_coaching_style(self, user_profile: Dict, context: Dict) -> str:
        """Determine the best coaching style for this interaction"""
        if not user_profile:
            return "supportive"
        
        # Analyze user's emotional state and preferences
        psychological_profile = user_profile.get('psychological_profile', {})
        recent_performance = context.get('recent_performance', 'neutral')
        
        if recent_performance == 'poor' or context.get('emotional_state') == 'frustrated':
            return "supportive"
        elif psychological_profile.get('learning_style') == 'analytical':
            return "analytical"
        elif context.get('topic') in ['motivation', 'goals', 'mindset']:
            return "motivational"
        elif psychological_profile.get('depth_preference') == 'philosophical':
            return "philosophical"
        else:
            return "practical"
    
    def _build_system_prompt(self, coaching_style: str, user_profile: Dict, knowledge_context: List) -> str:
        """Build the system prompt for the coaching agent"""
        base_prompt = f"""You are an expert poker coach and mentor with deep psychological insight. Your coaching style is {coaching_style}: {self.coaching_styles[coaching_style]}.

Your role is to:
1. Provide personalized poker strategy and mental game coaching
2. Help users develop both poker skills and life skills through poker metaphors
3. Build psychological profiles through natural conversation
4. Track and support user goals (poker and personal)
5. Offer encouragement and maintain user confidence
6. Connect poker concepts to broader life lessons

User Profile Summary:
{json.dumps(user_profile, indent=2) if user_profile else "New user - build rapport and gather insights"}

Relevant Knowledge Context:
{json.dumps(knowledge_context, indent=2) if knowledge_context else "No specific knowledge retrieved"}

Guidelines:
- Ask thoughtful, open-ended questions to understand the user better
- Use metaphors and analogies to explain complex concepts
- Be encouraging and supportive while providing honest feedback
- Connect poker strategy to personal development
- Adapt your communication style to the user's preferences
- Remember details about the user for future conversations

Response Format:
Provide your response as natural conversation, but include:
- Main coaching message
- 2-3 actionable suggestions
- 1-2 follow-up questions to deepen understanding
- Emotional tone indicator (supportive/analytical/motivational/philosophical/practical)"""

        return base_prompt
    
    def _build_conversation_context(self, conversation_history: List, current_message: str, context: Dict) -> str:
        """Build the conversation context for the current interaction"""
        context_parts = []
        
        if conversation_history:
            context_parts.append("Recent conversation history:")
            for conv in conversation_history[-3:]:  # Last 3 exchanges
                context_parts.append(f"User: {conv.get('message', '')}")
                context_parts.append(f"Coach: {conv.get('response', '')}")
        
        if context:
            context_parts.append(f"Current context: {json.dumps(context)}")
        
        context_parts.append(f"Current user message: {current_message}")
        
        return "\n".join(context_parts)
    
    def _parse_response(self, response_text: str) -> CoachingResponse:
        """Parse the AI response into structured components"""
        # Simple parsing - in production, you might use more sophisticated NLP
        lines = response_text.split('\n')
        
        message = response_text
        suggestions = []
        follow_up_questions = []
        emotional_tone = "supportive"
        
        # Extract suggestions and questions if formatted properly
        for line in lines:
            if line.strip().startswith('Suggestion:') or line.strip().startswith('-'):
                suggestions.append(line.strip().replace('Suggestion:', '').replace('-', '').strip())
            elif line.strip().endswith('?'):
                follow_up_questions.append(line.strip())
        
        return CoachingResponse(
            message=message,
            context={},
            suggestions=suggestions[:3],  # Limit to 3 suggestions
            emotional_tone=emotional_tone,
            follow_up_questions=follow_up_questions[:2]  # Limit to 2 questions
        )
    
    def _update_user_insights(self, user_id: str, message: str, response: CoachingResponse, user_profile: Dict):
        """Update user psychological profile based on interaction"""
        try:
            # Analyze user message for psychological insights
            insights = self._extract_psychological_insights(message)
            
            # Update user profile
            if insights:
                self.memory_manager.update_psychological_profile(user_id, insights)
                
        except Exception as e:
            logger.error(f"Error updating user insights: {str(e)}")
    
    def _extract_psychological_insights(self, message: str) -> Dict:
        """Extract psychological insights from user message"""
        insights = {}
        
        # Simple keyword-based analysis (in production, use more sophisticated NLP)
        message_lower = message.lower()
        
        # Risk tolerance indicators
        if any(word in message_lower for word in ['scared', 'afraid', 'nervous', 'worried']):
            insights['risk_tolerance'] = 'low'
        elif any(word in message_lower for word in ['aggressive', 'bold', 'confident', 'fearless']):
            insights['risk_tolerance'] = 'high'
        
        # Emotional regulation indicators
        if any(word in message_lower for word in ['tilt', 'angry', 'frustrated', 'upset']):
            insights['emotional_regulation'] = 'needs_work'
        elif any(word in message_lower for word in ['calm', 'composed', 'focused', 'zen']):
            insights['emotional_regulation'] = 'strong'
        
        # Learning style indicators
        if any(word in message_lower for word in ['theory', 'study', 'analyze', 'calculate']):
            insights['learning_style'] = 'analytical'
        elif any(word in message_lower for word in ['practice', 'play', 'experience', 'feel']):
            insights['learning_style'] = 'experiential'
        
        return insights
    
    def generate_daily_insight(self, user_id: str) -> Dict:
        """Generate a daily motivational insight"""
        try:
            user_profile = self.memory_manager.get_user_profile(user_id)
            
            # Get a random insight template
            insight_templates = [
                "Today's poker wisdom: {wisdom}. How can you apply this to your game today?",
                "Mental game focus: {focus}. Remember, poker is as much about psychology as it is about cards.",
                "Daily challenge: {challenge}. Small improvements compound over time.",
                "Mindset reminder: {mindset}. Your attitude determines your altitude at the tables.",
                "Strategic thought: {strategy}. Every decision is an opportunity to improve."
            ]
            
            template = random.choice(insight_templates)
            
            # Generate personalized content based on user profile
            prompt = f"""Generate a brief, inspiring poker insight for a user with this profile:
            {json.dumps(user_profile, indent=2) if user_profile else "General user"}
            
            Focus on: mental game, strategy, personal development, or motivation.
            Keep it under 100 words and actionable."""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=150
            )
            
            insight_content = response.choices[0].message.content
            
            return {
                "insight": insight_content,
                "date": datetime.now().isoformat(),
                "category": "daily_wisdom"
            }
            
        except Exception as e:
            logger.error(f"Error generating daily insight: {str(e)}")
            return {
                "insight": "Every hand is a new opportunity to make the best decision with the information you have. Focus on the process, not the outcome.",
                "date": datetime.now().isoformat(),
                "category": "daily_wisdom"
            }
    
    def ask_anything_mode(self, user_id: str, question: str, category: str = "general") -> Dict:
        """Handle 'ask anything' mode for life advice beyond poker"""
        try:
            user_profile = self.memory_manager.get_user_profile(user_id)
            
            system_prompt = f"""You are a wise mentor who uses poker principles to provide life advice. 
            The user is asking about: {category}
            
            User profile: {json.dumps(user_profile, indent=2) if user_profile else "General user"}
            
            Guidelines:
            - Connect your advice to poker principles when relevant
            - Be supportive and encouraging
            - Provide practical, actionable advice
            - Draw from psychology, philosophy, and personal development
            - Keep responses conversational and warm
            
            Categories you can help with:
            - Mental health and emotional well-being
            - Goal setting and achievement
            - Relationships and communication
            - Career and personal development
            - Spirituality and meaning
            - Habits and discipline
            - Learning and growth"""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            return {
                "response": response.choices[0].message.content,
                "category": category,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in ask anything mode: {str(e)}")
            return {
                "response": "I'm here to help you with any questions about life, growth, and personal development. What's on your mind?",
                "category": category,
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_profiling_question(self, user_id: str, category: str = None) -> str:
        """Generate a natural profiling question to learn more about the user"""
        if not category:
            category = random.choice(list(self.profiling_questions.keys()))
        
        questions = self.profiling_questions.get(category, self.profiling_questions['goals_motivation'])
        return random.choice(questions)
