"""
API endpoints for the AI Butler application.
"""

from fastapi import APIRouter, HTTPException
from api.models import ChatRequest, ChatResponse
from services.chat import ChatService
from services.memory import MemoryService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Initialize services (will be done at runtime)
chat_service = None
memory_service = None

def get_services():
    """Get or initialize services."""
    global chat_service, memory_service
    if chat_service is None:
        chat_service = ChatService()
    if memory_service is None:
        memory_service = MemoryService()
    return chat_service, memory_service

@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """
    Main chat endpoint that processes user input and returns AI response.
    
    Args:
        request: ChatRequest containing user input and ID
        
    Returns:
        ChatResponse with AI response and metadata
    """
    try:
        logger.info(f"Processing request for user: {request.user_id}")
        
        # Get services
        chat_service, memory_service = get_services()
        
        # Load user memory
        user_memory = memory_service.load_memory(request.user_id)
        
        # Process the chat request
        response = await chat_service.process_request(
            user_input=request.user_input,
            user_id=request.user_id,
            user_memory=user_memory,
            context=request.context
        )
        
        # Save updated memory if needed
        if response.memory_updated:
            memory_service.save_memory(request.user_id, user_memory)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/memory/{user_id}")
async def get_user_memory(user_id: str):
    """
    Retrieve user memory for debugging/development purposes.
    """
    try:
        chat_service, memory_service = get_services()
        memory = memory_service.load_memory(user_id)
        return {"user_id": user_id, "memory": memory}
    except Exception as e:
        logger.error(f"Error loading memory for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load user memory")

@router.post("/test-tools")
async def test_tool_execution():
    """
    Test endpoint to verify tool call execution is working.
    """
    try:
        chat_service, memory_service = get_services()
        
        # Test with a simple tool request
        test_memory = {"conversation_history": [], "preferences": {}}
        
        response = await chat_service.process_request(
            user_input="Add a task to buy groceries",
            user_id="test_user",
            user_memory=test_memory
        )
        
        return {
            "message": "Tool execution test completed",
            "response": response.response,
            "tools_used": response.tools_used,
            "metadata": response.metadata
        }
        
    except Exception as e:
        logger.error(f"Error in tool execution test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Tool execution test failed: {str(e)}")

@router.get("/test-todoist")
async def test_todoist_integration():
    """
    Test endpoint to verify Todoist API integration.
    """
    try:
        chat_service, memory_service = get_services()
        
        # Test Todoist service directly
        todoist_service = chat_service.todoist_service
        
        # Test getting projects
        projects_result = await todoist_service.get_projects()
        
        # Test getting tasks
        tasks_result = await todoist_service.get_tasks()
        
        return {
            "message": "Todoist integration test completed",
            "projects": projects_result,
            "tasks": tasks_result,
            "api_token_configured": bool(todoist_service.api_token)
        }
        
    except Exception as e:
        logger.error(f"Error in Todoist integration test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Todoist integration test failed: {str(e)}") 