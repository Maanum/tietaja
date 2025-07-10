# Tietäjä

Tietäjä is an AI-powered personal assistant that combines chat functionality with memory management and task integration. The project consists of a Python FastAPI backend and a React TypeScript frontend.

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tietaja
   ```

2. **Set up the development environment**
   ```bash
   make setup
   ```

3. **Launch the development servers**
   ```bash
   make dev
   ```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Environment Requirements

- **Python 3.9+** - Required for the FastAPI backend
- **Node.js** - Required for the React frontend (recommend using [Volta](https://volta.sh/) for version management)
- **make** - Required for the build automation

## Environment Variables

### Backend Setup

1. Copy the example environment file:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

## Development Commands

- `make setup` - Install all dependencies for both backend and frontend
- `make dev` - Run both backend and frontend in development mode
- `make backend` - Run only the backend server
- `make frontend` - Run only the frontend development server
- `make clean` - Remove all generated files and dependencies

## Project Structure

```
tietaja/
├── backend/          # FastAPI backend
│   ├── api/         # API endpoints and models
│   ├── services/    # Business logic services
│   ├── data/        # Data storage
│   └── main.py      # Application entry point
├── frontend/        # React TypeScript frontend
│   ├── src/         # Source code
│   └── public/      # Static assets
├── Makefile         # Build automation
└── README.md        # This file
```

## Features

- **AI Chat Interface** - Interactive chat with OpenAI models
- **Memory Management** - Persistent conversation history
- **Task Integration** - Todoist integration for task management
- **Modern UI** - Clean, responsive React interface
- **FastAPI Backend** - High-performance Python API 