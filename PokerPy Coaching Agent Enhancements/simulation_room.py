import random
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class Card:
    suit: str  # 'hearts', 'diamonds', 'clubs', 'spades'
    rank: str  # '2', '3', ..., 'K', 'A'
    
    def __str__(self):
        return f"{self.rank}{self.suit[0].upper()}"

@dataclass
class Player:
    id: str
    name: str
    stack: int
    position: str
    hole_cards: List[Card]
    is_active: bool = True
    is_all_in: bool = False
    current_bet: int = 0

@dataclass
class GameState:
    pot: int
    community_cards: List[Card]
    current_bet: int
    players: List[Player]
    active_player: int
    street: str  # 'preflop', 'flop', 'turn', 'river'
    small_blind: int
    big_blind: int

@dataclass
class SimulationScenario:
    id: str
    name: str
    description: str
    difficulty: str
    scenario_type: str
    initial_state: GameState
    learning_objectives: List[str]
    success_criteria: Dict

class SimulationRoom:
    def __init__(self, coaching_agent):
        self.coaching_agent = coaching_agent
        self.active_simulations = {}
        self.scenario_templates = self._initialize_scenarios()
        
    def _initialize_scenarios(self) -> Dict[str, Dict]:
        """Initialize predefined simulation scenarios"""
        return {
            "cash_game_basic": {
                "name": "Basic Cash Game Decision",
                "description": "Practice fundamental cash game decisions in common spots",
                "difficulty": "beginner",
                "learning_objectives": [
                    "Position awareness",
                    "Basic hand selection",
                    "Pot odds calculation",
                    "Betting for value"
                ]
            },
            "tournament_bubble": {
                "name": "Tournament Bubble Play",
                "description": "Navigate bubble situations with ICM considerations",
                "difficulty": "advanced",
                "learning_objectives": [
                    "ICM understanding",
                    "Risk assessment",
                    "Survival vs accumulation",
                    "Pressure spots"
                ]
            },
            "bluff_spot": {
                "name": "Bluffing Opportunity",
                "description": "Identify and execute profitable bluffs",
                "difficulty": "intermediate",
                "learning_objectives": [
                    "Board texture analysis",
                    "Opponent range assessment",
                    "Bluff sizing",
                    "Story consistency"
                ]
            },
            "tilt_control": {
                "name": "Tilt Management",
                "description": "Practice emotional control after bad beats",
                "difficulty": "intermediate",
                "learning_objectives": [
                    "Emotional regulation",
                    "Decision quality under stress",
                    "Bankroll protection",
                    "Mental reset techniques"
                ]
            },
            "multi_way_pot": {
                "name": "Multi-way Pot Navigation",
                "description": "Handle complex multi-player situations",
                "difficulty": "advanced",
                "learning_objectives": [
                    "Range interaction",
                    "Protection vs value",
                    "Position dynamics",
                    "Pot control"
                ]
            }
        }
    
    def create_simulation(self, user_id: str, scenario_type: str, difficulty: str, custom_params: Dict = None) -> Dict:
        """Create a new simulation scenario"""
        try:
            simulation_id = str(uuid.uuid4())
            
            # Get scenario template
            if scenario_type in self.scenario_templates:
                template = self.scenario_templates[scenario_type]
            else:
                template = self.scenario_templates["cash_game_basic"]
            
            # Generate initial game state
            initial_state = self._generate_game_state(scenario_type, difficulty, custom_params)
            
            # Create scenario
            scenario = SimulationScenario(
                id=simulation_id,
                name=template["name"],
                description=template["description"],
                difficulty=difficulty,
                scenario_type=scenario_type,
                initial_state=initial_state,
                learning_objectives=template["learning_objectives"],
                success_criteria=self._generate_success_criteria(scenario_type, difficulty)
            )
            
            # Store simulation
            self.active_simulations[simulation_id] = {
                "scenario": scenario,
                "current_state": initial_state,
                "history": [],
                "user_id": user_id,
                "created_at": datetime.now(),
                "completed": False
            }
            
            # Generate coaching instructions
            instructions = self._generate_instructions(scenario)
            
            return {
                "id": simulation_id,
                "scenario": {
                    "name": scenario.name,
                    "description": scenario.description,
                    "difficulty": scenario.difficulty,
                    "learning_objectives": scenario.learning_objectives
                },
                "instructions": instructions,
                "state": self._serialize_game_state(initial_state)
            }
            
        except Exception as e:
            logger.error(f"Error creating simulation: {str(e)}")
            raise
    
    def _generate_game_state(self, scenario_type: str, difficulty: str, custom_params: Dict = None) -> GameState:
        """Generate initial game state for scenario"""
        # Create deck
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        deck = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(deck)
        
        # Default parameters
        params = {
            "num_players": 6,
            "small_blind": 1,
            "big_blind": 2,
            "starting_stack": 200,
            "street": "preflop"
        }
        
        if custom_params:
            params.update(custom_params)
        
        # Create players
        positions = ["UTG", "MP", "CO", "BTN", "SB", "BB"]
        players = []
        
        for i in range(params["num_players"]):
            # Deal hole cards
            hole_cards = [deck.pop(), deck.pop()]
            
            player = Player(
                id=f"player_{i}",
                name=f"Player {i+1}" if i > 0 else "You",
                stack=params["starting_stack"],
                position=positions[i] if i < len(positions) else f"Player{i+1}",
                hole_cards=hole_cards if i == 0 else [],  # Only show user's cards
                is_active=True,
                current_bet=params["small_blind"] if i == params["num_players"]-2 else (params["big_blind"] if i == params["num_players"]-1 else 0)
            )
            players.append(player)
        
        # Deal community cards based on street
        community_cards = []
        if params["street"] in ["flop", "turn", "river"]:
            community_cards.extend([deck.pop(), deck.pop(), deck.pop()])  # Flop
        if params["street"] in ["turn", "river"]:
            community_cards.append(deck.pop())  # Turn
        if params["street"] == "river":
            community_cards.append(deck.pop())  # River
        
        # Calculate initial pot
        pot = sum(player.current_bet for player in players)
        
        return GameState(
            pot=pot,
            community_cards=community_cards,
            current_bet=max(player.current_bet for player in players),
            players=players,
            active_player=0,  # User is always first to act in simulations
            street=params["street"],
            small_blind=params["small_blind"],
            big_blind=params["big_blind"]
        )
    
    def _generate_success_criteria(self, scenario_type: str, difficulty: str) -> Dict:
        """Generate success criteria for the scenario"""
        base_criteria = {
            "decision_quality": 0.7,  # Minimum decision quality score
            "learning_objectives_met": 0.8,  # Percentage of objectives demonstrated
            "time_efficiency": 300  # Maximum time in seconds
        }
        
        if scenario_type == "tournament_bubble":
            base_criteria.update({
                "icm_awareness": 0.8,
                "survival_priority": True
            })
        elif scenario_type == "bluff_spot":
            base_criteria.update({
                "bluff_frequency": 0.3,
                "story_consistency": 0.8
            })
        elif scenario_type == "tilt_control":
            base_criteria.update({
                "emotional_stability": 0.9,
                "decision_consistency": 0.8
            })
        
        return base_criteria
    
    def _generate_instructions(self, scenario: SimulationScenario) -> str:
        """Generate coaching instructions for the scenario"""
        instructions = f"""
        Welcome to the {scenario.name} simulation!
        
        {scenario.description}
        
        Learning Objectives:
        {chr(10).join(f"• {obj}" for obj in scenario.learning_objectives)}
        
        Your goal is to make the best decision in this spot while demonstrating understanding of the key concepts.
        
        Take your time to analyze:
        - Your position and stack size
        - Opponent tendencies and ranges
        - Pot odds and equity
        - The overall game situation
        
        Remember: Focus on the decision-making process, not just the outcome.
        """
        
        return instructions.strip()
    
    def process_action(self, simulation_id: str, action: str, parameters: Dict = None) -> Dict:
        """Process a player action in the simulation"""
        try:
            if simulation_id not in self.active_simulations:
                raise ValueError("Simulation not found")
            
            simulation = self.active_simulations[simulation_id]
            current_state = simulation["current_state"]
            
            # Validate action
            valid_actions = self._get_valid_actions(current_state)
            if action not in valid_actions:
                return {
                    "error": f"Invalid action. Valid actions: {valid_actions}",
                    "state": self._serialize_game_state(current_state)
                }
            
            # Process the action
            result = self._execute_action(current_state, action, parameters or {})
            
            # Update simulation history
            simulation["history"].append({
                "action": action,
                "parameters": parameters,
                "timestamp": datetime.now(),
                "state_before": self._serialize_game_state(current_state)
            })
            
            # Generate coaching feedback
            feedback = self._generate_feedback(simulation, action, parameters, result)
            
            # Check if simulation is complete
            is_complete = self._check_completion(simulation, result)
            if is_complete:
                simulation["completed"] = True
                completion_analysis = self._generate_completion_analysis(simulation)
                result.update(completion_analysis)
            
            return {
                "result": result,
                "feedback": feedback,
                "state": self._serialize_game_state(current_state),
                "completed": is_complete,
                "valid_actions": self._get_valid_actions(current_state) if not is_complete else []
            }
            
        except Exception as e:
            logger.error(f"Error processing action: {str(e)}")
            return {"error": str(e)}
    
    def _get_valid_actions(self, state: GameState) -> List[str]:
        """Get valid actions for current game state"""
        actions = ["fold"]
        
        if state.current_bet > state.players[state.active_player].current_bet:
            actions.append("call")
        else:
            actions.append("check")
        
        # Can always raise/bet if not all-in
        if state.players[state.active_player].stack > 0:
            if state.current_bet > 0:
                actions.append("raise")
            else:
                actions.append("bet")
        
        return actions
    
    def _execute_action(self, state: GameState, action: str, parameters: Dict) -> Dict:
        """Execute the player action and update game state"""
        player = state.players[state.active_player]
        result = {"action": action, "amount": 0, "description": ""}
        
        if action == "fold":
            player.is_active = False
            result["description"] = f"{player.name} folds"
            
        elif action == "check":
            result["description"] = f"{player.name} checks"
            
        elif action == "call":
            call_amount = min(state.current_bet - player.current_bet, player.stack)
            player.current_bet += call_amount
            player.stack -= call_amount
            state.pot += call_amount
            result["amount"] = call_amount
            result["description"] = f"{player.name} calls {call_amount}"
            
        elif action in ["bet", "raise"]:
            bet_amount = parameters.get("amount", state.big_blind * 3)
            bet_amount = min(bet_amount, player.stack)
            
            if action == "raise":
                total_bet = state.current_bet + bet_amount
            else:
                total_bet = bet_amount
            
            amount_to_add = total_bet - player.current_bet
            player.current_bet = total_bet
            player.stack -= amount_to_add
            state.pot += amount_to_add
            state.current_bet = total_bet
            
            result["amount"] = total_bet
            result["description"] = f"{player.name} {action}s to {total_bet}"
        
        # Simulate opponent actions (simplified)
        self._simulate_opponent_actions(state)
        
        return result
    
    def _simulate_opponent_actions(self, state: GameState):
        """Simulate opponent actions (simplified AI)"""
        # This is a simplified simulation - in production, you'd want more sophisticated opponent modeling
        for i, player in enumerate(state.players[1:], 1):  # Skip user (index 0)
            if not player.is_active:
                continue
            
            # Simple decision logic based on random factors and position
            action_prob = random.random()
            
            if action_prob < 0.3:  # 30% fold
                player.is_active = False
            elif action_prob < 0.7:  # 40% call
                call_amount = min(state.current_bet - player.current_bet, player.stack)
                player.current_bet += call_amount
                player.stack -= call_amount
                state.pot += call_amount
            else:  # 30% raise
                raise_amount = random.randint(state.big_blind * 2, state.big_blind * 5)
                total_bet = state.current_bet + raise_amount
                amount_to_add = min(total_bet - player.current_bet, player.stack)
                player.current_bet += amount_to_add
                player.stack -= amount_to_add
                state.pot += amount_to_add
                state.current_bet = player.current_bet
    
    def _generate_feedback(self, simulation: Dict, action: str, parameters: Dict, result: Dict) -> str:
        """Generate coaching feedback for the action"""
        scenario = simulation["scenario"]
        state = simulation["current_state"]
        
        # Use coaching agent to generate personalized feedback
        feedback_prompt = f"""
        The user just took action '{action}' in a {scenario.scenario_type} simulation.
        
        Game situation:
        - Pot: {state.pot}
        - Current bet: {state.current_bet}
        - User's stack: {state.players[0].stack}
        - Position: {state.players[0].position}
        - Street: {state.street}
        
        Learning objectives: {scenario.learning_objectives}
        
        Provide brief, constructive feedback on this decision.
        """
        
        try:
            feedback_response = self.coaching_agent.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": feedback_prompt}],
                temperature=0.7,
                max_tokens=200
            )
            return feedback_response.choices[0].message.content
        except:
            return f"Good {action}! Consider the pot odds and your position for future decisions."
    
    def _check_completion(self, simulation: Dict, result: Dict) -> bool:
        """Check if simulation is complete"""
        state = simulation["current_state"]
        
        # Check if only one player is active
        active_players = sum(1 for p in state.players if p.is_active)
        if active_players <= 1:
            return True
        
        # Check if we've reached the river and all betting is complete
        if state.street == "river" and all(p.current_bet == state.current_bet or not p.is_active for p in state.players):
            return True
        
        return False
    
    def _generate_completion_analysis(self, simulation: Dict) -> Dict:
        """Generate analysis when simulation completes"""
        scenario = simulation["scenario"]
        history = simulation["history"]
        
        analysis = {
            "performance_score": random.uniform(0.6, 0.9),  # Simplified scoring
            "objectives_met": random.sample(scenario.learning_objectives, k=min(3, len(scenario.learning_objectives))),
            "key_insights": [
                "Position awareness was demonstrated well",
                "Consider pot odds more carefully in future decisions",
                "Good emotional control throughout the hand"
            ],
            "next_steps": [
                "Practice similar scenarios with different stack sizes",
                "Focus on opponent range reading",
                "Review ICM concepts for tournament play"
            ]
        }
        
        return analysis
    
    def _serialize_game_state(self, state: GameState) -> Dict:
        """Serialize game state for JSON response"""
        return {
            "pot": state.pot,
            "community_cards": [str(card) for card in state.community_cards],
            "current_bet": state.current_bet,
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "stack": p.stack,
                    "position": p.position,
                    "hole_cards": [str(card) for card in p.hole_cards] if p.id == "player_0" else ["XX", "XX"],
                    "is_active": p.is_active,
                    "current_bet": p.current_bet
                }
                for p in state.players
            ],
            "active_player": state.active_player,
            "street": state.street,
            "small_blind": state.small_blind,
            "big_blind": state.big_blind
        }
    
    def get_simulation_history(self, simulation_id: str) -> Dict:
        """Get simulation history and analysis"""
        if simulation_id not in self.active_simulations:
            return {"error": "Simulation not found"}
        
        simulation = self.active_simulations[simulation_id]
        return {
            "scenario": asdict(simulation["scenario"]),
            "history": simulation["history"],
            "completed": simulation["completed"],
            "created_at": simulation["created_at"].isoformat()
        }
    
    def get_available_scenarios(self) -> Dict:
        """Get list of available simulation scenarios"""
        return self.scenario_templates

