"""
Parser utility for parsing GPT-4o output into structured tool calls.
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional
from api.models import ToolCall

logger = logging.getLogger(__name__)

def parse_tool_calls(gpt_response: str) -> List[ToolCall]:
    """
    Parse GPT-4o response to extract structured tool calls.
    
    Args:
        gpt_response: Raw response from GPT-4o
        
    Returns:
        List of ToolCall objects
    """
    tool_calls = []
    
    try:
        # Method 1: Look for JSON tool calls in the response
        json_tool_calls = _extract_json_tool_calls(gpt_response)
        if json_tool_calls:
            tool_calls.extend(json_tool_calls)
        
        # Method 2: Look for function call patterns
        function_calls = _extract_function_calls(gpt_response)
        if function_calls:
            tool_calls.extend(function_calls)
        
        # Method 3: Look for action patterns
        action_calls = _extract_action_calls(gpt_response)
        if action_calls:
            tool_calls.extend(action_calls)
        
        # Method 4: Look for natural language tool requests
        natural_calls = _extract_natural_tool_requests(gpt_response)
        if natural_calls:
            tool_calls.extend(natural_calls)
        
        logger.info(f"Parsed {len(tool_calls)} tool calls from response")
        return tool_calls
        
    except Exception as e:
        logger.error(f"Error parsing tool calls: {str(e)}")
        return []

def parse_openai_tool_calls(openai_response) -> List[ToolCall]:
    """
    Parse tool calls directly from OpenAI response object.
    
    Args:
        openai_response: OpenAI response object with tool_calls
        
    Returns:
        List of ToolCall objects
    """
    tool_calls = []
    
    try:
        if hasattr(openai_response, 'choices') and openai_response.choices:
            choice = openai_response.choices[0]
            if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    try:
                        # Parse the function arguments
                        args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                        
                        tool_calls.append(ToolCall(
                            action=tool_call.function.name,
                            args=args,
                            confidence=1.0
                        ))
                        
                        logger.info(f"Parsed OpenAI tool call: {tool_call.function.name}")
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse tool call arguments: {e}")
                        # Try to use raw arguments as string
                        tool_calls.append(ToolCall(
                            action=tool_call.function.name,
                            args={"raw_args": tool_call.function.arguments},
                            confidence=0.8
                        ))
                    except Exception as e:
                        logger.error(f"Error parsing tool call: {e}")
                        continue
        
        logger.info(f"Parsed {len(tool_calls)} OpenAI tool calls")
        return tool_calls
        
    except Exception as e:
        logger.error(f"Error parsing OpenAI tool calls: {str(e)}")
        return []

def _extract_natural_tool_requests(response: str) -> List[ToolCall]:
    """
    Extract tool requests from natural language in the response.
    
    Args:
        response: GPT response text
        
    Returns:
        List of ToolCall objects
    """
    tool_calls = []
    
    # Look for natural language patterns that indicate tool usage
    patterns = [
        (r"add.*task.*['\"]([^'\"]+)['\"]", "add_task", lambda m: {"content": m.group(1)}),
        (r"create.*task.*['\"]([^'\"]+)['\"]", "add_task", lambda m: {"content": m.group(1)}),
        (r"show.*projects", "get_projects", lambda m: {}),
        (r"list.*projects", "get_projects", lambda m: {}),
        (r"get.*projects", "get_projects", lambda m: {}),
        (r"show.*tasks", "get_tasks", lambda m: {}),
        (r"list.*tasks", "get_tasks", lambda m: {}),
        (r"get.*tasks", "get_tasks", lambda m: {}),
        (r"complete.*task.*['\"]([^'\"]+)['\"]", "complete_task", lambda m: {"task_id": m.group(1)}),
        (r"mark.*task.*['\"]([^'\"]+)['\"].*complete", "complete_task", lambda m: {"task_id": m.group(1)}),
    ]
    
    for pattern, action, args_extractor in patterns:
        matches = re.findall(pattern, response, re.IGNORECASE)
        for match in matches:
            try:
                if isinstance(match, tuple):
                    args = args_extractor(match)
                else:
                    args = args_extractor(match)
                
                tool_calls.append(ToolCall(
                    action=action,
                    args=args,
                    confidence=0.7  # Lower confidence for natural language parsing
                ))
                
            except Exception as e:
                logger.warning(f"Error parsing natural tool request: {str(e)}")
                continue
    
    return tool_calls

def _extract_json_tool_calls(response: str) -> List[ToolCall]:
    """
    Extract tool calls from JSON format in the response.
    
    Args:
        response: GPT response text
        
    Returns:
        List of ToolCall objects
    """
    tool_calls = []
    
    # Look for JSON blocks that might contain tool calls
    json_patterns = [
        r'```json\s*(\[.*?\])\s*```',
        r'```\s*(\[.*?\])\s*```',
        r'\{.*?"action".*?"args".*?\}',
        r'\[.*?\{.*?"action".*?"args".*?\}.*?\]'
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                # Try to parse as JSON
                if isinstance(match, str):
                    data = json.loads(match)
                else:
                    data = match
                
                # Handle both single tool call and array of tool calls
                if isinstance(data, list):
                    for item in data:
                        if _is_valid_tool_call(item):
                            tool_calls.append(ToolCall(**item))
                elif _is_valid_tool_call(data):
                    tool_calls.append(ToolCall(**data))
                    
            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.warning(f"Error parsing JSON tool call: {str(e)}")
                continue
    
    return tool_calls

def _extract_function_calls(response: str) -> List[ToolCall]:
    """
    Extract function calls from text patterns.
    
    Args:
        response: GPT response text
        
    Returns:
        List of ToolCall objects
    """
    tool_calls = []
    
    # Look for function call patterns
    function_patterns = [
        r'function:\s*(\w+)\s*args:\s*(\{.*?\})',
        r'call\s+(\w+)\s*\(([^)]+)\)',
        r'(\w+)\s*:\s*(\{.*?\})'
    ]
    
    for pattern in function_patterns:
        matches = re.findall(pattern, response, re.IGNORECASE)
        for match in matches:
            try:
                if len(match) == 2:
                    action, args_str = match
                    
                    # Try to parse args as JSON
                    try:
                        args = json.loads(args_str)
                    except json.JSONDecodeError:
                        # If not JSON, try to parse as key-value pairs
                        args = _parse_key_value_pairs(args_str)
                    
                    tool_calls.append(ToolCall(
                        action=action.strip(),
                        args=args if isinstance(args, dict) else {"raw_args": args_str}
                    ))
                    
            except Exception as e:
                logger.warning(f"Error parsing function call: {str(e)}")
                continue
    
    return tool_calls

def _extract_action_calls(response: str) -> List[ToolCall]:
    """
    Extract action calls from text patterns.
    
    Args:
        response: GPT response text
        
    Returns:
        List of ToolCall objects
    """
    tool_calls = []
    
    # Look for action patterns
    action_patterns = [
        r'action:\s*(\w+)',
        r'perform\s+(\w+)',
        r'execute\s+(\w+)',
        r'run\s+(\w+)'
    ]
    
    for pattern in action_patterns:
        matches = re.findall(pattern, response, re.IGNORECASE)
        for match in matches:
            try:
                action = match.strip()
                
                # Look for arguments near the action
                args = _extract_nearby_args(response, action)
                
                tool_calls.append(ToolCall(
                    action=action,
                    args=args
                ))
                
            except Exception as e:
                logger.warning(f"Error parsing action call: {str(e)}")
                continue
    
    return tool_calls

def _is_valid_tool_call(data: Dict[str, Any]) -> bool:
    """
    Check if a dictionary represents a valid tool call.
    
    Args:
        data: Dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    return (
        isinstance(data, dict) and
        "action" in data and
        isinstance(data["action"], str) and
        "args" in data and
        isinstance(data["args"], dict)
    )

