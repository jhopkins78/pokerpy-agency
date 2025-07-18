"""
Compatibility Wrapper for PokerPy Agent Migration
Provides seamless transition from old agents to RAG-enhanced agents
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging

from src.agents.base_agent import BaseAgent, AgentMessage, AgentCapability
from .coach_rag_enhanced import RAGEnhancedCoachAgent
from Agentic_Rag.rag.rag_orchestrator import RAGOrchestrator

logger = logging.getLogger(__name__)

class CompatibilityWrapper:
    """
    Wrapper that provides backward compatibility for old agent interfaces
    while routing requests to new RAG-enhanced agents
    """
    
    def __init__(self, rag_orchestrator: RAGOrchestrator = None):
        self.rag_orchestrator = rag_orchestrator
        self.agent_mapping = {}
        self.legacy_agents = {}
        self.enhanced_agents = {}
        
        # Initialize agent mappings
        self._initialize_agent_mappings()
        
        logger.info("Compatibility wrapper initialized")
    
    def _initialize_agent_mappings(self):
        """Initialize mappings between old and new agents"""
        
        # Create RAG-enhanced agents
        if self.rag_orchestrator:
            self.enhanced_agents['coach'] = RAGEnhancedCoachAgent(self.rag_orchestrator)
        
        # Map old agent IDs to new agents
        self.agent_mapping = {
            'coach': 'coach',  # Old coach -> RAG-enhanced coach
            'ai_coach': 'coach',  # Alternative naming
            'poker_coach': 'coach'  # Alternative naming
        }
        
        logger.info(f"Agent mappings initialized: {list(self.agent_mapping.keys())}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID, with automatic mapping to enhanced versions"""
        
        # Map old agent ID to new agent ID
        mapped_id = self.agent_mapping.get(agent_id, agent_id)
        
        # Return enhanced agent if available
        if mapped_id in self.enhanced_agents:
            return self.enhanced_agents[mapped_id]
        
        # Fallback to legacy agent if available
        if agent_id in self.legacy_agents:
            logger.warning(f"Using legacy agent for {agent_id}")
            return self.legacy_agents[agent_id]
        
        logger.error(f"Agent not found: {agent_id}")
        return None
    
    def register_legacy_agent(self, agent: BaseAgent):
        """Register a legacy agent as fallback"""
        self.legacy_agents[agent.agent_id] = agent
        logger.info(f"Registered legacy agent: {agent.agent_id}")
    
    def register_enhanced_agent(self, agent_id: str, agent: BaseAgent):
        """Register an enhanced agent"""
        self.enhanced_agents[agent_id] = agent
        logger.info(f"Registered enhanced agent: {agent_id}")
    
    async def process_legacy_message(self, agent_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message using legacy format and convert to new format
        Provides backward compatibility for old API calls
        """
        
        try:
            # Get the appropriate agent
            agent = self.get_agent(agent_id)
            if not agent:
                return {
                    'success': False,
                    'error': f'Agent not found: {agent_id}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Convert legacy message format to new format
            agent_message = self._convert_legacy_message(message_data)
            
            # Process with enhanced agent
            response = await agent.process_message(agent_message)
            
            # Convert response back to legacy format
            legacy_response = self._convert_to_legacy_response(response)
            
            return {
                'success': True,
                'response': legacy_response,
                'agent_id': agent_id,
                'enhanced': True,  # Indicate this came from enhanced agent
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing legacy message: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _convert_legacy_message(self, message_data: Dict[str, Any]) -> AgentMessage:
        """Convert legacy message format to new AgentMessage format"""
        
        # Extract common fields
        message_type = message_data.get('type', 'general_request')
        content = message_data.get('content', {})
        user_id = message_data.get('user_id', 'anonymous')
        
        # Handle different legacy message formats
        if 'query' in message_data:
            # Legacy coaching request format
            message_type = 'coaching_request'
            content = {
                'query': message_data['query'],
                'user_id': user_id,
                'context': message_data.get('context', {})
            }
        elif 'hand_analysis' in message_data:
            # Legacy hand analysis format
            message_type = 'analyze_hand'
            content = {
                'hand_analysis': message_data['hand_analysis'],
                'user_id': user_id,
                'context': message_data.get('context', {})
            }
        elif 'concept' in message_data:
            # Legacy concept explanation format
            message_type = 'explain_concept'
            content = {
                'concept': message_data['concept'],
                'user_id': user_id,
                'context': message_data.get('context', {})
            }
        
        # Create AgentMessage
        return AgentMessage(
            id=f"legacy_{datetime.now().timestamp()}",
            sender=user_id,
            recipient="coach",
            message_type=message_type,
            content=content,
            timestamp=datetime.now(),
            priority=message_data.get('priority', 1),
            requires_response=True
        )
    
    def _convert_to_legacy_response(self, response: AgentMessage) -> Dict[str, Any]:
        """Convert new AgentMessage response to legacy format"""
        
        if not response:
            return {
                'message': 'No response generated',
                'confidence': 0.0
            }
        
        # Extract response content
        content = response.content
        
        # Build legacy response format
        legacy_response = {
            'message': content.get('response', content.get('explanation', 'Response generated')),
            'confidence': content.get('confidence', 1.0),
            'timestamp': response.timestamp.isoformat() if response.timestamp else datetime.now().isoformat()
        }
        
        # Add optional fields if present
        if 'sources' in content:
            legacy_response['sources'] = content['sources']
        
        if 'learning_points' in content:
            legacy_response['learning_points'] = content['learning_points']
        
        if 'follow_up_suggestions' in content:
            legacy_response['suggestions'] = content['follow_up_suggestions']
        
        if 'related_concepts' in content:
            legacy_response['related_concepts'] = content['related_concepts']
        
        return legacy_response
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of an agent with compatibility information"""
        
        agent = self.get_agent(agent_id)
        if not agent:
            return {
                'agent_id': agent_id,
                'status': 'not_found',
                'enhanced': False
            }
        
        # Get agent status
        status = agent.get_status() if hasattr(agent, 'get_status') else {}
        
        # Add compatibility information
        status.update({
            'agent_id': agent_id,
            'enhanced': agent_id in self.enhanced_agents,
            'legacy_compatible': True,
            'rag_enabled': hasattr(agent, 'rag_orchestrator') and agent.rag_orchestrator is not None
        })
        
        return status
    
    def list_available_agents(self) -> Dict[str, Any]:
        """List all available agents with their capabilities"""
        
        agents_info = {}
        
        # Enhanced agents
        for agent_id, agent in self.enhanced_agents.items():
            agents_info[agent_id] = {
                'type': 'enhanced',
                'name': agent.name,
                'description': agent.description,
                'capabilities': [cap.name for cap in agent.get_capabilities()],
                'rag_enabled': True
            }
        
        # Legacy agents
        for agent_id, agent in self.legacy_agents.items():
            if agent_id not in agents_info:  # Don't override enhanced agents
                agents_info[agent_id] = {
                    'type': 'legacy',
                    'name': agent.name,
                    'description': agent.description,
                    'capabilities': [cap.name for cap in agent.get_capabilities()],
                    'rag_enabled': False
                }
        
        return {
            'agents': agents_info,
            'total_agents': len(agents_info),
            'enhanced_agents': len(self.enhanced_agents),
            'legacy_agents': len(self.legacy_agents)
        }
    
    def migrate_conversation_history(self, user_id: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Migrate conversation history to new format"""
        
        migrated_history = []
        
        for entry in history:
            # Convert each history entry to new format
            migrated_entry = {
                'timestamp': entry.get('timestamp', datetime.now().isoformat()),
                'user_message': entry.get('user_message', entry.get('query', '')),
                'agent_response': entry.get('agent_response', entry.get('response', '')),
                'message_type': entry.get('type', 'general_request'),
                'enhanced': False,  # Mark as legacy
                'migrated': True
            }
            
            migrated_history.append(migrated_entry)
        
        logger.info(f"Migrated {len(migrated_history)} conversation entries for user {user_id}")
        return migrated_history


class LegacyCoachAgent(BaseAgent):
    """
    Legacy coach agent wrapper that routes to RAG-enhanced agent
    Maintains exact same interface as original coach agent
    """
    
    def __init__(self, compatibility_wrapper: CompatibilityWrapper):
        super().__init__(
            agent_id="coach",
            name="AI Poker Coach",
            description="Provides conversational AI coaching (RAG-enhanced)"
        )
        
        self.wrapper = compatibility_wrapper
        self.enhanced_agent = compatibility_wrapper.get_agent("coach")
    
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process message using enhanced agent"""
        if self.enhanced_agent:
            return await self.enhanced_agent.process_message(message)
        else:
            # Fallback to basic response
            return self._create_fallback_response(message)
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return capabilities (enhanced if available)"""
        if self.enhanced_agent:
            return self.enhanced_agent.get_capabilities()
        else:
            return [
                AgentCapability(
                    name="coaching_request",
                    description="Provide basic poker coaching",
                    input_schema={"query": "str", "user_id": "str"},
                    output_schema={"response": "str"}
                )
            ]
    
    def _create_fallback_response(self, message: AgentMessage) -> AgentMessage:
        """Create fallback response when enhanced agent not available"""
        return AgentMessage(
            id=f"fallback_{datetime.now().timestamp()}",
            sender=self.agent_id,
            recipient=message.sender,
            message_type="response",
            content={
                'response': 'I apologize, but the enhanced coaching system is temporarily unavailable. Please try again later.',
                'confidence': 0.1,
                'fallback': True
            },
            timestamp=datetime.now()
        )
