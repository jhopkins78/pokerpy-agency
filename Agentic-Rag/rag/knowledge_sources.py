"""
Knowledge Sources for Automatic Content Ingestion
Provides automated knowledge acquisition from various sources
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from dataclasses import dataclass
import hashlib

from .knowledge_base import KnowledgeDocument, DocumentType, SkillLevel

@dataclass
class SourceContent:
    """Represents content from a knowledge source"""
    title: str
    content: str
    source_url: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

class KnowledgeSource(ABC):
    """Abstract base class for knowledge sources"""
    
    def __init__(self, source_id: str, name: str, description: str):
        self.source_id = source_id
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"knowledge_source_{source_id}")
        self.last_update = None
        self.update_frequency = timedelta(hours=24)  # Default update frequency
        
    @abstractmethod
    async def fetch_content(self) -> List[SourceContent]:
        """Fetch content from the source"""
        pass
    
    @abstractmethod
    def process_content(self, raw_content: Any) -> List[SourceContent]:
        """Process raw content into structured format"""
        pass
    
    def should_update(self) -> bool:
        """Check if source should be updated"""
        if self.last_update is None:
            return True
        return datetime.now() - self.last_update >= self.update_frequency
    
    def create_knowledge_document(self, content: SourceContent, doc_type: DocumentType, skill_level: SkillLevel) -> KnowledgeDocument:
        """Create a knowledge document from source content"""
        return KnowledgeDocument(
            id=f"{self.source_id}_{hashlib.md5(content.title.encode()).hexdigest()[:8]}",
            title=content.title,
            content=content.content,
            document_type=doc_type,
            skill_level=skill_level,
            tags=content.tags + [self.source_id],
            metadata={
                'source_id': self.source_id,
                'source_url': content.source_url,
                'author': content.author,
                'published_date': content.published_date.isoformat() if content.published_date else None,
                **content.metadata
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
            source=self.name,
            confidence_score=0.8  # Default confidence for sourced content
        )

class PokerStrategySource(KnowledgeSource):
    """
    Source for poker strategy content
    Simulates fetching from poker strategy websites and forums
    """
    
    def __init__(self):
        super().__init__(
            source_id="poker_strategy",
            name="Poker Strategy Database",
            description="Curated poker strategy content from expert sources"
        )
        
        # Simulated strategy content database
        self.strategy_database = [
            {
                "title": "Preflop Range Construction in 6-Max Cash Games",
                "content": """Preflop range construction is fundamental to profitable poker. In 6-max cash games, position is crucial for determining opening ranges. From early position (UTG), open tight ranges of approximately 15-18% of hands, focusing on strong broadway cards, pocket pairs 77+, and suited connectors 87s+. From middle position, expand to 20-25% including more suited connectors and weaker broadway hands. In late position (CO/BTN), open 25-35% of hands, including suited one-gappers, weak aces, and small pocket pairs for set mining value.""",
                "author": "Expert Strategy Team",
                "tags": ["preflop", "ranges", "6-max", "cash-games", "position"],
                "skill_level": "intermediate",
                "published_date": datetime.now() - timedelta(days=30)
            },
            {
                "title": "Pot Odds and Equity Calculations for Beginners",
                "content": """Understanding pot odds is essential for making profitable decisions. Pot odds represent the ratio between the current pot size and the cost of your call. If the pot is $100 and you need to call $25, you're getting 4:1 pot odds, meaning you need 20% equity to break even. Use the 4-2 rule for quick equity estimation: multiply your outs by 4 on the flop or 2 on the turn to get approximate equity percentage. For example, with 8 outs on the flop, you have roughly 32% equity.""",
                "author": "Beginner Strategy Guide",
                "tags": ["pot-odds", "equity", "mathematics", "beginners", "fundamentals"],
                "skill_level": "beginner",
                "published_date": datetime.now() - timedelta(days=15)
            },
            {
                "title": "Advanced Bluffing Theory and Range Balancing",
                "content": """Effective bluffing requires understanding range construction and opponent tendencies. Your bluffing frequency should be based on pot odds you're offering opponents. When betting 2/3 pot, opponents need 28.6% equity to call, so you should bluff with hands that have less than 28.6% equity but good blockers. Balance your range by bluffing with hands that block opponent's calling range while having some equity as backup. Consider board texture, opponent type, and stack depths when constructing bluffing ranges.""",
                "author": "Advanced Strategy Analysis",
                "tags": ["bluffing", "range-balancing", "advanced", "gto", "theory"],
                "skill_level": "advanced",
                "published_date": datetime.now() - timedelta(days=7)
            },
            {
                "title": "Tournament ICM Considerations",
                "content": """Independent Chip Model (ICM) becomes crucial in tournament play, especially near bubble situations and final tables. ICM pressure affects optimal strategy by making survival more valuable than chip accumulation. In bubble situations, avoid marginal spots against similar stacks and exploit short stacks who are playing too tight. At final tables, consider pay jumps when making decisions - sometimes folding premium hands is correct when ICM pressure is extreme.""",
                "author": "Tournament Strategy Expert",
                "tags": ["tournaments", "icm", "bubble", "final-table", "strategy"],
                "skill_level": "advanced",
                "published_date": datetime.now() - timedelta(days=20)
            },
            {
                "title": "Reading Physical Tells in Live Poker",
                "content": """Physical tells can provide valuable information in live poker, but they should supplement, not replace, fundamental strategy. Common reliable tells include: sudden posture changes often indicate strength, trembling hands usually show excitement (strong hand), and covering mouth may indicate deception. However, be aware of reverse tells and focus primarily on betting patterns and timing tells, which are more reliable than physical tells.""",
                "author": "Live Poker Specialist",
                "tags": ["live-poker", "tells", "psychology", "reads", "physical"],
                "skill_level": "intermediate",
                "published_date": datetime.now() - timedelta(days=45)
            }
        ]
    
    async def fetch_content(self) -> List[SourceContent]:
        """Fetch strategy content from database"""
        try:
            content_list = []
            
            for item in self.strategy_database:
                content = SourceContent(
                    title=item["title"],
                    content=item["content"],
                    author=item["author"],
                    published_date=item["published_date"],
                    tags=item["tags"],
                    metadata={"skill_level": item["skill_level"]}
                )
                content_list.append(content)
            
            self.last_update = datetime.now()
            self.logger.info(f"Fetched {len(content_list)} strategy articles")
            return content_list
        
        except Exception as e:
            self.logger.error(f"Error fetching strategy content: {e}")
            return []
    
    def process_content(self, raw_content: Any) -> List[SourceContent]:
        """Process raw strategy content"""
        # In a real implementation, this would parse HTML, clean text, etc.
        return raw_content if isinstance(raw_content, list) else []

