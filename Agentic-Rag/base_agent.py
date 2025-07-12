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