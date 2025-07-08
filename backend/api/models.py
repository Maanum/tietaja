"""
Pydantic models for API request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    """Request model for chat interactions."""
    user_input: str = Field(..., description="User's message or question")
    user_id: str = Field(..., description="Unique identifier for the user")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for the request")
    
class ChatResponse(BaseModel):
    """Response model for chat interactions."""
    response: str = Field(..., description="AI assistant's response")
    user_id: str = Field(..., description="User ID this response is for")
    memory_updated: bool = Field(default=False, description="Whether user memory was updated")
    tools_used: Optional[List[str]] = Field(default=None, description="List of tools/actions used")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional response metadata")

class ToolCall(BaseModel):
    """Model for structured tool calls."""
    action: str = Field(..., description="Name of the action to perform")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the action")
    confidence: float = Field(default=1.0, description="Confidence score for this tool call") 