class HandHistorySource(KnowledgeSource):
    """
    Source for hand history analysis and learning
    Processes anonymized hand histories for educational content
    """
    
    def __init__(self):
        super().__init__(
            source_id="hand_history",
            name="Hand History Database",
            description="Analyzed hand histories for educational purposes"
        )
        
        # Simulated hand history database
        self.hand_database = [
            {
                "title": "AA vs KK Preflop All-in Analysis",
                "content": """Hand Analysis: Hero holds AA in the big blind, villain raises from UTG, hero 3-bets, villain 4-bet shoves. This is a clear call with pocket aces, as AA vs KK is approximately 81% vs 19%. The key learning point is that AA should never fold preflop in cash games, regardless of stack depth. Even against the tightest 4-bet shoving range, AA maintains significant equity.""",
                "situation": "preflop_allin",
                "stakes": "1/2",
                "tags": ["aa", "kk", "preflop", "all-in", "premium-pairs"],
                "skill_level": "beginner"
            },
            {
                "title": "Bluff Catching with Second Pair",
                "content": """Hand Analysis: Hero calls with 77 on A♠7♣2♦ flop, turn brings K♠, villain bets large on 5♠ river. With second pair, hero must consider villain's range and bluffing frequency. Given the board texture and betting pattern, villain likely has some bluffs with missed draws. The pot odds of 3:1 require 25% equity, and second pair likely has this against a balanced range including bluffs.""",
                "situation": "bluff_catch",
                "stakes": "2/5",
                "tags": ["bluff-catching", "second-pair", "river-decision", "pot-odds"],
                "skill_level": "intermediate"
            },
            {
                "title": "Multi-way Pot with Drawing Hand",
                "content": """Hand Analysis: Hero holds 9♠8♠ in a 4-way pot on J♠7♣6♦ flop. With an open-ended straight draw and backdoor flush draw, hero has approximately 13 outs (8 for straight, 9 for flush minus overlaps). In multi-way pots, drawing hands gain value due to better pot odds and implied odds. The correct play is to call and see the turn, as folding would be too tight given the pot odds.""",
                "situation": "multiway_draw",
                "stakes": "1/3",
                "tags": ["drawing-hands", "multiway", "pot-odds", "implied-odds"],
                "skill_level": "intermediate"
            }
        ]
    
    async def fetch_content(self) -> List[SourceContent]:
        """Fetch hand history content"""
        try:
            content_list = []
            
            for hand in self.hand_database:
                content = SourceContent(
                    title=hand["title"],
                    content=hand["content"],
                    tags=hand["tags"],
                    metadata={
                        "situation": hand["situation"],
                        "stakes": hand["stakes"],
                        "skill_level": hand["skill_level"]
                    }
                )
                content_list.append(content)
            
            self.last_update = datetime.now()
            self.logger.info(f"Fetched {len(content_list)} hand histories")
            return content_list
        
        except Exception as e:
            self.logger.error(f"Error fetching hand histories: {e}")
            return []
    
    def process_content(self, raw_content: Any) -> List[SourceContent]:
        """Process hand history content"""
        return raw_content if isinstance(raw_content, list) else []

