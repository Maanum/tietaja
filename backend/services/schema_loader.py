"""
Schema loader for MCP action schemas.
Loads tool schemas from local JSON files for GPT-4o function calling.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SchemaLoader:
    """Service for loading MCP action schemas from local JSON files."""
    
    def __init__(self, schemas_dir: str = "schemas"):
        """
        Initialize the schema loader.
        
        Args:
            schemas_dir: Directory containing schema JSON files
        """
        self.schemas_dir = Path(schemas_dir)
        self.schemas_dir.mkdir(exist_ok=True)
        self._schemas_cache = {}
        self._load_default_schemas()
    
    def get_available_schemas(self) -> List[Dict[str, Any]]:
        """
        Get all available tool schemas for GPT-4o function calling.
        
        Returns:
            List of tool schemas in OpenAI format
        """
        try:
            schemas = []
            
            # Add Todoist schemas
            todoist_schemas = self._get_todoist_schemas()
            schemas.extend(todoist_schemas)
            
            # Add memory schemas
            memory_schemas = self._get_memory_schemas()
            schemas.extend(memory_schemas)
            
            # Load custom schemas from files
            custom_schemas = self._load_custom_schemas()
            schemas.extend(custom_schemas)
            
            logger.info(f"Loaded {len(schemas)} tool schemas")
            return schemas
            
        except Exception as e:
            logger.error(f"Error loading schemas: {str(e)}")
            return []
    
    def get_schema_by_name(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific schema by name.
        
        Args:
            schema_name: Name of the schema to retrieve
            
        Returns:
            Schema dictionary or None if not found
        """
        schemas = self.get_available_schemas()
        for schema in schemas:
            if schema.get("function", {}).get("name") == schema_name:
                return schema
        return None
    
    def _get_todoist_schemas(self) -> List[Dict[str, Any]]:
        """
        Get Todoist-related tool schemas.
        
        Returns:
            List of Todoist tool schemas
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "add_task",
                    "description": "Add a new task to Todoist",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The content/description of the task"
                            },
                            "project_id": {
                                "type": "string",
                                "description": "Optional project ID to add the task to"
                            },
                            "due_date": {
                                "type": "string",
                                "description": "Optional due date in ISO format (YYYY-MM-DD)"
                            },
                            "priority": {
                                "type": "integer",
                                "description": "Task priority (1-4, where 1 is highest)",
                                "minimum": 1,
                                "maximum": 4
                            },
                            "description": {
                                "type": "string",
                                "description": "Optional detailed description of the task"
                            },
                            "labels": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional list of label names to apply"
                            }
                        },
                        "required": ["content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_projects",
                    "description": "Get all Todoist projects",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_tasks",
                    "description": "Get tasks from Todoist, optionally filtered by project",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "Optional project ID to filter tasks"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "complete_task",
                    "description": "Mark a Todoist task as completed",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "The ID of the task to complete"
                            }
                        },
                        "required": ["task_id"]
                    }
                }
            }
        ]
    
    def _get_memory_schemas(self) -> List[Dict[str, Any]]:
        """
        Get memory-related tool schemas.
        
        Returns:
            List of memory tool schemas
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "update_preference",
                    "description": "Update a user preference in memory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "The preference key to update"
                            },
                            "value": {
                                "type": "string",
                                "description": "The new value for the preference"
                            }
                        },
                        "required": ["key", "value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_preference",
                    "description": "Get a user preference from memory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "The preference key to retrieve"
                            }
                        },
                        "required": ["key"]
                    }
                }
            }
        ]
    
    def _load_custom_schemas(self) -> List[Dict[str, Any]]:
        """
        Load custom schemas from JSON files in the schemas directory.
        
        Returns:
            List of custom tool schemas
        """
        schemas = []
        
        try:
            for schema_file in self.schemas_dir.glob("*.json"):
                try:
                    with open(schema_file, 'r', encoding='utf-8') as f:
                        schema_data = json.load(f)
                        
                        # Handle both single schema and array of schemas
                        if isinstance(schema_data, list):
                            schemas.extend(schema_data)
                        else:
                            schemas.append(schema_data)
                            
                    logger.info(f"Loaded custom schema from {schema_file}")
                    
                except Exception as e:
                    logger.error(f"Error loading schema from {schema_file}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error scanning schemas directory: {str(e)}")
        
        return schemas
    
    def _load_default_schemas(self):
        """Load and cache default schemas."""
        try:
            # Create default schema files if they don't exist
            self._create_default_schema_files()
            
        except Exception as e:
            logger.error(f"Error loading default schemas: {str(e)}")
    
    def _create_default_schema_files(self):
        """Create default schema files for common tools."""
        default_schemas = {
            "todoist.json": self._get_todoist_schemas(),
            "memory.json": self._get_memory_schemas()
        }
        
        for filename, schemas in default_schemas.items():
            schema_file = self.schemas_dir / filename
            
            if not schema_file.exists():
                try:
                    with open(schema_file, 'w', encoding='utf-8') as f:
                        json.dump(schemas, f, indent=2)
                    logger.info(f"Created default schema file: {filename}")
                except Exception as e:
                    logger.error(f"Error creating schema file {filename}: {str(e)}")
    
    def reload_schemas(self) -> bool:
        """
        Reload all schemas from files.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self._schemas_cache.clear()
            self._load_default_schemas()
            logger.info("Schemas reloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error reloading schemas: {str(e)}")
            return False
    
    def validate_schema(self, schema: Dict[str, Any]) -> bool:
        """
        Validate a schema structure.
        
        Args:
            schema: Schema dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation
            if not isinstance(schema, dict):
                return False
            
            if "type" not in schema or schema["type"] != "function":
                return False
            
            if "function" not in schema:
                return False
            
            function = schema["function"]
            if "name" not in function or "description" not in function:
                return False
            
            return True
            
        except Exception:
            return False 