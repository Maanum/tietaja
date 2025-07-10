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
from datetime import datetime

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
        debug_trace = []
        
        try:
            debug_trace.append("📥 Loading user memory and context...")
            
            # Build conversation history from user memory
            debug_trace.append("📚 Building conversation history...")
            messages = self._build_conversation_messages(user_input, user_memory, context)
            debug_trace.append(f"✅ Built conversation with {len(messages)} messages")
            
            # Get available tool schemas
            debug_trace.append("🔧 Loading available tool schemas...")
            tool_schemas = self.schema_loader.get_available_schemas()
            debug_trace.append(f"✅ Found {len(tool_schemas) if tool_schemas else 0} available tools")
            
            # Call GPT-4o with tools and get full response
            debug_trace.append("🤖 Sending conversation to GPT-4o with tools...")
            gpt_response, openai_response = await self.openai_client.chat_completion_with_response(
                messages=messages,
                tools=tool_schemas
            )
            debug_trace.append("✅ Received response from GPT-4o")
            
            # Parse tool calls from OpenAI response object
            debug_trace.append("🔍 Parsing tool calls from response...")
            tool_calls = parse_openai_tool_calls(openai_response)
            
            # Execute tool calls if any
            tools_used = []
            tool_results = []
            if tool_calls:
                debug_trace.append(f"⚡ Executing {len(tool_calls)} tool calls...")
                logger.info(f"Tool calls: {tool_calls}")
                tools_used, tool_results = await self._execute_tool_calls(tool_calls, user_id)
                debug_trace.append(f"✅ Completed {len(tools_used)} tool executions")
                
                # If tools were executed, get a follow-up response from GPT
                if tool_results:
                    debug_trace.append("🔄 Getting follow-up response after tool execution...")
                    follow_up_messages = self._build_follow_up_messages(user_input, tool_results, messages)
                    gpt_response, _ = await self.openai_client.chat_completion_with_response(
                        messages=follow_up_messages
                    )
                    debug_trace.append("✅ Received follow-up response")
            else:
                debug_trace.append("ℹ️ No tool calls detected in response")
                tools_used = []
            
            # Update user memory with this interaction
            debug_trace.append("💾 Updating user memory...")
            memory_updated = self._update_memory(user_memory, user_input, gpt_response, tools_used)
            debug_trace.append(f"✅ Memory updated: {memory_updated}")
            
            return ChatResponse(
                response=gpt_response,
                user_id=user_id,
                memory_updated=memory_updated,
                tools_used=tools_used if tools_used else None,
                debug_trace=debug_trace,
                metadata={
                    "tool_calls": [tc.dict() for tc in tool_calls] if tool_calls else None,
                    "tool_results": tool_results if 'tool_results' in locals() else None,
                    "context": context
                }
            )
            
        except Exception as e:
            debug_trace.append(f"❌ Error occurred: {str(e)}")
            logger.error(f"Error in process_request: {str(e)}")
            raise
    
    def _build_conversation_messages(
        self, 
        user_input: str, 
        user_memory: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Build conversation messages for GPT-4o from user memory and current input.
        
        Args:
            user_input: Current user message
            user_memory: User's conversation history and preferences
            context: Additional context
            
        Returns:
            List of messages in OpenAI format
        """
        messages = []
        
        # Add system message
        system_prompt = """You are an AI assistant with access to user memory and various tools including Todoist integration. 
        You can help users with tasks, remember their preferences, and manage their todo lists.
        
        Available tools:
        - Todoist: Add tasks, view projects, manage todos
        - Memory: Access and update user preferences and conversation history
        
        When a user asks you to perform an action (like adding a task to Todoist), use the appropriate tool.
        Always be helpful, concise, and use tools when appropriate.
        
        For complex operations like deleting all tasks from a project:
        1. First use get_projects to find the project ID
        2. Then use get_tasks with the project_id to get all tasks in that project
        3. Finally use delete_task for each task ID found
        
        IMPORTANT: For bulk operations, you should execute all necessary tool calls in sequence to complete the user's request. 
        Do not stop after just getting project information - continue with the actual deletion operations."""
        
        # Add user preferences context if available
        if user_memory and user_memory.get("preferences"):
            prefs = user_memory["preferences"]
            system_prompt += f"\n\nUser Preferences:\n- Language: {prefs.get('language', 'en')}\n- Timezone: {prefs.get('timezone', 'UTC')}"
        
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history from memory
        if user_memory and user_memory.get("conversation_history"):
            history = user_memory["conversation_history"]
            # Keep only last 5 interactions to prevent token limit issues
            recent_history = history[-5:] if len(history) > 5 else history
            
            for interaction in recent_history:
                if interaction.get("user_input"):
                    messages.append({"role": "user", "content": interaction["user_input"]})
                if interaction.get("ai_response"):
                    messages.append({"role": "assistant", "content": interaction["ai_response"]})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _build_follow_up_messages(
        self, 
        original_input: str, 
        tool_results: List[Dict[str, Any]], 
        original_messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Build follow-up messages after tool execution.
        
        Args:
            original_input: Original user input
            tool_results: Results from executed tools
            original_messages: Original conversation messages
            
        Returns:
            List of messages for follow-up response
        """
        # Start with original conversation
        messages = original_messages.copy()
        
        # Add tool execution results
        results_summary = "\n".join([f"- {result.get('action', 'Unknown')}: {result.get('result', 'Completed')}" 
                                   for result in tool_results])
        
        tool_message = f"""I just executed some actions for you based on your request: "{original_input}"

Results:
{results_summary}

Please provide a helpful response to the user about what was accomplished."""
        
        messages.append({"role": "user", "content": tool_message})
        
        return messages
    
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
                    
                elif tool_call.action == "delete_task":
                    # Delete a Todoist task
                    result = await self.todoist_service.delete_task(**tool_call.args)
                    executed_tools.append("todoist_delete_task")
                    logger.info(f"Deleted Todoist task: {result}")
                    
                elif tool_call.action == "update_task":
                    # Update a Todoist task
                    result = await self.todoist_service.update_task(**tool_call.args)
                    executed_tools.append("todoist_update_task")
                    logger.info(f"Updated Todoist task: {result}")
                    
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
            "timestamp": datetime.now().isoformat()
        }
        
        user_memory["conversation_history"].append(interaction)
        user_memory["last_interaction"] = interaction
        
        # Keep only last 10 interactions to prevent memory bloat
        if len(user_memory["conversation_history"]) > 10:
            user_memory["conversation_history"] = user_memory["conversation_history"][-10:]
        
        return True 