.PHONY: help install build test run-backend run-frontend run cli clean docker-build docker-up docker-down

help:
	@echo "ValiCrypt Developer Automation Commands"
	@echo "---------------------------------------"
	@echo "make install       Install frontend and backend dependencies"
	@echo "make build         Build frontend production SPA"
	@echo "make test          Run automated test suite (pytest)"
	@echo "make run           Run full-stack server (FastAPI serves API + built frontend)"
	@echo "make run-backend   Run uvicorn backend in reload mode"
	@echo "make run-frontend  Run Vite dev server for frontend development"
	@echo "make cli           Show ValiCrypt CLI usage"
	@echo "make docker-build  Build production Docker container"
	@echo "make docker-up     Start Docker Compose stack"
	@echo "make docker-down   Stop Docker Compose stack"
	@echo "make clean         Remove temp files and test caches"

install:
	@echo "Installing backend dependencies..."
	pip install -r backend/requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

build:
	@echo "Building frontend production bundle..."
	cd frontend && npm run build

test:
	@echo "Running full test suite..."
	./scripts/run_tests.sh

run: build
	@echo "Starting full-stack application on http://localhost:8000..."
	./scripts/run_backend.sh

run-backend:
	./scripts/run_backend.sh

run-frontend:
	./scripts/run_frontend.sh

cli:
	./bin/valicrypt --help

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	rm -rf backend/.pytest_cache frontend/dist frontend/node_modules/.vite /tmp/mediavault mediavault.db
	find . -type d -name "__pycache__" -exec rm -rf {} +