class CommunityContentSource(KnowledgeSource):
    """
    Source for community-generated content
    Processes forum posts, Q&A, and user discussions
    """
    
    def __init__(self):
        super().__init__(
            source_id="community",
            name="Community Content",
            description="High-quality community discussions and Q&A"
        )
        
        # Simulated community content
        self.community_database = [
            {
                "title": "How to Handle Tilt and Emotional Control",
                "content": """Community Discussion: Managing tilt is crucial for long-term success. When you feel emotions rising, take a break immediately. Implement a stop-loss rule - if you lose 3 buy-ins, quit for the day. Practice mindfulness and breathing exercises between hands. Remember that variance is part of poker, and short-term results don't reflect your skill level. Focus on making good decisions rather than results.""",
                "author": "CommunityModerator",
                "upvotes": 45,
                "tags": ["tilt", "psychology", "mental-game", "emotional-control"],
                "skill_level": "all_levels"
            },
            {
                "title": "Bankroll Management for Micro Stakes",
                "content": """Community Q&A: For micro stakes cash games, maintain 25-30 buy-ins for your current level. This provides sufficient cushion for variance while allowing for growth. Don't move up until you have proper bankroll for the next level. Track your results and move down if your bankroll drops below 20 buy-ins. Discipline in bankroll management is more important than poker skill for long-term success.""",
                "author": "MicroStakesExpert",
                "upvotes": 32,
                "tags": ["bankroll", "micro-stakes", "management", "variance"],
                "skill_level": "beginner"
            },
            {
                "title": "Transitioning from Cash Games to Tournaments",
                "content": """Community Discussion: Tournament strategy differs significantly from cash games. In tournaments, consider ICM pressure, changing stack depths, and blind levels. Early stages play similar to cash games with deep stacks. Middle stages require tighter play as blinds increase. Late stages and bubble play require understanding of ICM and survival considerations. Practice different tournament phases separately.""",
                "author": "TournamentPro",
                "upvotes": 28,
                "tags": ["tournaments", "cash-games", "transition", "icm", "strategy"],
                "skill_level": "intermediate"
            }
        ]
    
    async def fetch_content(self) -> List[SourceContent]:
        """Fetch community content"""
        try:
            content_list = []
            
            for post in self.community_database:
                content = SourceContent(
                    title=post["title"],
                    content=post["content"],
                    author=post["author"],
                    tags=post["tags"],
                    metadata={
                        "upvotes": post["upvotes"],
                        "skill_level": post["skill_level"],
                        "content_type": "community_post"
                    }
                )
                content_list.append(content)
            
            self.last_update = datetime.now()
            self.logger.info(f"Fetched {len(content_list)} community posts")
            return content_list
        
        except Exception as e:
            self.logger.error(f"Error fetching community content: {e}")
            return []
    
    def process_content(self, raw_content: Any) -> List[SourceContent]:
        """Process community content"""
        return raw_content if isinstance(raw_content, list) else []

