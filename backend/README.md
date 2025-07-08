# AI Butler Backend

A FastAPI-based backend for an AI assistant with memory and Todoist integration.

## Features

- **FastAPI Application**: Modern, fast web framework for building APIs
- **GPT-4o Integration**: OpenAI's latest model for intelligent responses
- **User Memory**: Persistent user-specific conversation history and preferences
- **Todoist Integration**: Task management via Model Context Protocol (MCP)
- **Modular Architecture**: Clean separation of concerns with services and utilities

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── api/                    # API layer
│   ├── endpoints.py        # Route definitions
│   └── models.py          # Pydantic models
├── services/              # Business logic
│   ├── chat.py            # Chat processing service
│   ├── memory.py          # User memory management
│   ├── todoist_mcp.py     # Todoist MCP integration
│   └── schema_loader.py   # Tool schema management
├── llm/                   # LLM integration
│   └── openai_client.py   # OpenAI API wrapper
├── utils/                 # Utilities
│   └── parser.py          # Response parsing utilities
├── data/                  # Data storage
│   └── memory_kristofer.json  # Example user memory
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Create a `.env` file with:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   TODOIST_API_TOKEN=your_todoist_api_token_here
   TODOIST_MCP_SERVER_URL=http://localhost:3000
   ```

3. **Run the Application**:
   ```bash
   python main.py
   ```
   
   Or with uvicorn:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

- `GET /`: Health check
- `GET /health`: Health check
- `POST /api/v1/ask`: Main chat endpoint
- `GET /api/v1/memory/{user_id}`: Get user memory

## Usage

### Chat Endpoint

Send a POST request to `/api/v1/ask`:

```json
{
  "user_input": "Add a task to buy groceries tomorrow",
  "user_id": "kristofer",
  "context": {
    "timezone": "America/New_York"
  }
}
```

Response:
```json
{
  "response": "I'll add a task to buy groceries for tomorrow in your Todoist.",
  "user_id": "kristofer",
  "memory_updated": true,
  "tools_used": ["todoist_add_task"],
  "metadata": {
    "tool_calls": [...],
    "context": {...}
  }
}
```

## Development

### Adding New Tools

1. Define the tool schema in `services/schema_loader.py`
2. Implement the tool logic in the appropriate service
3. Add tool execution in `services/chat.py`

### Extending Memory

The memory system stores user preferences and conversation history. Extend the memory structure in `services/memory.py` to add new fields.

### Todoist Integration

The Todoist integration uses Model Context Protocol (MCP). The current implementation includes stubbed functions that can be replaced with actual MCP client calls.

## Architecture Notes

- **Services**: Handle business logic and external integrations
- **API Layer**: Manages HTTP requests/responses and validation
- **LLM Integration**: Wraps OpenAI API with error handling and logging
- **Memory System**: JSON-based persistence with backup functionality
- **Tool System**: Extensible schema-based tool calling

## Future Enhancements

- Database integration for scalable memory storage
- Real-time updates via WebSockets
- Advanced tool chaining and workflow automation
- Multi-modal support (images, documents)
- Enhanced security and authentication 