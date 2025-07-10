setup:
	# Set up Python backend
	cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
	# Set up frontend dependencies
	cd frontend && npm install

dev:
	# Run backend and frontend concurrently
	cd backend && source .venv/bin/activate && uvicorn main:app --reload & \
	cd frontend && npm run dev

backend:
	# Run backend only
	cd backend && source .venv/bin/activate && uvicorn main:app --reload

frontend:
	# Run frontend only
	cd frontend && npm run dev

clean:
	# Clean up generated files
	cd backend && rm -rf .venv
	cd frontend && rm -rf node_modules
	cd frontend && rm -rf build

.PHONY: setup dev backend frontend clean 