def _parse_key_value_pairs(text: str) -> Dict[str, Any]:
    """
    Parse key-value pairs from text.
    
    Args:
        text: Text containing key-value pairs
        
    Returns:
        Dictionary of parsed key-value pairs
    """
    result = {}
    
    # Simple key-value parsing
    pairs = re.findall(r'(\w+)\s*[:=]\s*([^,\s]+)', text)
    for key, value in pairs:
        # Try to convert value to appropriate type
        if value.lower() in ('true', 'false'):
            result[key] = value.lower() == 'true'
        elif value.isdigit():
            result[key] = int(value)
        elif value.replace('.', '').isdigit():
            result[key] = float(value)
        else:
            result[key] = value
    
    return result

def _extract_nearby_args(response: str, action: str) -> Dict[str, Any]:
    """
    Extract arguments that appear near an action in the response.
    
    Args:
        response: Full response text
        action: Action name to search near
        
    Returns:
        Dictionary of extracted arguments
    """
    args = {}
    
    # Look for the action in the response
    action_index = response.lower().find(action.lower())
    if action_index == -1:
        return args
    
    # Extract text around the action
    start = max(0, action_index - 200)
    end = min(len(response), action_index + 200)
    context = response[start:end]
    
    # Look for common argument patterns
    arg_patterns = [
        r'content["\s]*:["\s]*["\']([^"\']+)["\']',
        r'project_id["\s]*:["\s]*["\']([^"\']+)["\']',
        r'due_date["\s]*:["\s]*["\']([^"\']+)["\']',
        r'priority["\s]*:["\s]*(\d+)',
        r'description["\s]*:["\s]*["\']([^"\']+)["\']',
        r'labels["\s]*:["\s]*\[([^\]]+)\]'
    ]
    
    for pattern in arg_patterns:
        matches = re.findall(pattern, context, re.IGNORECASE)
        for match in matches:
            if pattern.startswith('priority'):
                args['priority'] = int(match)
            elif pattern.startswith('labels'):
                args['labels'] = [label.strip().strip('"\'') for label in match.split(',')]
            else:
                # Extract the argument name from the pattern
                arg_name = pattern.split('[')[0].split('"')[1]
                args[arg_name] = match
    
    return args

def format_tool_calls_for_display(tool_calls: List[ToolCall]) -> str:
    """
    Format tool calls for human-readable display.
    
    Args:
        tool_calls: List of ToolCall objects
        
    Returns:
        Formatted string representation
    """
    if not tool_calls:
        return "No tool calls detected"
    
    formatted = []
    for i, tool_call in enumerate(tool_calls, 1):
        formatted.append(f"{i}. {tool_call.action}")
        if tool_call.args:
            formatted.append(f"   Args: {json.dumps(tool_call.args, indent=2)}")
        if tool_call.confidence != 1.0:
            formatted.append(f"   Confidence: {tool_call.confidence}")
    
    return "\n".join(formatted)

def validate_tool_call(tool_call: ToolCall) -> bool:
    """
    Validate a tool call structure.
    
    Args:
        tool_call: ToolCall object to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check required fields
        if not tool_call.action or not isinstance(tool_call.action, str):
            return False
        
        if not isinstance(tool_call.args, dict):
            return False
        
        # Check confidence range
        if not (0.0 <= tool_call.confidence <= 1.0):
            return False
        
        return True
        
    except Exception:
        return False 