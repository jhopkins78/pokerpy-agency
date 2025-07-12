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
                        "key_takeaways": {"type": "array"},
                        "next_steps": {"type": "array"},
                        "follow_up_questions": {"type": "array"}
                    }
                }
            ),
            AgentCapability(
                name="answer_question",
                description="Answer poker-related questions in a conversational manner",
                input_schema={
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "user_id": {"type": "string"},
                        "context": {"type": "object"}
                    },
                    "required": ["question", "user_id"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "answer": {"type": "string"},
                        "examples": {"type": "array"},
                        "related_concepts": {"type": "array"}
                    }
                }
            ),
            AgentCapability(
                name="provide_encouragement",
                description="Provide motivational coaching and encouragement",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "situation": {"type": "string"},
                        "progress_data": {"type": "object"}
                    },
                    "required": ["user_id", "situation"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "encouragement_message": {"type": "string"},
                        "progress_highlights": {"type": "array"},
                        "motivation": {"type": "string"}
                    }
                }
            ),
            AgentCapability(
                name="create_learning_plan",
                description="Create personalized learning plans based on identified weaknesses",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "identified_leaks": {"type": "array"},
                        "skill_level": {"type": "string"},
                        "time_commitment": {"type": "string"}
                    },
                    "required": ["user_id", "identified_leaks"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "learning_plan": {"type": "object"},
                        "weekly_goals": {"type": "array"},
                        "practice_exercises": {"type": "array"}
                    }
                }
            )
        ]
    
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process coaching requests and provide personalized responses"""
        try:
            message_type = message.message_type
            content = message.content
            
            if message_type == "explain_analysis":
                result = await self._explain_analysis(content)
            elif message_type == "answer_question":
                result = await self._answer_question(content)
            elif message_type == "provide_encouragement":
                result = await self._provide_encouragement(content)
            elif message_type == "create_learning_plan":
                result = await self._create_learning_plan(content)
            else:
                result = {"error": f"Unknown message type: {message_type}"}
            
            return AgentMessage(
                id=f"response_{message.id}",
                sender=self.agent_id,
                recipient=message.sender,
                message_type=f"response_{message_type}",
                content=result,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error processing coaching message: {e}")
            return AgentMessage(
                id=f"error_{message.id}",
                sender=self.agent_id,
                recipient=message.sender,
                message_type="error",
                content={"error": str(e)},
                timestamp=datetime.now()
            )
    
    async def _explain_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert technical analysis into plain English explanation"""
        technical_analysis = data.get("technical_analysis", {})
        user_id = data.get("user_id")
        skill_level = data.get("skill_level", "beginner")
        explanation_style = data.get("explanation_style", "conversational")
        
        # Update user skill level
        self.user_skill_levels[user_id] = skill_level
        
        # Generate explanation based on skill level
        explanation = self._generate_explanation(technical_analysis, skill_level, explanation_style)
        key_takeaways = self._extract_key_takeaways(technical_analysis, skill_level)
        next_steps = self._suggest_next_steps(technical_analysis, skill_level)
        follow_up_questions = self._generate_follow_up_questions(technical_analysis, skill_level)
        
        return {
            "plain_english_explanation": explanation,
            "key_takeaways": key_takeaways,
            "next_steps": next_steps,
            "follow_up_questions": follow_up_questions,
            "coaching_tone": self.coaching_style
        }
    
    async def _answer_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Answer poker questions in a conversational manner"""
        question = data.get("question", "")
        user_id = data.get("user_id")
        context = data.get("context", {})
        
        # Analyze question to determine topic and complexity
        question_analysis = self._analyze_question(question)
        skill_level = self.user_skill_levels.get(user_id, "beginner")
        
        # Generate answer based on question type and user skill level
        answer = self._generate_answer(question, question_analysis, skill_level, context)
        examples = self._provide_examples(question_analysis, skill_level)
        related_concepts = self._suggest_related_concepts(question_analysis)
        
        return {
            "answer": answer,
            "examples": examples,
            "related_concepts": related_concepts,
            "question_type": question_analysis["type"],
            "confidence": question_analysis["confidence"]
        }
    
    async def _provide_encouragement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide motivational coaching and encouragement"""
        user_id = data.get("user_id")
        situation = data.get("situation", "general")
        progress_data = data.get("progress_data", {})
        
        # Generate personalized encouragement
        encouragement_message = self._generate_encouragement(situation, progress_data)
        progress_highlights = self._highlight_progress(progress_data)
        motivation = self._provide_motivation(situation)
        
        return {
            "encouragement_message": encouragement_message,
            "progress_highlights": progress_highlights,
            "motivation": motivation,
            "coaching_style": self.coaching_style
        }
    
    async def _create_learning_plan(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create personalized learning plan"""
        user_id = data.get("user_id")
        identified_leaks = data.get("identified_leaks", [])
        skill_level = data.get("skill_level", "beginner")
        time_commitment = data.get("time_commitment", "moderate")
        
        # Create structured learning plan
        learning_plan = self._build_learning_plan(identified_leaks, skill_level, time_commitment)
        weekly_goals = self._create_weekly_goals(learning_plan, time_commitment)
        practice_exercises = self._suggest_practice_exercises(identified_leaks, skill_level)
        
        return {
            "learning_plan": learning_plan,
            "weekly_goals": weekly_goals,
            "practice_exercises": practice_exercises,
            "estimated_timeline": self._estimate_improvement_timeline(identified_leaks, time_commitment)
        }
    
    def _generate_explanation(self, technical_analysis: Dict[str, Any], skill_level: str, style: str) -> str:
        """Generate plain English explanation of technical analysis"""
        # Start with appropriate template
        intro_templates = self.response_templates["hand_analysis"][skill_level]
        intro = random.choice(intro_templates)
        
        explanation_parts = [intro]
        
        # Explain key decisions
        if "key_decisions" in technical_analysis:
            explanation_parts.append("\\n\\nHere are the main decisions in this hand:")
            for decision in technical_analysis["key_decisions"]:
                plain_explanation = self._translate_decision(decision, skill_level)
                explanation_parts.append(f"• {plain_explanation}")
        
        # Explain mistakes if any
        if "mistakes" in technical_analysis and technical_analysis["mistakes"]:
            mistake_intro = random.choice(self.response_templates["mistake_explanation"])
            explanation_parts.append(f"\\n\\n{mistake_intro}")
            for mistake in technical_analysis["mistakes"]:
                plain_mistake = self._translate_mistake(mistake, skill_level)
                explanation_parts.append(f"• {plain_mistake}")
        
        # Add recommendations
        if "recommendations" in technical_analysis:
            explanation_parts.append("\\n\\nHere's what I recommend for next time:")
            for rec in technical_analysis["recommendations"]:
                plain_rec = self._translate_recommendation(rec, skill_level)
                explanation_parts.append(f"• {plain_rec}")
        
        # Add encouragement
        encouragement = random.choice(self.response_templates["encouragement"])
        explanation_parts.append(f"\\n\\n{encouragement}")
        
        return "".join(explanation_parts)
    
    def _translate_decision(self, decision: Dict[str, Any], skill_level: str) -> str:
        """Translate technical decision analysis to plain English"""
        street = decision.get("street", "")
        decision_type = decision.get("decision", "")
        analysis = decision.get("analysis", "")
        
        if skill_level == "beginner":
            return f"On the {street}, you {decision_type}. {self._simplify_analysis(analysis)}"
        elif skill_level == "intermediate":
            return f"{street.capitalize()}: {decision_type} - {analysis}"
        else:
            return f"{street.capitalize()} {decision_type}: {analysis} (alternatives: {', '.join(decision.get('alternatives', []))})"
    
    def _translate_mistake(self, mistake: Dict[str, Any], skill_level: str) -> str:
        """Translate technical mistake analysis to plain English"""
        mistake_type = mistake.get("type", "")
        description = mistake.get("description", "")
        
        if skill_level == "beginner":
            return self._simplify_mistake(description)
        else:
            return f"{mistake_type}: {description}"
    
    def _translate_recommendation(self, recommendation: str, skill_level: str) -> str:
        """Translate technical recommendation to plain English"""
        if skill_level == "beginner":
            return self._simplify_recommendation(recommendation)
        else:
            return recommendation
    
    def _simplify_analysis(self, analysis: str) -> str:
        """Simplify technical analysis for beginners"""
        # Replace technical terms with plain English
        simplified = analysis
        for technical_term, plain_term in self.plain_english_concepts.items():
            simplified = simplified.replace(technical_term, plain_term)
        return simplified
    
    def _simplify_mistake(self, mistake: str) -> str:
        """Simplify mistake explanation for beginners"""
        return self._simplify_analysis(mistake)
    
    def _simplify_recommendation(self, recommendation: str) -> str:
        """Simplify recommendation for beginners"""
        return self._simplify_analysis(recommendation)
    
    def _extract_key_takeaways(self, technical_analysis: Dict[str, Any], skill_level: str) -> List[str]:
        """Extract key takeaways from technical analysis"""
        takeaways = []
        
        if "preflop_analysis" in technical_analysis:
            takeaways.append("Pay attention to your position when deciding which hands to play")
        
        if "postflop_analysis" in technical_analysis:
            takeaways.append("Consider the board texture when deciding whether to bet or check")
        
        if skill_level == "beginner":
            takeaways.append("Focus on playing tight and aggressive")
            takeaways.append("Position is one of the most important factors in poker")
        
        return takeaways
    
    def _suggest_next_steps(self, technical_analysis: Dict[str, Any], skill_level: str) -> List[str]:
        """Suggest next steps for improvement"""
        next_steps = []
        
        if skill_level == "beginner":
            next_steps.extend([
                "Practice hand selection from different positions",
                "Study basic pot odds calculations",
                "Review more hands to identify patterns"
            ])
        elif skill_level == "intermediate":
            next_steps.extend([
                "Work on range construction",
                "Practice bet sizing in different situations",
                "Study opponent tendencies"
            ])
        else:
            next_steps.extend([
                "Analyze GTO solutions for similar spots",
                "Consider exploitative adjustments",
                "Review solver outputs for this board texture"
            ])
        
        return next_steps
    
    def _generate_follow_up_questions(self, technical_analysis: Dict[str, Any], skill_level: str) -> List[str]:
        """Generate follow-up questions to encourage learning"""
        questions = []
        
        if skill_level == "beginner":
            questions.extend([
                "What would you do if the opponent raised instead?",
                "How does your position affect this decision?",
                "What hands do you think your opponent could have?"
            ])
        elif skill_level == "intermediate":
            questions.extend([
                "How would you adjust against a tighter opponent?",
                "What's your plan for the turn card?",
                "How does stack depth affect this decision?"
            ])
        else:
            questions.extend([
                "What exploitative adjustments would you make?",
                "How does this compare to the GTO solution?",
                "What meta-game factors should you consider?"
            ])
        
        return questions[:3]  # Limit to 3 questions
    
    def _analyze_question(self, question: str) -> Dict[str, Any]:
        """Analyze user question to determine type and complexity"""
        question_lower = question.lower()
        
        # Determine question type
        if any(word in question_lower for word in ["what", "how", "why", "when"]):
            question_type = "conceptual"
        elif any(word in question_lower for word in ["should", "would", "better"]):
            question_type = "decision"
        elif any(word in question_lower for word in ["calculate", "odds", "equity"]):
            question_type = "mathematical"
        else:
            question_type = "general"
        
        # Determine complexity
        technical_terms = sum(1 for term in self.plain_english_concepts.keys() if term in question_lower)
        complexity = "advanced" if technical_terms > 2 else "intermediate" if technical_terms > 0 else "beginner"
        
        return {
            "type": question_type,
            "complexity": complexity,
            "confidence": 0.8,  # Mock confidence score
            "technical_terms": technical_terms
        }
    
    def _generate_answer(self, question: str, analysis: Dict[str, Any], skill_level: str, context: Dict[str, Any]) -> str:
        """Generate answer based on question analysis"""
        question_type = analysis["type"]
        
        if question_type == "conceptual":
            return self._answer_conceptual_question(question, skill_level, context)
        elif question_type == "decision":
            return self._answer_decision_question(question, skill_level, context)
        elif question_type == "mathematical":
            return self._answer_mathematical_question(question, skill_level, context)
        else:
            return self._answer_general_question(question, skill_level, context)
    
    def _answer_conceptual_question(self, question: str, skill_level: str, context: Dict[str, Any]) -> str:
        """Answer conceptual poker questions"""
        if "position" in question.lower():
            if skill_level == "beginner":
                return "Position in poker refers to where you sit at the table relative to the dealer button. It's super important because players in 'late position' (closer to the button) get to see what everyone else does before making their decision. This gives them a huge advantage!"
            else:
                return "Position is crucial in poker strategy. Late position allows you to see opponents' actions before deciding, enabling more profitable bluffs, better pot control, and more accurate hand reading. You can play a wider range of hands profitably from late position."
        
        return "That's a great question! Let me explain that concept in simple terms..."
    
    def _answer_decision_question(self, question: str, skill_level: str, context: Dict[str, Any]) -> str:
        """Answer decision-making questions"""
        return "For this type of decision, you want to consider several factors: your position, your hand strength, your opponent's tendencies, and the pot size. Let me break down how to think through this..."
    
    def _answer_mathematical_question(self, question: str, skill_level: str, context: Dict[str, Any]) -> str:
        """Answer mathematical poker questions"""
        if skill_level == "beginner":
            return "Don't worry about complex math right now! The basic idea is: if you're getting good odds (the pot is big compared to what you need to call), and you have a decent chance of winning, then calling is usually right."
        else:
            return "For pot odds calculations, you compare the size of the bet you need to call to the total pot size. If your equity (chance of winning) is higher than the pot odds, you should call."
    
    def _answer_general_question(self, question: str, skill_level: str, context: Dict[str, Any]) -> str:
        """Answer general poker questions"""
        return "That's an interesting question! Let me share some thoughts on that..."
    
    def _provide_examples(self, analysis: Dict[str, Any], skill_level: str) -> List[str]:
        """Provide relevant examples"""
        examples = []
        
        if analysis["type"] == "conceptual":
            examples.append("For example, if you're on the button (best position), you can play hands like A-9 offsuit profitably")
        elif analysis["type"] == "mathematical":
            examples.append("If the pot is $100 and your opponent bets $50, you're getting 3:1 odds")
        
        return examples
    
    def _suggest_related_concepts(self, analysis: Dict[str, Any]) -> List[str]:
        """Suggest related concepts to explore"""
        if analysis["type"] == "conceptual":
            return ["hand selection", "betting patterns", "reading opponents"]
        elif analysis["type"] == "mathematical":
            return ["implied odds", "reverse implied odds", "expected value"]
        else:
            return ["basic strategy", "position play", "bankroll management"]
    
    def _generate_encouragement(self, situation: str, progress_data: Dict[str, Any]) -> str:
        """Generate personalized encouragement"""
        if situation == "mistake":
            return "Don't worry about that mistake - even the best players in the world make similar errors. What matters is that you're learning from it!"
        elif situation == "improvement":
            return "I can see real improvement in your game! You're starting to think about poker the right way."
        else:
            return random.choice(self.response_templates["encouragement"])
    
    def _highlight_progress(self, progress_data: Dict[str, Any]) -> List[str]:
        """Highlight user's progress"""
        highlights = []
        
        if progress_data.get("hands_analyzed", 0) > 10:
            highlights.append(f"You've analyzed {progress_data['hands_analyzed']} hands - great dedication!")
        
        if progress_data.get("improvement_score", 0) > 0:
            highlights.append(f"Your play has improved by {progress_data['improvement_score']}% this week!")
        
        return highlights
    
    def _provide_motivation(self, situation: str) -> str:
        """Provide motivational message"""
        motivations = {
            "general": "Remember, every pro was once a beginner. Keep practicing and stay curious!",
            "mistake": "Mistakes are just learning opportunities in disguise. You're on the right path!",
            "improvement": "You're building solid fundamentals. Keep up the great work!",
            "plateau": "Plateaus are normal in poker. Push through and you'll reach the next level!"
        }
        
        return motivations.get(situation, motivations["general"])
    
    def _build_learning_plan(self, leaks: List[Dict[str, Any]], skill_level: str, time_commitment: str) -> Dict[str, Any]:
        """Build structured learning plan"""
        plan = {
            "focus_areas": [],
            "timeline": "4 weeks",
            "difficulty": skill_level,
            "time_per_week": time_commitment
        }
        
        # Prioritize leaks and create focus areas
        for leak in leaks[:3]:  # Focus on top 3 leaks
            plan["focus_areas"].append({
                "area": leak.get("leak_type", "general"),
                "description": leak.get("description", ""),
                "priority": leak.get("fix_priority", 1),
                "estimated_time": "1 week"
            })
        
        return plan
    
    def _create_weekly_goals(self, learning_plan: Dict[str, Any], time_commitment: str) -> List[str]:
        """Create weekly learning goals"""
        goals = []
        
        for i, focus_area in enumerate(learning_plan["focus_areas"]):
            week = i + 1
            area = focus_area["area"]
            goals.append(f"Week {week}: Focus on improving {area}")
        
        return goals
    
    def _suggest_practice_exercises(self, leaks: List[Dict[str, Any]], skill_level: str) -> List[Dict[str, Any]]:
        """Suggest practice exercises"""
        exercises = []
        
        for leak in leaks[:3]:
            leak_type = leak.get("leak_type", "general")
            
            if "preflop" in leak_type:
                exercises.append({
                    "title": "Preflop Hand Selection Practice",
                    "description": "Practice opening ranges from different positions",
                    "duration": "15 minutes daily"
                })
            elif "postflop" in leak_type:
                exercises.append({
                    "title": "Board Texture Analysis",
                    "description": "Analyze different flop textures and betting strategies",
                    "duration": "20 minutes daily"
                })
        
        return exercises
    
    def _estimate_improvement_timeline(self, leaks: List[Dict[str, Any]], time_commitment: str) -> str:
        """Estimate timeline for improvement"""
        num_leaks = len(leaks)
        
        if time_commitment == "light":
            weeks = num_leaks * 2
        elif time_commitment == "moderate":
            weeks = num_leaks * 1.5
        else:  # intensive
            weeks = num_leaks
        
        return f"{int(weeks)} weeks"

