"""
Base Agent Class for PokerPy Agentic System
Inspired by Harmony Engine Architecture
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

class AgentStatus(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    COMPLETED = "completed"

@dataclass
class AgentMessage:
    """Standard message format for inter-agent communication"""
    id: str
    sender: str
    recipient: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime
    priority: int = 1
    requires_response: bool = False

@dataclass
class AgentCapability:
    """Defines what an agent can do"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

class BaseAgent(ABC):
    """
    Base class for all PokerPy agents
    Provides core functionality for communication, state management, and execution
    """
    
    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.capabilities: List[AgentCapability] = []
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.response_handlers: Dict[str, Callable] = {}
        self.context: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"agent.{agent_id}")
        
        # Performance metrics
        self.metrics = {
            "messages_processed": 0,
            "errors": 0,
            "average_response_time": 0.0,
            "last_activity": None
        }
        
    @abstractmethod
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming message and return response if needed"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """Return list of agent capabilities"""
        pass
    
    async def send_message(self, recipient: str, message_type: str, content: Dict[str, Any], 
                          priority: int = 1, requires_response: bool = False) -> str:
        """Send message to another agent via orchestrator"""
        message_id = f"{self.agent_id}_{datetime.now().timestamp()}"
        message = AgentMessage(
            id=message_id,
            sender=self.agent_id,
            recipient=recipient,
            message_type=message_type,
            content=content,
            timestamp=datetime.now(),
            priority=priority,
            requires_response=requires_response
        )
        
        # In a real implementation, this would go through the orchestrator
        self.logger.info(f"Sending message {message_id} to {recipient}")
        return message_id
    
    async def receive_message(self, message: AgentMessage):
        """Receive message and add to processing queue"""
        await self.message_queue.put(message)
        self.logger.info(f"Received message {message.id} from {message.sender}")
    
    async def start(self):
        """Start the agent's message processing loop"""
        self.logger.info(f"Starting agent {self.name}")
        self.status = AgentStatus.IDLE
        
        while True:
            try:
                # Wait for messages with timeout
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self._handle_message(message)
            except asyncio.TimeoutError:
                # Periodic maintenance tasks
                await self._maintenance()
            except Exception as e:
                self.logger.error(f"Error in message loop: {e}")
                self.metrics["errors"] += 1
                self.status = AgentStatus.ERROR
    
    async def _handle_message(self, message: AgentMessage):
        """Internal message handling with metrics and error handling"""
        start_time = datetime.now()
        self.status = AgentStatus.PROCESSING
        
        try:
            response = await self.process_message(message)
            
            if response and message.requires_response:
                # Send response back through orchestrator
                await self.send_message(
                    recipient=message.sender,
                    message_type=f"response_{message.message_type}",
                    content=response.content if response else {}
                )
            
            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.metrics["messages_processed"] += 1
            self.metrics["average_response_time"] = (
                (self.metrics["average_response_time"] * (self.metrics["messages_processed"] - 1) + processing_time) 
                / self.metrics["messages_processed"]
            )
            self.metrics["last_activity"] = datetime.now()
            
            self.status = AgentStatus.COMPLETED
            
        except Exception as e:
            self.logger.error(f"Error processing message {message.id}: {e}")
            self.metrics["errors"] += 1
            self.status = AgentStatus.ERROR
        
        finally:
            self.status = AgentStatus.IDLE
    
    async def _maintenance(self):
        """Periodic maintenance tasks"""
        # Clean up old context data, update metrics, etc.
        pass
    
    def update_context(self, key: str, value: Any):
        """Update agent context"""
        self.context[key] = value
        self.logger.debug(f"Updated context: {key}")
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get value from agent context"""
        return self.context.get(key, default)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "capabilities": [cap.name for cap in self.get_capabilities()],
            "metrics": self.metrics,
            "queue_size": self.message_queue.qsize()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "capabilities": [asdict(cap) for cap in self.get_capabilities()],
            "metrics": self.metrics
        }