class LearningMaterialSource(KnowledgeSource):
    """
    Source for structured learning materials
    Provides tutorials, lessons, and educational content
    """
    
    def __init__(self):
        super().__init__(
            source_id="learning",
            name="Learning Materials",
            description="Structured tutorials and educational content"
        )
        
        # Simulated learning materials
        self.learning_database = [
            {
                "title": "Poker Fundamentals: Starting Hand Selection",
                "content": """Lesson 1: Starting hand selection is the foundation of profitable poker. Learn to categorize hands into groups: Premium hands (AA, KK, QQ, AK), Strong hands (JJ, TT, AQ, AJ), Playable hands (99-22, suited connectors, suited aces), and Marginal hands (offsuit connectors, weak aces). Position determines which groups to play. In early position, stick to premium and strong hands. In late position, expand to include playable and some marginal hands.""",
                "lesson_number": 1,
                "module": "fundamentals",
                "tags": ["fundamentals", "starting-hands", "position", "hand-selection"],
                "skill_level": "beginner",
                "prerequisites": []
            },
            {
                "title": "Intermediate Concepts: Continuation Betting",
                "content": """Lesson 5: Continuation betting (c-betting) is betting on the flop after raising preflop. C-bet frequency should depend on board texture, opponent type, and position. On dry boards (A♠K♣7♦), c-bet frequently as you have range advantage. On wet boards (9♠8♠7♣), c-bet more selectively. Against calling stations, c-bet for value with strong hands. Against tight players, c-bet as bluffs more frequently.""",
                "lesson_number": 5,
                "module": "intermediate_concepts",
                "tags": ["c-betting", "continuation-betting", "post-flop", "board-texture"],
                "skill_level": "intermediate",
                "prerequisites": ["starting-hands", "position", "pot-odds"]
            },
            {
                "title": "Advanced Theory: Game Theory Optimal Play",
                "content": """Lesson 12: Game Theory Optimal (GTO) play seeks unexploitable strategies through mathematical balance. GTO provides a baseline strategy that cannot be exploited, but may not be maximally profitable against specific opponents. Key GTO concepts include: mixed strategies (randomizing between actions), indifference principles (making opponents indifferent between options), and range balancing (protecting strong hands with bluffs). Use GTO as a foundation, then exploit opponent deviations.""",
                "lesson_number": 12,
                "module": "advanced_theory",
                "tags": ["gto", "game-theory", "balance", "unexploitable", "advanced"],
                "skill_level": "advanced",
                "prerequisites": ["c-betting", "bluffing", "range-construction"]
            }
        ]
    
    async def fetch_content(self) -> List[SourceContent]:
        """Fetch learning materials"""
        try:
            content_list = []
            
            for lesson in self.learning_database:
                content = SourceContent(
                    title=lesson["title"],
                    content=lesson["content"],
                    tags=lesson["tags"],
                    metadata={
                        "lesson_number": lesson["lesson_number"],
                        "module": lesson["module"],
                        "skill_level": lesson["skill_level"],
                        "prerequisites": lesson["prerequisites"],
                        "content_type": "learning_material"
                    }
                )
                content_list.append(content)
            
            self.last_update = datetime.now()
            self.logger.info(f"Fetched {len(content_list)} learning materials")
            return content_list
        
        except Exception as e:
            self.logger.error(f"Error fetching learning materials: {e}")
            return []
    
    def process_content(self, raw_content: Any) -> List[SourceContent]:
        """Process learning materials"""
        return raw_content if isinstance(raw_content, list) else []

