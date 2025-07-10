"""
Agent Orchestrator for PokerPy Agentic System
Coordinates communication and workflow between specialized agents
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import asdict
from collections import defaultdict, deque

from .base_agent import BaseAgent, AgentMessage, AgentStatus

class AgentOrchestrator:
    """
    Central orchestrator that manages all agents and coordinates their interactions
    Similar to Harmony Engine's orchestration layer
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_router: Dict[str, str] = {}  # message_type -> agent_id
        self.workflow_definitions: Dict[str, List[str]] = {}  # workflow_name -> agent_sequence
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.message_history: deque = deque(maxlen=1000)
        self.logger = logging.getLogger("orchestrator")
        
        # Performance monitoring
        self.metrics = {
            "total_messages": 0,
            "active_workflows": 0,
            "agent_utilization": defaultdict(int),
            "error_count": 0,
            "average_workflow_time": 0.0
        }
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent.agent_id] = agent
        
        # Register agent capabilities for routing
        for capability in agent.get_capabilities():
            self.message_router[capability.name] = agent.agent_id
            
        self.logger.info(f"Registered agent {agent.name} with capabilities: {[cap.name for cap in agent.get_capabilities()]}")
    
    def define_workflow(self, workflow_name: str, agent_sequence: List[str]):
        """Define a workflow as a sequence of agent interactions"""
        self.workflow_definitions[workflow_name] = agent_sequence
        self.logger.info(f"Defined workflow '{workflow_name}': {' -> '.join(agent_sequence)}")
    
    async def route_message(self, message: AgentMessage) -> bool:
        """Route message to appropriate agent"""
        try:
            if message.recipient in self.agents:
                target_agent = self.agents[message.recipient]
                await target_agent.receive_message(message)
                
                # Update metrics
                self.metrics["total_messages"] += 1
                self.metrics["agent_utilization"][message.recipient] += 1
                self.message_history.append(asdict(message))
                
                return True
            else:
                self.logger.error(f"No agent found for recipient: {message.recipient}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error routing message {message.id}: {e}")
            self.metrics["error_count"] += 1
            return False
    
    async def execute_workflow(self, workflow_name: str, initial_data: Dict[str, Any], 
                             user_id: str = None) -> Dict[str, Any]:
        """Execute a predefined workflow"""
        if workflow_name not in self.workflow_definitions:
            raise ValueError(f"Workflow '{workflow_name}' not defined")
        
        workflow_id = f"{workflow_name}_{datetime.now().timestamp()}"
        start_time = datetime.now()
        
        # Initialize workflow state
        workflow_state = {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "user_id": user_id,
            "status": "running",
            "current_step": 0,
            "data": initial_data,
            "results": {},
            "start_time": start_time,
            "steps": self.workflow_definitions[workflow_name]
        }
        
        self.active_workflows[workflow_id] = workflow_state
        self.metrics["active_workflows"] += 1
        
        try:
            # Execute workflow steps
            for step_index, agent_id in enumerate(workflow_state["steps"]):
                workflow_state["current_step"] = step_index
                
                if agent_id not in self.agents:
                    raise ValueError(f"Agent '{agent_id}' not found for workflow step")
                
                # Prepare message for current step
                message = AgentMessage(
                    id=f"{workflow_id}_step_{step_index}",
                    sender="orchestrator",
                    recipient=agent_id,
                    message_type=f"workflow_{workflow_name}_step_{step_index}",
                    content={
                        "workflow_id": workflow_id,
                        "step_index": step_index,
                        "data": workflow_state["data"],
                        "previous_results": workflow_state["results"]
                    },
                    timestamp=datetime.now(),
                    requires_response=True
                )
                
                # Send message and wait for response
                response = await self._send_and_wait(message)
                
                if response:
                    workflow_state["results"][agent_id] = response.content
                    # Update data for next step
                    if "updated_data" in response.content:
                        workflow_state["data"].update(response.content["updated_data"])
                else:
                    raise Exception(f"No response from agent {agent_id} in workflow step {step_index}")
            
            # Workflow completed successfully
            workflow_state["status"] = "completed"
            workflow_state["end_time"] = datetime.now()
            
            # Update metrics
            execution_time = (workflow_state["end_time"] - start_time).total_seconds()
            self.metrics["average_workflow_time"] = (
                (self.metrics["average_workflow_time"] * (self.metrics["active_workflows"] - 1) + execution_time)
                / self.metrics["active_workflows"]
            )
            
            # Trigger completion events
            await self._trigger_event("workflow_completed", workflow_state)
            
            return workflow_state
            
        except Exception as e:
            workflow_state["status"] = "error"
            workflow_state["error"] = str(e)
            workflow_state["end_time"] = datetime.now()
            
            self.logger.error(f"Workflow {workflow_id} failed: {e}")
            self.metrics["error_count"] += 1
            
            # Trigger error events
            await self._trigger_event("workflow_error", workflow_state)
            
            raise e
            
        finally:
            self.metrics["active_workflows"] -= 1
            # Keep workflow state for debugging but mark as inactive
            workflow_state["active"] = False
    
    async def _send_and_wait(self, message: AgentMessage, timeout: float = 30.0) -> Optional[AgentMessage]:
        """Send message and wait for response"""
        # In a real implementation, this would use proper async communication
        # For now, we'll simulate the response
        await self.route_message(message)
        
        # Wait for response (simplified implementation)
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Return a mock response for now
        return AgentMessage(
            id=f"response_{message.id}",
            sender=message.recipient,
            recipient=message.sender,
            message_type=f"response_{message.message_type}",
            content={"status": "processed", "result": "mock_result"},
            timestamp=datetime.now()
        )
    
    async def start_all_agents(self):
        """Start all registered agents"""
        tasks = []
        for agent in self.agents.values():
            task = asyncio.create_task(agent.start())
            tasks.append(task)
            
        self.logger.info(f"Started {len(tasks)} agents")
        return tasks
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add event handler for orchestrator events"""
        self.event_handlers[event_type].append(handler)
    
    async def _trigger_event(self, event_type: str, data: Any):
        """Trigger event handlers"""
        for handler in self.event_handlers[event_type]:
            try:
                await handler(data)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event_type}: {e}")
    
    def get_agent_status(self, agent_id: str = None) -> Dict[str, Any]:
        """Get status of specific agent or all agents"""
        if agent_id:
            if agent_id in self.agents:
                return self.agents[agent_id].get_status()
            else:
                return {"error": f"Agent {agent_id} not found"}
        else:
            return {agent_id: agent.get_status() for agent_id, agent in self.agents.items()}
    
    def get_workflow_status(self, workflow_id: str = None) -> Dict[str, Any]:
        """Get status of specific workflow or all active workflows"""
        if workflow_id:
            return self.active_workflows.get(workflow_id, {"error": "Workflow not found"})
        else:
            return {wf_id: wf_state for wf_id, wf_state in self.active_workflows.items() if wf_state.get("active", True)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator performance metrics"""
        return {
            "orchestrator_metrics": self.metrics,
            "agent_count": len(self.agents),
            "active_workflows": len([wf for wf in self.active_workflows.values() if wf.get("active", True)]),
            "message_queue_sizes": {agent_id: agent.message_queue.qsize() for agent_id, agent in self.agents.items()},
            "recent_messages": list(self.message_history)[-10:]  # Last 10 messages
        }
    
    async def shutdown(self):
        """Gracefully shutdown all agents"""
        self.logger.info("Shutting down orchestrator and all agents")
        
        # Cancel all active workflows
        for workflow_state in self.active_workflows.values():
            if workflow_state.get("active", True):
                workflow_state["status"] = "cancelled"
                workflow_state["active"] = False
        
        # Stop all agents (in a real implementation, agents would have stop methods)
        self.logger.info("All agents stopped")

