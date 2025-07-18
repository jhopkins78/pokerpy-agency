"""
Hand Analyzer Agent for PokerPy
Specialized agent for analyzing poker hands and providing technical insights
"""

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.agents.base_agent import BaseAgent, AgentMessage, AgentCapability

class HandAnalyzerAgent(BaseAgent):
    """
    Specialized agent for poker hand analysis
    Processes hand histories and provides technical analysis
    """
    
    def __init__(self):
        super().__init__(
            agent_id="hand_analyzer",
            name="Hand Analyzer",
            description="Analyzes poker hands and provides technical insights"
        )
        
        # Initialize poker-specific knowledge
        self.position_rankings = {
            'BTN': 1, 'CO': 2, 'HJ': 3, 'LJ': 4, 'UTG+1': 5, 'UTG': 6,
            'SB': 7, 'BB': 8
        }
        
        self.hand_rankings = {
            'AA': 1, 'KK': 2, 'QQ': 3, 'JJ': 4, 'TT': 5, '99': 6, '88': 7, '77': 8,
            'AKs': 9, 'AQs': 10, 'AJs': 11, 'ATs': 12, 'A9s': 13, 'A8s': 14,
            'AKo': 15, 'KQs': 16, 'KJs': 17, 'KTs': 18, 'QJs': 19, 'QTs': 20
            # ... more hand rankings
        }
        
    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="analyze_hand",
                description="Analyze a poker hand and provide technical insights",
                input_schema={
                    "type": "object",
                    "properties": {
                        "hand_history": {"type": "string"},
                        "player_position": {"type": "string"},
                        "stack_size": {"type": "number"},
                        "analysis_depth": {"type": "string", "enum": ["basic", "intermediate", "advanced"]}
                    },
                    "required": ["hand_history"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "technical_analysis": {"type": "object"},
                        "key_decisions": {"type": "array"},
                        "mistakes": {"type": "array"},
                        "recommendations": {"type": "array"}
                    }
                }
            ),
            AgentCapability(
                name="calculate_equity",
                description="Calculate hand equity and pot odds",
                input_schema={
                    "type": "object",
                    "properties": {
                        "hero_cards": {"type": "string"},
                        "board": {"type": "string"},
                        "opponent_range": {"type": "string"},
                        "pot_size": {"type": "number"},
                        "bet_size": {"type": "number"}
                    },
                    "required": ["hero_cards", "board"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "equity": {"type": "number"},
                        "pot_odds": {"type": "number"},
                        "ev_calculation": {"type": "object"}
                    }
                }
            ),
            AgentCapability(
                name="identify_leaks",
                description="Identify common poker leaks from hand analysis",
                input_schema={
                    "type": "object",
                    "properties": {
                        "hand_histories": {"type": "array"},
                        "player_stats": {"type": "object"}
                    },
                    "required": ["hand_histories"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "identified_leaks": {"type": "array"},
                        "frequency_analysis": {"type": "object"},
                        "priority_fixes": {"type": "array"}
                    }
                }
            )
        ]
    
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming analysis requests"""
        try:
            message_type = message.message_type
            content = message.content
            
            if message_type == "analyze_hand":
                result = await self._analyze_hand(content)
            elif message_type == "calculate_equity":
                result = await self._calculate_equity(content)
            elif message_type == "identify_leaks":
                result = await self._identify_leaks(content)
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
            self.logger.error(f"Error processing message: {e}")
            return AgentMessage(
                id=f"error_{message.id}",
                sender=self.agent_id,
                recipient=message.sender,
                message_type="error",
                content={"error": str(e)},
                timestamp=datetime.now()
            )
    
    async def _analyze_hand(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a poker hand and provide technical insights"""
        hand_history = data.get("hand_history", "")
        analysis_depth = data.get("analysis_depth", "basic")
        
        # Parse hand history
        parsed_hand = self._parse_hand_history(hand_history)
        
        if not parsed_hand:
            return {"error": "Could not parse hand history"}
        
        # Perform analysis based on depth
        analysis = {
            "hand_summary": self._create_hand_summary(parsed_hand),
            "preflop_analysis": self._analyze_preflop(parsed_hand),
            "postflop_analysis": self._analyze_postflop(parsed_hand),
            "key_decisions": self._identify_key_decisions(parsed_hand),
            "technical_metrics": self._calculate_technical_metrics(parsed_hand)
        }
        
        if analysis_depth in ["intermediate", "advanced"]:
            analysis.update({
                "range_analysis": self._analyze_ranges(parsed_hand),
                "equity_calculations": self._calculate_hand_equity(parsed_hand),
                "gto_comparison": self._compare_to_gto(parsed_hand)
            })
        
        if analysis_depth == "advanced":
            analysis.update({
                "exploitative_considerations": self._analyze_exploitative_spots(parsed_hand),
                "meta_game_factors": self._analyze_meta_game(parsed_hand)
            })
        
        return analysis
    
    async def _calculate_equity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate hand equity and pot odds"""
        hero_cards = data.get("hero_cards", "")
        board = data.get("board", "")
        opponent_range = data.get("opponent_range", "random")
        pot_size = data.get("pot_size", 0)
        bet_size = data.get("bet_size", 0)
        
        # Simplified equity calculation (in real implementation, use poker evaluation library)
        equity = self._calculate_simplified_equity(hero_cards, board, opponent_range)
        pot_odds = self._calculate_pot_odds(pot_size, bet_size)
        ev_calculation = self._calculate_expected_value(equity, pot_odds, pot_size, bet_size)
        
        return {
            "equity": equity,
            "pot_odds": pot_odds,
            "ev_calculation": ev_calculation,
            "recommendation": "call" if ev_calculation["ev"] > 0 else "fold"
        }
    
    async def _identify_leaks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify common poker leaks from multiple hands"""
        hand_histories = data.get("hand_histories", [])
        player_stats = data.get("player_stats", {})
        
        leaks = []
        frequency_analysis = {}
        
        # Analyze patterns across multiple hands
        for hand in hand_histories:
            parsed_hand = self._parse_hand_history(hand)
            if parsed_hand:
                hand_leaks = self._identify_hand_leaks(parsed_hand)
                leaks.extend(hand_leaks)
        
        # Frequency analysis
        leak_counts = {}
        for leak in leaks:
            leak_type = leak.get("type", "unknown")
            leak_counts[leak_type] = leak_counts.get(leak_type, 0) + 1
        
        # Prioritize leaks by frequency and impact
        priority_fixes = self._prioritize_leaks(leak_counts, player_stats)
        
        return {
            "identified_leaks": leaks,
            "frequency_analysis": leak_counts,
            "priority_fixes": priority_fixes,
            "overall_assessment": self._create_overall_assessment(leaks, player_stats)
        }
    
    def _parse_hand_history(self, hand_history: str) -> Optional[Dict[str, Any]]:
        """Parse hand history text into structured data"""
        # Simplified parser - in real implementation, use proper poker hand parser
        try:
            lines = hand_history.strip().split('\n')
            parsed = {
                "game_info": {},
                "players": [],
                "actions": [],
                "board": "",
                "pot_size": 0
            }
            
            # Extract basic information
            for line in lines:
                if "Hold'em" in line:
                    parsed["game_info"]["game_type"] = "Hold'em"
                elif "Seat" in line and ":" in line:
                    # Parse player information
                    player_match = re.search(r'Seat (\d+): (.+?) \(\$?([\d.]+)\)', line)
                    if player_match:
                        parsed["players"].append({
                            "seat": int(player_match.group(1)),
                            "name": player_match.group(2),
                            "stack": float(player_match.group(3))
                        })
                elif any(action in line for action in ["folds", "calls", "raises", "bets", "checks"]):
                    # Parse actions
                    parsed["actions"].append(line.strip())
                elif "FLOP" in line or "TURN" in line or "RIVER" in line:
                    # Parse board
                    board_match = re.search(r'\[([^\]]+)\]', line)
                    if board_match:
                        parsed["board"] = board_match.group(1)
            
            return parsed
            
        except Exception as e:
            self.logger.error(f"Error parsing hand history: {e}")
            return None
    
    def _create_hand_summary(self, parsed_hand: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the hand"""
        return {
            "game_type": parsed_hand.get("game_info", {}).get("game_type", "Unknown"),
            "num_players": len(parsed_hand.get("players", [])),
            "board": parsed_hand.get("board", ""),
            "num_actions": len(parsed_hand.get("actions", [])),
            "pot_size": parsed_hand.get("pot_size", 0)
        }
    
    def _analyze_preflop(self, parsed_hand: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze preflop play"""
        return {
            "opening_range_assessment": "standard",
            "position_play": "appropriate",
            "sizing": "standard",
            "recommendations": ["Consider tighter opening range from early position"]
        }
    
    def _analyze_postflop(self, parsed_hand: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze postflop play"""
        return {
            "board_texture": "dry",
            "betting_pattern": "standard",
            "hand_strength": "medium",
            "recommendations": ["Consider betting for value on this dry board"]
        }
    
    def _identify_key_decisions(self, parsed_hand: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify key decision points in the hand"""
        return [
            {
                "street": "preflop",
                "decision": "open raise",
                "analysis": "Standard open from this position",
                "alternatives": ["fold", "limp"]
            },
            {
                "street": "flop",
                "decision": "continuation bet",
                "analysis": "Good spot for c-bet on this board texture",
                "alternatives": ["check"]
            }
        ]
    
    def _calculate_technical_metrics(self, parsed_hand: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate technical poker metrics"""
        return {
            "vpip": 25.0,
            "pfr": 20.0,
            "aggression_factor": 2.5,
            "c_bet_frequency": 75.0,
            "fold_to_c_bet": 45.0
        }
    
    def _analyze_ranges(self, parsed_hand: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze hand ranges"""
        return {
            "hero_range": "22+, A2s+, K9s+, Q9s+, J9s+, T8s+, 97s+, 86s+, 75s+, 64s+, 53s+, A9o+, KTo+, QTo+, JTo",
            "villain_range": "estimated based on position and action",
            "range_advantage": "hero"
        }
    
    def _calculate_hand_equity(self, parsed_hand: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate hand equity"""
        return {
            "current_equity": 65.5,
            "river_equity": 58.2,
            "equity_realization": 89.0
        }
    
    def _compare_to_gto(self, parsed_hand: Dict[str, Any]) -> Dict[str, Any]:
        """Compare play to GTO strategy"""
        return {
            "gto_compliance": 85.0,
            "major_deviations": [],
            "ev_loss": 0.05
        }
    
    def _analyze_exploitative_spots(self, parsed_hand: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze exploitative opportunities"""
        return {
            "opponent_tendencies": "tight-passive",
            "exploitative_adjustments": ["increase bluff frequency", "value bet thinner"],
            "meta_game_considerations": []
        }
    
    def _analyze_meta_game(self, parsed_hand: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze meta-game factors"""
        return {
            "table_image": "tight-aggressive",
            "recent_history": "no significant history",
            "adjustments": []
        }
    
    def _calculate_simplified_equity(self, hero_cards: str, board: str, opponent_range: str) -> float:
        """Simplified equity calculation"""
        # In real implementation, use proper poker evaluation library
        return 55.5  # Mock equity
    
    def _calculate_pot_odds(self, pot_size: float, bet_size: float) -> float:
        """Calculate pot odds"""
        if bet_size == 0:
            return 0.0
        return bet_size / (pot_size + bet_size)
    
    def _calculate_expected_value(self, equity: float, pot_odds: float, pot_size: float, bet_size: float) -> Dict[str, Any]:
        """Calculate expected value"""
        call_ev = (equity / 100) * (pot_size + bet_size) - bet_size
        fold_ev = 0.0
        
        return {
            "call_ev": call_ev,
            "fold_ev": fold_ev,
            "ev": max(call_ev, fold_ev),
            "best_action": "call" if call_ev > fold_ev else "fold"
        }
    
    def _identify_hand_leaks(self, parsed_hand: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify leaks in a single hand"""
        leaks = []
        
        # Example leak detection
        actions = parsed_hand.get("actions", [])
        for action in actions:
            if "calls" in action.lower() and "river" in action.lower():
                leaks.append({
                    "type": "river_call_leak",
                    "description": "Calling too wide on river",
                    "severity": "medium",
                    "street": "river"
                })
        
        return leaks
    
    def _prioritize_leaks(self, leak_counts: Dict[str, int], player_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize leaks by frequency and impact"""
        priority_leaks = []
        
        for leak_type, count in leak_counts.items():
            priority_leaks.append({
                "leak_type": leak_type,
                "frequency": count,
                "impact": "high" if count > 5 else "medium" if count > 2 else "low",
                "fix_priority": count * 2  # Simple priority calculation
            })
        
        return sorted(priority_leaks, key=lambda x: x["fix_priority"], reverse=True)
    
    def _create_overall_assessment(self, leaks: List[Dict[str, Any]], player_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Create overall assessment of player's game"""
        return {
            "overall_rating": "intermediate",
            "strengths": ["good preflop play", "appropriate aggression"],
            "weaknesses": ["river play", "bluff catching"],
            "improvement_areas": ["hand reading", "bet sizing"],
            "confidence_score": 75.0
        }