class KnowledgeSourceManager:
    """
    Manages multiple knowledge sources and coordinates content ingestion
    """
    
    def __init__(self, knowledge_base, vector_store):
        self.knowledge_base = knowledge_base
        self.vector_store = vector_store
        self.sources = {}
        self.logger = logging.getLogger("knowledge_source_manager")
        
        # Initialize default sources
        self._initialize_default_sources()
        
        # Ingestion statistics
        self.ingestion_stats = {
            'total_ingested': 0,
            'successful_ingestions': 0,
            'failed_ingestions': 0,
            'last_ingestion': None
        }
    
    def _initialize_default_sources(self):
        """Initialize default knowledge sources"""
        self.register_source(PokerStrategySource())
        self.register_source(HandHistorySource())
        self.register_source(CommunityContentSource())
        self.register_source(LearningMaterialSource())
    
    def register_source(self, source: KnowledgeSource):
        """Register a new knowledge source"""
        self.sources[source.source_id] = source
        self.logger.info(f"Registered knowledge source: {source.name}")
    
    async def ingest_from_source(self, source_id: str) -> Dict[str, Any]:
        """Ingest content from a specific source"""
        if source_id not in self.sources:
            raise ValueError(f"Unknown source: {source_id}")
        
        source = self.sources[source_id]
        
        try:
            # Fetch content from source
            content_list = await source.fetch_content()
            
            ingested_count = 0
            failed_count = 0
            
            for content in content_list:
                try:
                    # Determine document type and skill level
                    doc_type = self._determine_document_type(content, source)
                    skill_level = self._determine_skill_level(content)
                    
                    # Create knowledge document
                    document = source.create_knowledge_document(content, doc_type, skill_level)
                    
                    # Add to knowledge base
                    if self.knowledge_base.add_document(document):
                        # Add to vector store
                        self.vector_store.add_document_embedding(document)
                        ingested_count += 1
                    else:
                        failed_count += 1
                
                except Exception as e:
                    self.logger.error(f"Error ingesting content '{content.title}': {e}")
                    failed_count += 1
            
            # Update statistics
            self.ingestion_stats['total_ingested'] += ingested_count
            self.ingestion_stats['successful_ingestions'] += ingested_count
            self.ingestion_stats['failed_ingestions'] += failed_count
            self.ingestion_stats['last_ingestion'] = datetime.now()
            
            result = {
                'source_id': source_id,
                'source_name': source.name,
                'total_content': len(content_list),
                'ingested': ingested_count,
                'failed': failed_count,
                'success': True
            }
            
            self.logger.info(f"Ingested {ingested_count}/{len(content_list)} items from {source.name}")
            return result
        
        except Exception as e:
            self.logger.error(f"Error ingesting from source {source_id}: {e}")
            return {
                'source_id': source_id,
                'error': str(e),
                'success': False
            }
    
    async def ingest_from_all_sources(self) -> Dict[str, Any]:
        """Ingest content from all registered sources"""
        results = {}
        
        for source_id in self.sources:
            if self.sources[source_id].should_update():
                results[source_id] = await self.ingest_from_source(source_id)
            else:
                results[source_id] = {
                    'source_id': source_id,
                    'skipped': True,
                    'reason': 'Not due for update'
                }
        
        return {
            'ingestion_results': results,
            'total_sources': len(self.sources),
            'updated_sources': len([r for r in results.values() if r.get('success')]),
            'statistics': self.ingestion_stats
        }
    
    def _determine_document_type(self, content: SourceContent, source: KnowledgeSource) -> DocumentType:
        """Determine document type based on content and source"""
        if source.source_id == "poker_strategy":
            return DocumentType.STRATEGY
        elif source.source_id == "hand_history":
            return DocumentType.HAND_ANALYSIS
        elif source.source_id == "community":
            return DocumentType.COMMUNITY_POST
        elif source.source_id == "learning":
            return DocumentType.LEARNING_MODULE
        else:
            return DocumentType.STRATEGY  # Default
    
    def _determine_skill_level(self, content: SourceContent) -> SkillLevel:
        """Determine skill level from content metadata"""
        skill_level_str = content.metadata.get('skill_level', 'beginner')
        
        try:
            return SkillLevel(skill_level_str)
        except ValueError:
            return SkillLevel.BEGINNER  # Default
    
    def get_source_statistics(self) -> Dict[str, Any]:
        """Get statistics for all sources"""
        stats = {
            'total_sources': len(self.sources),
            'ingestion_stats': self.ingestion_stats,
            'sources': {}
        }
        
        for source_id, source in self.sources.items():
            stats['sources'][source_id] = {
                'name': source.name,
                'description': source.description,
                'last_update': source.last_update.isoformat() if source.last_update else None,
                'should_update': source.should_update()
            }
        
        return stats

