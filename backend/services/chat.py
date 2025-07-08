"""
Chat service for handling prompt construction and GPT-4o interactions.
"""

from api.models import ChatResponse, ToolCall
from llm.openai_client import OpenAIClient
from utils.parser import parse_tool_calls, parse_openai_tool_calls
from services.todoist_mcp import TodoistMCPService
from services.schema_loader import SchemaLoader
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat interactions with GPT-4o."""
    
    def __init__(self):
        """Initialize the chat service with required components."""
        self.openai_client = OpenAIClient()
        self.todoist_service = TodoistMCPService()
        self.schema_loader = SchemaLoader()
        
    async def process_request(
        self, 
        user_input: str, 
        user_id: str, 
        user_memory: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """
        Process a user request and return an AI response.
        
        Args:
            user_input: The user's message
            user_id: Unique user identifier
            user_memory: User's conversation history and preferences
            context: Additional context for the request
            
        Returns:
            ChatResponse with AI response and metadata
        """
        try:
            # Construct the prompt with user memory and available tools
            prompt = self._construct_prompt(user_input, user_memory, context)
            
            # Get available tool schemas
            tool_schemas = self.schema_loader.get_available_schemas()
            
            # Call GPT-4o with tools and get full response
            gpt_response, openai_response = await self.openai_client.chat_completion_with_response(
                messages=[{"role": "user", "content": prompt}],
                tools=tool_schemas
            )
            
            # Parse tool calls from OpenAI response object
            tool_calls = parse_openai_tool_calls(openai_response)
            
            # Execute tool calls if any
            tools_used = []
            tool_results = []
            if tool_calls:
                logger.info(f"Tool calls: {tool_calls}")
                tools_used, tool_results = await self._execute_tool_calls(tool_calls, user_id)
                
                # If tools were executed, get a follow-up response from GPT
                if tool_results:
                    follow_up_prompt = self._construct_follow_up_prompt(user_input, tool_results)
                    gpt_response, _ = await self.openai_client.chat_completion_with_response(
                        messages=[{"role": "user", "content": follow_up_prompt}]
                    )
            else:
                tools_used = []
            
            # Update user memory with this interaction
            memory_updated = self._update_memory(user_memory, user_input, gpt_response, tools_used)
            
            return ChatResponse(
                response=gpt_response,
                user_id=user_id,
                memory_updated=memory_updated,
                tools_used=tools_used if tools_used else None,
                metadata={
                    "tool_calls": [tc.dict() for tc in tool_calls] if tool_calls else None,
                    "tool_results": tool_results if 'tool_results' in locals() else None,
                    "context": context
                }
            )
            
        except Exception as e:
            logger.error(f"Error in process_request: {str(e)}")
            raise
    
    def _construct_prompt(
        self, 
        user_input: str, 
        user_memory: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Construct a comprehensive prompt for GPT-4o.
        
        Args:
            user_input: User's message
            user_memory: User's memory/history
            context: Additional context
            
        Returns:
            Formatted prompt string
        """
        # Base system prompt
        system_prompt = """You are an AI assistant with access to user memory and various tools including Todoist integration. 
        You can help users with tasks, remember their preferences, and manage their todo lists.
        
        Available tools:
        - Todoist: Add tasks, view projects, manage todos
        - Memory: Access and update user preferences and conversation history
        
        When a user asks you to perform an action (like adding a task to Todoist), use the appropriate tool.
        Always be helpful, concise, and use tools when appropriate."""
        
        # Add user memory context
        memory_context = ""
        if user_memory:
            memory_context = f"\nUser Memory:\n{user_memory}\n"
        
        # Add additional context
        context_str = ""
        if context:
            context_str = f"\nAdditional Context:\n{context}\n"
        
        # Construct final prompt
        prompt = f"{system_prompt}{memory_context}{context_str}\nUser: {user_input}\nAssistant:"
        
        return prompt
    
    def _construct_follow_up_prompt(self, original_input: str, tool_results: List[Dict[str, Any]]) -> str:
        """
        Construct a follow-up prompt after tool execution.
        
        Args:
            original_input: Original user input
            tool_results: Results from executed tools
            
        Returns:
            Formatted follow-up prompt
        """
        results_summary = "\n".join([f"- {result.get('action', 'Unknown')}: {result.get('result', 'Completed')}" 
                                   for result in tool_results])
        
        return f"""I just executed some actions for you based on your request: "{original_input}"

Results:
{results_summary}

Please provide a helpful response to the user about what was accomplished."""
    
    async def _execute_tool_calls(self, tool_calls: List[ToolCall], user_id: str) -> tuple[List[str], List[Dict[str, Any]]]:
        """
        Execute tool calls returned by GPT-4o.
        
        Args:
            tool_calls: List of tool calls to execute
            user_id: User ID for context
            
        Returns:
            Tuple of (executed_tools, tool_results)
        """
        executed_tools = []
        tool_results = []
        
        for tool_call in tool_calls:
            try:
                result = None
                
                if tool_call.action == "add_task":
                    # Execute Todoist task creation
                    result = await self.todoist_service.add_task(**tool_call.args)
                    executed_tools.append("todoist_add_task")
                    logger.info(f"Added Todoist task: {result}")
                    
                elif tool_call.action == "get_projects":
                    # Get Todoist projects
                    result = await self.todoist_service.get_projects()
                    executed_tools.append("todoist_get_projects")
                    logger.info(f"Retrieved Todoist projects: {result}")
                    
                elif tool_call.action == "get_tasks":
                    # Get Todoist tasks
                    result = await self.todoist_service.get_tasks(**tool_call.args)
                    executed_tools.append("todoist_get_tasks")
                    logger.info(f"Retrieved Todoist tasks: {result}")
                    
                elif tool_call.action == "complete_task":
                    # Complete a Todoist task
                    result = await self.todoist_service.close_task(**tool_call.args)
                    executed_tools.append("todoist_complete_task")
                    logger.info(f"Completed Todoist task: {result}")
                    
                else:
                    logger.warning(f"Unknown tool call: {tool_call.action}")
                    result = {"error": f"Unknown action: {tool_call.action}"}
                
                # Add result to tool_results
                if result is not None:
                    tool_results.append({
                        "action": tool_call.action,
                        "args": tool_call.args,
                        "result": result,
                        "success": "error" not in str(result).lower()
                    })
                    
            except Exception as e:
                logger.error(f"Error executing tool call {tool_call.action}: {str(e)}")
                tool_results.append({
                    "action": tool_call.action,
                    "args": tool_call.args,
                    "result": {"error": str(e)},
                    "success": False
                })
        
        return executed_tools, tool_results
    
    def _update_memory(
        self, 
        user_memory: Dict[str, Any], 
        user_input: str, 
        ai_response: str, 
        tools_used: List[str]
    ) -> bool:
        """
        Update user memory with the current interaction.
        
        Args:
            user_memory: Current user memory
            user_input: User's message
            ai_response: AI's response
            tools_used: Tools that were used
            
        Returns:
            True if memory was updated, False otherwise
        """
        # Initialize memory if empty
        if not user_memory:
            user_memory = {
                "conversation_history": [],
                "preferences": {},
                "last_interaction": None
            }
        
        # Add current interaction to history
        interaction = {
            "user_input": user_input,
            "ai_response": ai_response,
            "tools_used": tools_used,
            "timestamp": "2024-01-01T00:00:00Z"  # TODO: Use actual timestamp
        }
        
        user_memory["conversation_history"].append(interaction)
        user_memory["last_interaction"] = interaction
        
        # Keep only last 10 interactions to prevent memory bloat
        if len(user_memory["conversation_history"]) > 10:
            user_memory["conversation_history"] = user_memory["conversation_history"][-10:]
        
        return True 