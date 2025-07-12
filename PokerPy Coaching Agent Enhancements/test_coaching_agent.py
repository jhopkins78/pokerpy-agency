import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from coaching_agent import PokerCoachingAgent, CoachingResponse
from memory_manager import MemoryManager
from rag_system import RAGSystem

class TestPokerCoachingAgent:
    
    @pytest.fixture
    def mock_rag_system(self):
        rag = Mock(spec=RAGSystem)
        rag.search.return_value = [
            {
                "content": "Position is crucial in poker. Play tighter from early position.",
                "category": "poker_strategy",
                "relevance_score": 0.9
            }
        ]
        return rag
    
    @pytest.fixture
    def mock_memory_manager(self):
        memory = Mock(spec=MemoryManager)
        memory.get_user_profile.return_value = {
            "user_id": "test_user",
            "skill_level": "intermediate",
            "psychological_profile": {
                "risk_tolerance": "medium",
                "emotional_regulation": "good",
                "learning_style": "analytical"
            },
            "preferences": {
                "coaching_style": "supportive"
            }
        }
        memory.get_recent_conversations.return_value = []
        return memory
    
    @pytest.fixture
    def coaching_agent(self, mock_rag_system, mock_memory_manager):
        return PokerCoachingAgent(mock_rag_system, mock_memory_manager)
    
    def test_coaching_agent_initialization(self, coaching_agent):
        """Test that coaching agent initializes properly"""
        assert coaching_agent.rag_system is not None
        assert coaching_agent.memory_manager is not None
        assert len(coaching_agent.coaching_styles) > 0
        assert len(coaching_agent.profiling_questions) > 0
    
    def test_determine_coaching_style(self, coaching_agent):
        """Test coaching style determination logic"""
        # Test supportive style for poor performance
        user_profile = {"psychological_profile": {}}
        context = {"recent_performance": "poor", "emotional_state": "frustrated"}
        
        style = coaching_agent._determine_coaching_style(user_profile, context)
        assert style == "supportive"
        
        # Test analytical style for analytical learners
        user_profile = {"psychological_profile": {"learning_style": "analytical"}}
        context = {}
        
        style = coaching_agent._determine_coaching_style(user_profile, context)
        assert style == "analytical"
    
    def test_build_system_prompt(self, coaching_agent):
        """Test system prompt building"""
        user_profile = {"skill_level": "beginner"}
        knowledge_context = [{"content": "Test knowledge"}]
        
        prompt = coaching_agent._build_system_prompt("supportive", user_profile, knowledge_context)
        
        assert "supportive" in prompt
        assert "poker coach" in prompt.lower()
        assert "Test knowledge" in prompt
    
    def test_parse_response(self, coaching_agent):
        """Test response parsing"""
        response_text = """This is a coaching response about position play.
        
        Suggestion: Practice playing tighter from early position
        Suggestion: Study position-based hand charts
        
        What specific positions do you find most challenging?
        How comfortable are you with late position play?"""
        
        parsed = coaching_agent._parse_response(response_text)
        
        assert isinstance(parsed, CoachingResponse)
        assert len(parsed.suggestions) > 0
        assert len(parsed.follow_up_questions) > 0
        assert parsed.emotional_tone == "supportive"
    
    def test_extract_psychological_insights(self, coaching_agent):
        """Test psychological insight extraction"""
        # Test risk tolerance detection
        message = "I'm always scared to make big bets, even with strong hands"
        insights = coaching_agent._extract_psychological_insights(message)
        assert insights.get("risk_tolerance") == "low"
        
        # Test emotional regulation detection
        message = "I went on tilt and lost my entire stack after a bad beat"
        insights = coaching_agent._extract_psychological_insights(message)
        assert insights.get("emotional_regulation") == "needs_work"
        
        # Test learning style detection
        message = "I love studying GTO charts and analyzing hand ranges"
        insights = coaching_agent._extract_psychological_insights(message)
        assert insights.get("learning_style") == "analytical"
    
    @patch('openai.OpenAI')
    def test_generate_response(self, mock_openai, coaching_agent):
        """Test response generation"""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Great question about position! Playing tight from early position is crucial because you have many players left to act behind you."
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        coaching_agent.client = mock_client
        
        response = coaching_agent.generate_response(
            user_id="test_user",
            message="How should I play from early position?",
            context={}
        )
        
        assert "message" in response
        assert "context" in response
        assert "suggestions" in response
        assert isinstance(response["suggestions"], list)
    
    @patch('openai.OpenAI')
    def test_generate_daily_insight(self, mock_openai, coaching_agent):
        """Test daily insight generation"""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Today's focus: Remember that every decision is an opportunity to improve. Focus on the process, not the outcome."
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        coaching_agent.client = mock_client
        
        insight = coaching_agent.generate_daily_insight("test_user")
        
        assert "insight" in insight
        assert "date" in insight
        assert "category" in insight
        assert insight["category"] == "daily_wisdom"
    
    @patch('openai.OpenAI')
    def test_ask_anything_mode(self, mock_openai, coaching_agent):
        """Test ask anything mode"""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Building discipline is like building a strong poker foundation. Start with small, consistent actions and gradually increase the challenge."
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        coaching_agent.client = mock_client
        
        response = coaching_agent.ask_anything_mode(
            user_id="test_user",
            question="How can I build more discipline in my daily life?",
            category="personal_development"
        )
        
        assert "response" in response
        assert "category" in response
        assert "timestamp" in response
        assert response["category"] == "personal_development"
    
    def test_generate_profiling_question(self, coaching_agent):
        """Test profiling question generation"""
        question = coaching_agent.generate_profiling_question("test_user", "risk_tolerance")
        
        assert isinstance(question, str)
        assert len(question) > 0
        assert "?" in question
    
    def test_coaching_styles_coverage(self, coaching_agent):
        """Test that all coaching styles are properly defined"""
        expected_styles = ["supportive", "analytical", "motivational", "philosophical", "practical"]
        
        for style in expected_styles:
            assert style in coaching_agent.coaching_styles
            assert len(coaching_agent.coaching_styles[style]) > 0
    
    def test_profiling_questions_coverage(self, coaching_agent):
        """Test that profiling questions cover all categories"""
        expected_categories = ["risk_tolerance", "emotional_regulation", "learning_style", "goals_motivation"]
        
        for category in expected_categories:
            assert category in coaching_agent.profiling_questions
            assert len(coaching_agent.profiling_questions[category]) > 0
            
            # Ensure all questions are actually questions
            for question in coaching_agent.profiling_questions[category]:
                assert isinstance(question, str)
                assert len(question) > 0

if __name__ == "__main__":
    pytest.main([__file__])

