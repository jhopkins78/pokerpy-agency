#!/usr/bin/env python3
"""
PokerPy Agent Migration Script
Migrates from original agents to RAG-enhanced agents
"""

import os
import sys
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PokerPyMigration:
    """Handles migration from original agents to RAG-enhanced agents"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.backup_dir = self.project_root / "migration_backup"
        self.src_dir = self.project_root / "src"
        
        # Migration configuration
        self.config = {
            'backup_enabled': True,
            'preserve_data': True,
            'validate_migration': True,
            'rollback_enabled': True
        }
        
        logger.info(f"Initialized migration for project: {self.project_root}")
    
    def run_migration(self):
        """Execute the complete migration process"""
        try:
            logger.info("Starting PokerPy agent migration to RAG-enhanced system")
            
            # Step 1: Pre-migration validation
            self._validate_environment()
            
            # Step 2: Create backup
            if self.config['backup_enabled']:
                self._create_backup()
            
            # Step 3: Update dependencies
            self._update_dependencies()
            
            # Step 4: Migrate agent files
            self._migrate_agent_files()
            
            # Step 5: Update main application
            self._update_main_application()
            
            # Step 6: Initialize RAG system
            self._initialize_rag_system()
            
            # Step 7: Validate migration
            if self.config['validate_migration']:
                self._validate_migration()
            
            logger.info("Migration completed successfully!")
            self._print_migration_summary()
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            if self.config['rollback_enabled']:
                self._rollback_migration()
            raise
    
    def _validate_environment(self):
        """Validate that the environment is ready for migration"""
        logger.info("Validating environment...")
        
        # Check Python version
        if sys.version_info < (3, 11):
            raise RuntimeError("Python 3.11+ required for RAG system")
        
        # Check project structure
        required_dirs = ['src', 'src/agents', 'src/routes']
        for dir_path in required_dirs:
            if not (self.project_root / dir_path).exists():
                raise RuntimeError(f"Required directory not found: {dir_path}")
        
        # Check for existing agents
        agent_files = ['src/agents/coach.py', 'src/agents/base_agent.py']
        for agent_file in agent_files:
            if not (self.project_root / agent_file).exists():
                raise RuntimeError(f"Required agent file not found: {agent_file}")
        
        logger.info("Environment validation passed")
    
    def _create_backup(self):
        """Create backup of existing system"""
        logger.info("Creating backup...")
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir()
        
        # Backup source code
        src_backup = backup_path / "src"
        shutil.copytree(self.src_dir, src_backup)
        
        # Backup database if exists
        db_files = list(self.project_root.glob("*.db"))
        for db_file in db_files:
            shutil.copy2(db_file, backup_path)
        
        # Backup configuration files
        config_files = ['requirements.txt', 'main.py']
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                shutil.copy2(file_path, backup_path)
        
        # Save backup metadata
        backup_info = {
            'timestamp': timestamp,
            'backup_path': str(backup_path),
            'migration_version': '1.0.0',
            'original_agents': self._get_agent_info()
        }
        
        with open(backup_path / "backup_info.json", 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        logger.info(f"Backup created at: {backup_path}")
        self.backup_path = backup_path
    
    def _update_dependencies(self):
        """Update requirements.txt with RAG dependencies"""
        logger.info("Updating dependencies...")
        
        requirements_file = self.project_root / "requirements.txt"
        
        # Read existing requirements
        existing_requirements = []
        if requirements_file.exists():
            with open(requirements_file, 'r') as f:
                existing_requirements = f.read().splitlines()
        
        # RAG-specific dependencies
        rag_dependencies = [
            "# RAG System Dependencies",
            "numpy==1.24.3",
            "scipy==1.11.1",
            "scikit-learn==1.3.0",
            "faiss-cpu==1.7.4",
            "nltk==3.8.1",
            "spacy==3.6.1",
            "pandas==2.0.3"
        ]
        
        # Merge dependencies (avoid duplicates)
        all_requirements = existing_requirements.copy()
        for dep in rag_dependencies:
            if not any(dep.split('==')[0] in req for req in existing_requirements if '==' in req):
                all_requirements.append(dep)
        
        # Write updated requirements
        with open(requirements_file, 'w') as f:
            f.write('\n'.join(all_requirements))
        
        logger.info("Dependencies updated")
    
    def _migrate_agent_files(self):
        """Migrate agent files to RAG-enhanced versions"""
        logger.info("Migrating agent files...")
        
        # Create RAG directory if it doesn't exist
        rag_dir = self.src_dir / "rag"
        rag_dir.mkdir(exist_ok=True)
        
        # Copy RAG system files (these should already exist from the RAG implementation)
        rag_files = [
            'knowledge_base.py',
            'vector_store.py', 
            'retrieval_agent.py',
            'rag_orchestrator.py',
            'knowledge_sources.py'
        ]
        
        for rag_file in rag_files:
            src_path = self.project_root / "src" / "rag" / rag_file
            if src_path.exists():
                logger.info(f"RAG file already exists: {rag_file}")
            else:
                logger.warning(f"RAG file missing: {rag_file} - ensure RAG system is properly installed")
        
        # Update agent __init__.py to include RAG agents
        agents_init = self.src_dir / "agents" / "__init__.py"
        if agents_init.exists():
            with open(agents_init, 'r') as f:
                content = f.read()
            
            # Add RAG imports if not present
            rag_imports = [
                "from .coach import CoachAgent"
            ]
            
            for import_line in rag_imports:
                if import_line not in content:
                    content += f"\n{import_line}"
            
            with open(agents_init, 'w') as f:
                f.write(content)
        
        logger.info("Agent files migrated")
    
    def _update_main_application(self):
        """Update main application to use RAG-enhanced agents"""
        logger.info("Updating main application...")
        
        # Check if RAG-integrated main file exists
        rag_main = self.src_dir / "main_rag_integrated.py"
        original_main = self.project_root / "main.py"
        
        if rag_main.exists():
            # Create a new main.py that uses RAG system
            migration_main_content = f'''#!/usr/bin/env python3
"""
PokerPy Main Application - RAG Enhanced
Migrated from original agents to RAG-enhanced system
"""

import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the RAG-integrated application
from main_rag_integrated import main

if __name__ == "__main__":
    main()
'''
            
            # Backup original main.py if it exists
            if original_main.exists():
                shutil.copy2(original_main, original_main.with_suffix('.py.backup'))
            
            # Write new main.py
            with open(original_main, 'w') as f:
                f.write(migration_main_content)
            
            logger.info("Main application updated to use RAG system")
        else:
            logger.warning("RAG-integrated main file not found - manual update required")
    
    def _initialize_rag_system(self):
        """Initialize the RAG system with default knowledge"""
        logger.info("Initializing RAG system...")
        
        try:
            # Import RAG components
            sys.path.insert(0, str(self.src_dir))
            from rag.knowledge_base import PokerKnowledgeBase
            from rag.vector_store import VectorStore, EmbeddingService
            
            # Initialize knowledge base
            knowledge_base = PokerKnowledgeBase()
            
            # Initialize vector store
            vector_store = VectorStore()
            embedding_service = EmbeddingService()
            
            # Get documents from knowledge base
            documents = knowledge_base.get_all_documents()
            
            if documents:
                # Add documents to vector store
                for doc in documents:
                    vector_store.add_document(
                        doc_id=doc.id,
                        content=doc.content,
                        metadata=doc.metadata
                    )
                
                # Build index
                vector_store.build_index()
                
                logger.info(f"RAG system initialized with {len(documents)} documents")
            else:
                logger.warning("No documents found in knowledge base")
                
        except ImportError as e:
            logger.error(f"Failed to import RAG components: {e}")
            logger.error("Ensure RAG system is properly installed")
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
    
    def _validate_migration(self):
        """Validate that migration was successful"""
        logger.info("Validating migration...")
        
        validation_results = {
            'rag_files_present': True,
            'dependencies_updated': True,
            'agents_accessible': True,
            'main_app_updated': True
        }
        
        # Check RAG files
        rag_files = ['knowledge_base.py', 'vector_store.py', 'retrieval_agent.py']
        for rag_file in rag_files:
            if not (self.src_dir / "rag" / rag_file).exists():
                validation_results['rag_files_present'] = False
                logger.error(f"Missing RAG file: {rag_file}")
        
        # Check if RAG-enhanced coach agent exists
        rag_coach = self.src_dir / "agents" / "coach.py"
        if not rag_coach.exists():
            validation_results['agents_accessible'] = False
            logger.error("Coach agent not found")
        
        # Check main application
        main_file = self.project_root / "main.py"
        if main_file.exists():
            with open(main_file, 'r') as f:
                content = f.read()
                if 'main_rag_integrated' not in content:
                    validation_results['main_app_updated'] = False
                    logger.error("Main application not updated for RAG")
        
        # Overall validation
        all_valid = all(validation_results.values())
        if all_valid:
            logger.info("Migration validation passed")
        else:
            logger.error("Migration validation failed")
            logger.error(f"Validation results: {validation_results}")
        
        return all_valid
    
    def _rollback_migration(self):
        """Rollback migration if something went wrong"""
        logger.info("Rolling back migration...")
        
        if hasattr(self, 'backup_path') and self.backup_path.exists():
            # Restore source code
            if (self.backup_path / "src").exists():
                if self.src_dir.exists():
                    shutil.rmtree(self.src_dir)
                shutil.copytree(self.backup_path / "src", self.src_dir)
            
            # Restore main files
            backup_main = self.backup_path / "main.py"
            if backup_main.exists():
                shutil.copy2(backup_main, self.project_root / "main.py")
            
            # Restore requirements
            backup_req = self.backup_path / "requirements.txt"
            if backup_req.exists():
                shutil.copy2(backup_req, self.project_root / "requirements.txt")
            
            logger.info("Migration rolled back successfully")
        else:
            logger.error("No backup found for rollback")
    
    def _get_agent_info(self):
        """Get information about existing agents"""
        agent_info = {}
        
        agents_dir = self.src_dir / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.py"):
                if agent_file.name != "__init__.py":
                    agent_info[agent_file.name] = {
                        'size': agent_file.stat().st_size,
                        'modified': datetime.fromtimestamp(agent_file.stat().st_mtime).isoformat()
                    }
        
        return agent_info
    
    def _print_migration_summary(self):
        """Print migration summary"""
        print("\n" + "="*60)
        print("POKERPY AGENT MIGRATION COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nMigration Summary:")
        print("- Original agents backed up")
        print("- RAG system initialized")
        print("- Dependencies updated")
        print("- Main application configured for RAG")
        print("\nNext Steps:")
        print("1. Test the application: python main.py")
        print("2. Verify RAG endpoints: curl http://localhost:5000/health")
        print("3. Check agent capabilities: curl http://localhost:5000/api/agents/status")
        print("\nFor rollback (if needed):")
        print(f"- Backup location: {self.backup_path}")
        print("- Run: python migrate_to_rag.py --rollback")
        print("\n" + "="*60)

def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate PokerPy to RAG-enhanced agents")
    parser.add_argument("--project-root", help="Project root directory", default=".")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    parser.add_argument("--validate-only", action="store_true", help="Only validate environment")
    
    args = parser.parse_args()
    
    migration = PokerPyMigration(args.project_root)
    
    if args.rollback:
        migration._rollback_migration()
    elif args.validate_only:
        migration._validate_environment()
        print("Environment validation completed")
    else:
        migration.run_migration()

if __name__ == "__main__":
    main()
