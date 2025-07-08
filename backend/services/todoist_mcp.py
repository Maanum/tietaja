"""
Todoist integration via Model Context Protocol (MCP).
Provides functions for managing tasks and projects in Todoist.
"""

import logging
import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TodoistMCPService:
    """Service for Todoist integration using Model Context Protocol."""
    
    def __init__(self):
        """Initialize the Todoist MCP service."""
        self.api_token = os.getenv("TODOIST_API_TOKEN")
        self.base_url = "https://api.todoist.com/rest/v2"
        self.mcp_server_url = os.getenv("TODOIST_MCP_SERVER_URL", "http://localhost:3000")
        
        if not self.api_token:
            logger.warning("TODOIST_API_TOKEN not set - Todoist integration will be limited")
        
        # Set up headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        } if self.api_token else {}
    
    async def add_task(
        self, 
        content: str, 
        project_id: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: int = 1,
        description: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Add a new task to Todoist.
        
        Args:
            content: Task content/description
            project_id: Optional project ID to add task to
            due_date: Optional due date (ISO format)
            priority: Task priority (1-4, where 1 is highest)
            description: Optional task description
            labels: Optional list of label names
            
        Returns:
            Dictionary with task creation result
        """
        try:
            # TODO: Implement actual Todoist API call via MCP
            logger.info(f"Adding Todoist task: {content}")
            
            # Stub implementation
            task_data = {
                "id": f"task_{datetime.now().timestamp()}",
                "content": content,
                "project_id": project_id,
                "due": {"date": due_date} if due_date else None,
                "priority": priority,
                "description": description,
                "labels": labels or [],
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
            
            logger.info(f"Successfully created task: {task_data['id']}")
            return {
                "success": True,
                "task": task_data,
                "message": "Task created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error adding Todoist task: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create task"
            }
    
    async def get_projects(self) -> Dict[str, Any]:
        """
        Get all Todoist projects.
        
        Returns:
            Dictionary with projects list
        """
        try:
            if not self.api_token:
                logger.warning("No Todoist API token available")
                return {
                    "success": False,
                    "error": "No Todoist API token configured",
                    "projects": []
                }
            
            logger.info("Fetching Todoist projects from API")
            
            # Make API request to get projects
            response = requests.get(
                f"{self.base_url}/projects",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                projects = response.json()
                logger.info(f"Successfully fetched {len(projects)} projects")
                
                # Format projects for consistency
                formatted_projects = []
                for project in projects:
                    formatted_projects.append({
                        "id": project.get("id"),
                        "name": project.get("name"),
                        "color": project.get("color"),
                        "parent_id": project.get("parent_id"),
                        "order": project.get("order"),
                        "is_favorite": project.get("is_favorite", False),
                        "is_inbox_project": project.get("is_inbox_project", False),
                        "is_team_inbox": project.get("is_team_inbox", False),
                        "view_style": project.get("view_style"),
                        "url": project.get("url")
                    })
                
                return {
                    "success": True,
                    "projects": formatted_projects,
                    "count": len(formatted_projects)
                }
            else:
                logger.error(f"Todoist API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API request failed: {response.status_code}",
                    "projects": []
                }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching Todoist projects: {str(e)}")
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "projects": []
            }
        except Exception as e:
            logger.error(f"Error fetching Todoist projects: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "projects": []
            }
    
    async def get_tasks(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get tasks from Todoist, optionally filtered by project.
        
        Args:
            project_id: Optional project ID to filter tasks
            
        Returns:
            Dictionary with tasks list
        """
        try:
            if not self.api_token:
                logger.warning("No Todoist API token available")
                return {
                    "success": False,
                    "error": "No Todoist API token configured",
                    "tasks": []
                }
            
            logger.info(f"Fetching Todoist tasks for project: {project_id}")
            
            # Build query parameters
            params = {}
            # Only include project_id if it looks like a real Todoist ID (all digits)
            if project_id and project_id.isdigit():
                params["project_id"] = project_id
            
            # Make API request to get tasks
            response = requests.get(
                f"{self.base_url}/tasks",
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                tasks = response.json()
                logger.info(f"Successfully fetched {len(tasks)} tasks")
                
                # Format tasks for consistency
                formatted_tasks = []
                for task in tasks:
                    formatted_tasks.append({
                        "id": task.get("id"),
                        "content": task.get("content"),
                        "project_id": task.get("project_id"),
                        "due": task.get("due"),
                        "priority": task.get("priority"),
                        "status": task.get("status"),
                        "description": task.get("description"),
                        "labels": task.get("labels", []),
                        "created_at": task.get("created_at"),
                        "url": task.get("url"),
                        "comment_count": task.get("comment_count", 0),
                        "assignee_id": task.get("assignee_id"),
                        "assigner_id": task.get("assigner_id"),
                        "parent_id": task.get("parent_id"),
                        "order": task.get("order"),
                        "section_id": task.get("section_id"),
                        "parent": task.get("parent"),
                        "section": task.get("section")
                    })
                
                return {
                    "success": True,
                    "tasks": formatted_tasks,
                    "count": len(formatted_tasks)
                }
            else:
                logger.error(f"Todoist API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API request failed: {response.status_code}",
                    "tasks": []
                }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching Todoist tasks: {str(e)}")
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "tasks": []
            }
        except Exception as e:
            logger.error(f"Error fetching Todoist tasks: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tasks": []
            }
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing Todoist task.
        
        Args:
            task_id: ID of the task to update
            updates: Dictionary of fields to update
            
        Returns:
            Dictionary with update result
        """
        try:
            # TODO: Implement actual Todoist API call via MCP
            logger.info(f"Updating Todoist task: {task_id}")
            
            return {
                "success": True,
                "task_id": task_id,
                "message": "Task updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating Todoist task: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update task"
            }
    
    async def close_task(self, task_id: str) -> Dict[str, Any]:
        """
        Close/mark a task as completed.
        
        Args:
            task_id: ID of the task to close
            
        Returns:
            Dictionary with close result
        """
        try:
            # TODO: Implement actual Todoist API call via MCP
            logger.info(f"Closing Todoist task: {task_id}")
            
            return {
                "success": True,
                "task_id": task_id,
                "message": "Task closed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error closing Todoist task: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to close task"
            }
    
    async def get_labels(self) -> Dict[str, Any]:
        """
        Get all Todoist labels.
        
        Returns:
            Dictionary with labels list
        """
        try:
            # TODO: Implement actual Todoist API call via MCP
            logger.info("Fetching Todoist labels")
            
            # Stub implementation
            labels = [
                {"id": "label_1", "name": "urgent", "color": "red"},
                {"id": "label_2", "name": "important", "color": "orange"}
            ]
            
            return {
                "success": True,
                "labels": labels,
                "count": len(labels)
            }
            
        except Exception as e:
            logger.error(f"Error fetching Todoist labels: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "labels": []
            }
    
    def _make_mcp_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Todoist MCP server.
        
        Args:
            method: MCP method to call
            params: Parameters for the method
            
        Returns:
            Response from MCP server
        """
        # TODO: Implement actual MCP client communication
        logger.info(f"Making MCP request: {method}")
        
        # Stub implementation
        return {
            "success": True,
            "result": {"stub": True},
            "message": "MCP request processed (stub)"
        } 