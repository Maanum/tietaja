# Tietäjä Frontend

A React + TypeScript chat interface for the Tietäjä AI assistant.

## Features

- Real-time chat interface with Tietäjä AI
- Message history with user and assistant messages
- Loading states and error handling
- Responsive design with Tailwind CSS
- Auto-scroll to latest messages
- Keyboard shortcuts (Enter to send)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000).

## Usage

- Type your message in the input field at the bottom
- Press Enter or click Send to submit
- The app will show "Tietäjä is thinking..." while processing
- Messages are sent to `http://localhost:8000/api/v1/ask`
- User messages appear on the right (blue)
- Assistant responses appear on the left (white)
- Error messages appear in red

## API Endpoint

The frontend expects the backend to be running at `http://localhost:8000` with the following endpoint:

- `POST /api/v1/ask`
- Body: `{ user_id: "kristofer", user_input: "..." }`
- Response: `{ response: "..." }` or `{ message: "..." }`

## Technologies

- React 18
- TypeScript
- Tailwind CSS
- React Hooks (useState, useEffect, useRef) 