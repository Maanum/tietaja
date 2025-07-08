"""
Memory service for loading and saving user-specific memory as JSON.
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class MemoryService:
    """Service for managing user memory persistence."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the memory service.
        
        Args:
            data_dir: Directory to store memory files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def load_memory(self, user_id: str) -> Dict[str, Any]:
        """
        Load user memory from JSON file.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            User memory dictionary, empty dict if no memory exists
        """
        try:
            memory_file = self.data_dir / f"memory_{user_id}.json"
            
            if not memory_file.exists():
                logger.info(f"No memory file found for user {user_id}, creating new memory")
                return self._create_default_memory()
            
            with open(memory_file, 'r', encoding='utf-8') as f:
                memory = json.load(f)
                logger.info(f"Loaded memory for user {user_id}")
                return memory
                
        except Exception as e:
            logger.error(f"Error loading memory for user {user_id}: {str(e)}")
            return self._create_default_memory()
    
    def save_memory(self, user_id: str, memory: Dict[str, Any]) -> bool:
        """
        Save user memory to JSON file.
        
        Args:
            user_id: Unique user identifier
            memory: Memory dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            memory_file = self.data_dir / f"memory_{user_id}.json"
            
            # Create backup of existing file
            if memory_file.exists():
                backup_file = self.data_dir / f"memory_{user_id}.json.backup"
                memory_file.rename(backup_file)
            
            # Save new memory
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved memory for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving memory for user {user_id}: {str(e)}")
            return False
    
    def update_memory(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific parts of user memory.
        
        Args:
            user_id: Unique user identifier
            updates: Dictionary of updates to apply
            
        Returns:
            True if successful, False otherwise
        """
        try:
            memory = self.load_memory(user_id)
            memory.update(updates)
            return self.save_memory(user_id, memory)
            
        except Exception as e:
            logger.error(f"Error updating memory for user {user_id}: {str(e)}")
            return False
    
    def delete_memory(self, user_id: str) -> bool:
        """
        Delete user memory file.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            memory_file = self.data_dir / f"memory_{user_id}.json"
            
            if memory_file.exists():
                memory_file.unlink()
                logger.info(f"Deleted memory for user {user_id}")
                return True
            else:
                logger.warning(f"No memory file found for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting memory for user {user_id}: {str(e)}")
            return False
    
    def _create_default_memory(self) -> Dict[str, Any]:
        """
        Create a default memory structure for new users.
        
        Returns:
            Default memory dictionary
        """
        return {
            "user_id": None,
            "conversation_history": [],
            "preferences": {
                "language": "en",
                "timezone": "UTC",
                "notification_preferences": {}
            },
            "todoist_integration": {
                "enabled": False,
                "last_sync": None,
                "project_mappings": {}
            },
            "created_at": "2024-01-01T00:00:00Z",
            "last_updated": "2024-01-01T00:00:00Z",
            "interaction_count": 0
        }
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about user memory.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Dictionary with memory statistics
        """
        try:
            memory = self.load_memory(user_id)
            memory_file = self.data_dir / f"memory_{user_id}.json"
            
            stats = {
                "user_id": user_id,
                "memory_exists": memory_file.exists(),
                "file_size_bytes": memory_file.stat().st_size if memory_file.exists() else 0,
                "conversation_count": len(memory.get("conversation_history", [])),
                "interaction_count": memory.get("interaction_count", 0),
                "preferences_count": len(memory.get("preferences", {})),
                "last_updated": memory.get("last_updated", "Unknown")
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting memory stats for user {user_id}: {str(e)}")
            return {"user_id": user_id, "error": str(e)} 