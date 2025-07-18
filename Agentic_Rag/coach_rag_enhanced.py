"""
RAG-Enhanced Coach Agent for PokerPy
Provides conversational AI coaching enhanced with knowledge retrieval
"""

import json
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.agents.base_agent import BaseAgent, AgentMessage, AgentCapability
from rag.rag_orchestrator import RAGOrchestrator
from rag.knowledge_base import SkillLevel, DocumentType

class RAGEnhancedCoachAgent(BaseAgent):
    """
    Conversational AI coach enhanced with RAG capabilities
    Provides personalized coaching with knowledge-backed responses
    """
    
    def __init__(self, rag_orchestrator: RAGOrchestrator = None):
        super().__init__(
            agent_id="rag_coach",
            name="RAG-Enhanced AI Poker Coach", 
            description="Provides conversational AI coaching enhanced with knowledge retrieval"
        )
        
        self.rag_orchestrator = rag_orchestrator
        
        # Coaching personality and style
        self.coaching_style = "encouraging"  # encouraging, direct, analytical
        self.user_skill_levels = {}  # user_id -> skill_level
        self.conversation_history = {}  # user_id -> conversation_history
        
        # Enhanced response templates with RAG integration
        self.response_templates = {
            "hand_analysis": {
                "beginner": [
                    "Let me break this down in simple terms using some proven strategies...",
                    "Here's what happened in your hand, backed by poker fundamentals...",
                    "Don't worry, this is a common spot. Based on established poker theory..."
                ],
                "intermediate": [
                    "Looking at this hand, there are key concepts from poker strategy to consider...",
                    "This is a great learning opportunity. Let me reference some strategic principles...",
                    "You're on the right track, but here's how experts approach this..."
                ],
                "advanced": [
                    "This hand presents interesting strategic considerations. Let me reference advanced theory...",
                    "Based on current poker research and GTO principles...",
                    "From both theoretical and practical perspectives, considering recent strategic developments..."
                ]
            },
            "concept_explanation": {
                "beginner": [
                    "This concept is fundamental to poker success. Let me explain it simply...",
                    "Here's a beginner-friendly explanation of this important idea...",
                    "This might seem complex, but it's actually quite straightforward..."
                ],
                "intermediate": [
                    "You're ready for a deeper understanding of this concept...",
                    "Building on what you already know, here's the next level...",
                    "This concept connects to several other strategic principles..."
                ],
                "advanced": [
                    "This concept has some nuanced applications in advanced play...",
                    "The theoretical foundation of this concept involves...",
                    "Recent developments in poker theory have refined our understanding..."
                ]
            },
            "encouragement": [
                "You're making great progress! Keep up the good work.",
                "Every hand is a learning opportunity, and you're learning fast!",
                "Poker is a journey, and you're on the right path.",
                "Your understanding is improving with each session!"
            ]
        }
        
        # Knowledge integration settings
        self.knowledge_integration = {
            'always_enhance': True,
            'min_confidence_threshold': 0.3,
            'max_knowledge_sources': 2,
            'prefer_skill_appropriate': True
        }
    
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process coaching requests with RAG enhancement"""
        try:
            if message.message_type == "coaching_request":
                return await self._handle_coaching_request(message)
            elif message.message_type == "explain_concept":
                return await self._handle_concept_explanation(message)
            elif message.message_type == "analyze_hand":
                return await self._handle_hand_analysis_coaching(message)
            elif message.message_type == "general_question":
                return await self._handle_general_question(message)
            else:
                return await self._handle_unknown_request(message)
        
        except Exception as e:
            self.logger.error(f"Error processing coaching message: {e}")
            return self._create_error_response(message, "I'm having trouble processing your request. Please try again.")
    
    async def _handle_coaching_request(self, message: AgentMessage) -> AgentMessage:
        """Handle general coaching requests with RAG enhancement"""
        try:
            content = message.content
            user_id = content.get('user_id', 'anonymous')
            query = content.get('query', '')
            context = content.get('context', {})
            
            # Determine user skill level
            skill_level = self._get_user_skill_level(user_id, context)
            
            # Generate base response
            base_response = await self._generate_base_coaching_response(query, skill_level, context)
            
            # Enhance with RAG if available
            if self.rag_orchestrator and self.knowledge_integration['always_enhance']:
                enhanced_response = await self.rag_orchestrator.enhance_agent_response(
                    agent_id=self.agent_id,
                    original_query=query,
                    agent_response=base_response,
                    context={
                        'skill_level': skill_level.value,
                        'user_id': user_id,
                        'coaching_context': True
                    }
                )
                
                final_response = enhanced_response.enhanced_response
                sources = enhanced_response.sources
                confidence = enhanced_response.confidence_score
            else:
                final_response = base_response
                sources = []
                confidence = 0.7
            
            # Update conversation history
            self._update_conversation_history(user_id, query, final_response)
            
            # Prepare response
            response_content = {
                'response': final_response,
                'coaching_style': self.coaching_style,
                'skill_level': skill_level.value,
                'confidence': confidence,
                'sources': sources,
                'follow_up_suggestions': self._generate_follow_up_suggestions(query, skill_level),
                'success': True
            }
            
            return self._create_response(message, response_content)
        
        except Exception as e:
            self.logger.error(f"Error in coaching request: {e}")
            return self._create_error_response(message, "I'm having trouble with your coaching request.")
    
    async def _handle_concept_explanation(self, message: AgentMessage) -> AgentMessage:
        """Handle concept explanation requests with knowledge retrieval"""
        try:
            content = message.content
            concept = content.get('concept', '')
            user_id = content.get('user_id', 'anonymous')
            context = content.get('context', {})
            
            skill_level = self._get_user_skill_level(user_id, context)
            
            # Generate explanation using RAG
            if self.rag_orchestrator:
                # First retrieve relevant knowledge about the concept
                retrieval_message = AgentMessage(
                    id=f"concept_retrieval_{datetime.now().timestamp()}",
                    sender=self.agent_id,
                    recipient="retrieval_agent",
                    message_type="retrieve_knowledge",
                    content={
                        'query': f"explain {concept} poker concept",
                        'context': {
                            'skill_level': skill_level.value,
                            'document_types': ['concept', 'strategy', 'tutorial']
                        },
                        'max_results': 3
                    },
                    timestamp=datetime.now()
                )
                
                # Get knowledge-based explanation
                base_explanation = await self._generate_concept_explanation(concept, skill_level)
                
                # Enhance with retrieved knowledge
                enhanced_response = await self.rag_orchestrator.enhance_agent_response(
                    agent_id=self.agent_id,
                    original_query=f"explain {concept}",
                    agent_response=base_explanation,
                    context={'skill_level': skill_level.value, 'concept_explanation': True}
                )
                
                final_explanation = enhanced_response.enhanced_response
                sources = enhanced_response.sources
                confidence = enhanced_response.confidence_score
            else:
                final_explanation = await self._generate_concept_explanation(concept, skill_level)
                sources = []
                confidence = 0.6
            
            response_content = {
                'concept': concept,
                'explanation': final_explanation,
                'skill_level': skill_level.value,
                'confidence': confidence,
                'sources': sources,
                'related_concepts': self._get_related_concepts(concept),
                'practice_suggestions': self._get_practice_suggestions(concept, skill_level),
                'success': True
            }
            
            return self._create_response(message, response_content)
        
        except Exception as e:
            self.logger.error(f"Error explaining concept: {e}")
            return self._create_error_response(message, f"I'm having trouble explaining {concept}.")
    
    async def _handle_hand_analysis_coaching(self, message: AgentMessage) -> AgentMessage:
        """Handle hand analysis with coaching perspective"""
        try:
            content = message.content
            hand_analysis = content.get('hand_analysis', {})
            user_id = content.get('user_id', 'anonymous')
            
            skill_level = self._get_user_skill_level(user_id, content.get('context', {}))
            
            # Generate coaching response based on hand analysis
            coaching_response = await self._generate_hand_coaching(hand_analysis, skill_level)
            
            # Enhance with strategic knowledge if available
            if self.rag_orchestrator:
                # Create query based on hand situation
                situation_query = self._extract_situation_query(hand_analysis)
                
                enhanced_response = await self.rag_orchestrator.enhance_agent_response(
                    agent_id=self.agent_id,
                    original_query=situation_query,
                    agent_response=coaching_response,
                    context={
                        'skill_level': skill_level.value,
                        'hand_analysis': True,
                        'situation': hand_analysis.get('situation', {})
                    }
                )
                
                final_response = enhanced_response.enhanced_response
                sources = enhanced_response.sources
                confidence = enhanced_response.confidence_score
            else:
                final_response = coaching_response
                sources = []
                confidence = 0.7
            
            response_content = {
                'coaching_response': final_response,
                'key_learning_points': self._extract_learning_points(hand_analysis, skill_level),
                'improvement_suggestions': self._generate_improvement_suggestions(hand_analysis, skill_level),
                'confidence': confidence,
                'sources': sources,
                'success': True
            }
            
            return self._create_response(message, response_content)
        
        except Exception as e:
            self.logger.error(f"Error in hand analysis coaching: {e}")
            return self._create_error_response(message, "I'm having trouble analyzing this hand.")
    
    async def _generate_base_coaching_response(self, query: str, skill_level: SkillLevel, context: Dict[str, Any]) -> str:
        """Generate base coaching response before RAG enhancement"""
        # Select appropriate template
        templates = self.response_templates.get("hand_analysis", {}).get(skill_level.value, [])
        if templates:
            intro = random.choice(templates)
        else:
            intro = "Let me help you with that..."
        
        # Generate response based on query type and skill level
        if "position" in query.lower():
            response = f"{intro} Position is crucial in poker. "
            if skill_level == SkillLevel.BEGINNER:
                response += "Think of it like this: the later you act, the more information you have about what other players are doing."
            else:
                response += "Your position determines your range construction and post-flop playability considerations."
        
        elif "pot odds" in query.lower():
            response = f"{intro} Pot odds help you make profitable decisions. "
            if skill_level == SkillLevel.BEGINNER:
                response += "Simply put, if you need to call $10 to win a $50 pot, you need to win more than 1 in 6 times to profit."
            else:
                response += "Calculate the ratio of the current pot size to the cost of your call, then compare to your equity."
        
        else:
            # Generic response
            response = f"{intro} This is a great question that many players struggle with. Let me break it down for you."
        
        return response
    
    async def _generate_concept_explanation(self, concept: str, skill_level: SkillLevel) -> str:
        """Generate concept explanation appropriate for skill level"""
        concept_lower = concept.lower()
        
        if concept_lower in ["pot odds", "odds"]:
            if skill_level == SkillLevel.BEGINNER:
                return "Pot odds are like a simple math problem that helps you decide whether to call a bet. If someone bets $10 into a $30 pot, you need to call $10 to win $40 total. That means you need to win at least 1 out of every 4 times (25%) to break even."
            else:
                return "Pot odds represent the ratio between the current pot size and the cost of a call. They're essential for determining the minimum equity required for a profitable call. The formula is: Required Equity = Call Amount / (Pot + Call Amount)."
        
        elif concept_lower in ["position"]:
            if skill_level == SkillLevel.BEGINNER:
                return "Position in poker is where you sit relative to the dealer button. Being 'in position' means you act after your opponents, giving you more information to make better decisions. It's like having the last word in a conversation."
            else:
                return "Position is arguably the most important factor in poker strategy. Late position allows for wider opening ranges, more profitable bluffs, better pot control, and superior information gathering. It directly impacts your expected value in every hand."
        
        else:
            return f"The concept of {concept} is an important part of poker strategy. Let me explain how it works and why it matters for your game."
    
    def _get_user_skill_level(self, user_id: str, context: Dict[str, Any]) -> SkillLevel:
        """Determine user skill level from context or history"""
        # Check context first
        if 'skill_level' in context:
            try:
                return SkillLevel(context['skill_level'])
            except ValueError:
                pass
        
        # Check stored user data
        if user_id in self.user_skill_levels:
            return self.user_skill_levels[user_id]
        
        # Default to beginner
        return SkillLevel.BEGINNER
    
    def _update_conversation_history(self, user_id: str, query: str, response: str):
        """Update conversation history for personalization"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response
        })
        
        # Keep only last 10 interactions
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
    
    def _generate_follow_up_suggestions(self, query: str, skill_level: SkillLevel) -> List[str]:
        """Generate follow-up suggestions based on the query"""
        suggestions = []
        
        if "position" in query.lower():
            suggestions = [
                "Would you like to practice position-based hand selection?",
                "Should we discuss how position affects post-flop play?",
                "Want to learn about positional betting strategies?"
            ]
        elif "pot odds" in query.lower():
            suggestions = [
                "Would you like to practice calculating pot odds?",
                "Should we discuss implied odds next?",
                "Want to learn about equity calculations?"
            ]
        else:
            suggestions = [
                "Would you like to explore this topic further?",
                "Should we look at some practical examples?",
                "Want to discuss related concepts?"
            ]
        
        return suggestions[:2]  # Return top 2 suggestions
    
    def _get_related_concepts(self, concept: str) -> List[str]:
        """Get related concepts for cross-learning"""
        concept_map = {
            "pot odds": ["equity", "implied odds", "expected value"],
            "position": ["range construction", "post-flop play", "betting patterns"],
            "equity": ["pot odds", "expected value", "hand strength"],
            "bluffing": ["value betting", "range balancing", "opponent reads"]
        }
        
        return concept_map.get(concept.lower(), [])
    
    def _get_practice_suggestions(self, concept: str, skill_level: SkillLevel) -> List[str]:
        """Get practice suggestions for the concept"""
        if concept.lower() == "pot odds":
            if skill_level == SkillLevel.BEGINNER:
                return [
                    "Practice with simple pot odds scenarios",
                    "Use the 4-2 rule for quick equity estimation",
                    "Start with obvious calling/folding spots"
                ]
            else:
                return [
                    "Practice complex multi-way pot odds calculations",
                    "Include implied odds in your analysis",
                    "Work on real-time calculation speed"
                ]
        
        return ["Practice this concept in low-stakes games", "Review hand histories focusing on this concept"]
    
    async def _generate_hand_coaching(self, hand_analysis: Dict[str, Any], skill_level: SkillLevel) -> str:
        """Generate coaching response for hand analysis"""
        # Extract key information from hand analysis
        action = hand_analysis.get('recommended_action', 'unknown')
        reasoning = hand_analysis.get('reasoning', '')
        
        # Generate coaching response
        if skill_level == SkillLevel.BEGINNER:
            response = f"Looking at this hand, the recommended play is to {action}. Here's why in simple terms: {reasoning}"
        else:
            response = f"The optimal play here is to {action}. The strategic reasoning involves: {reasoning}"
        
        return response
    
    def _extract_learning_points(self, hand_analysis: Dict[str, Any], skill_level: SkillLevel) -> List[str]:
        """Extract key learning points from hand analysis"""
        points = []
        
        if 'position' in hand_analysis:
            points.append(f"Position consideration: {hand_analysis['position']}")
        
        if 'pot_odds' in hand_analysis:
            points.append(f"Pot odds analysis: {hand_analysis['pot_odds']}")
        
        if not points:
            points.append("Focus on fundamental decision-making process")
        
        return points
    
    def _generate_improvement_suggestions(self, hand_analysis: Dict[str, Any], skill_level: SkillLevel) -> List[str]:
        """Generate specific improvement suggestions"""
        suggestions = []
        
        if skill_level == SkillLevel.BEGINNER:
            suggestions = [
                "Focus on position awareness in similar spots",
                "Practice pot odds calculations",
                "Review basic hand strength concepts"
            ]
        else:
            suggestions = [
                "Consider range construction in this position",
                "Analyze opponent tendencies more deeply",
                "Explore GTO vs exploitative considerations"
            ]
        
        return suggestions
    
    def _extract_situation_query(self, hand_analysis: Dict[str, Any]) -> str:
        """Extract a query string from hand analysis for knowledge retrieval"""
        situation = hand_analysis.get('situation', {})
        position = situation.get('position', '')
        action = situation.get('action', '')
        
        return f"{position} {action} poker strategy"
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return enhanced agent capabilities"""
        return [
            AgentCapability(
                name="coaching_request", 
                description="Provide personalized poker coaching",
                input_schema={"query": "str", "user_id": "str", "context": "dict"},
                output_schema={"response": "str", "confidence": "float", "sources": "list"}
            ),
            AgentCapability(
                name="explain_concept", 
                description="Explain poker concepts with knowledge backing",
                input_schema={"concept": "str", "user_id": "str", "context": "dict"},
                output_schema={"explanation": "str", "related_concepts": "list", "sources": "list"}
            ),
            AgentCapability(
                name="analyze_hand", 
                description="Provide coaching perspective on hand analysis",
                input_schema={"hand_analysis": "dict", "user_id": "str"},
                output_schema={"coaching_response": "str", "learning_points": "list", "sources": "list"}
            ),
            AgentCapability(
                name="general_question", 
                description="Answer general poker questions",
                input_schema={"question": "str", "context": "dict"},
                output_schema={"answer": "str", "confidence": "float", "sources": "list"}
            ),
            AgentCapability(
                name="rag_enhanced_responses", 
                description="Enhanced responses with knowledge retrieval",
                input_schema={"query": "str", "context": "dict"},
                output_schema={"enhanced_response": "str", "sources": "list", "confidence": "float"}
            )
        ]
    
    def _create_response(self, original_message: AgentMessage, content: Any) -> AgentMessage:
        """Create response message"""
        return AgentMessage(
            id=f"coach_response_{original_message.id}",
            sender=self.agent_id,
            recipient=original_message.sender,
            message_type=f"response_{original_message.message_type}",
            content=content,
            timestamp=datetime.now()
        )
    
    def _create_error_response(self, original_message: AgentMessage, error_message: str) -> AgentMessage:
        """Create error response message"""
        return AgentMessage(
            id=f"coach_error_{original_message.id}",
            sender=self.agent_id,
            recipient=original_message.sender,
            message_type=f"error_{original_message.message_type}",
            content={
                'success': False,
                'error': error_message,
                'timestamp': datetime.now().isoformat()
            },
            timestamp=datetime.now()
        )
