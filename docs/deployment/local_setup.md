# Local Development Setup

Step-by-step guide for setting up ArmPilot-AI for local development.

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.10+ | `python3 --version` |
| pip | 22+ | `pip3 --version` |
| Node.js | 18+ | `node --version` |
| pnpm | 8+ | `pnpm --version` |
| Git | 2+ | `git --version` |

## Quick Setup

```bash
# Clone the repository
git clone https://github.com/krrishyaduka/ArmPilot-AI.git
cd ArmPilot-AI

# Run the automated setup script
bash scripts/setup.sh
```

The setup script will:
1. Check prerequisites (Python, pip, Node.js)
2. Install Python dependencies from `backend/requirements.txt`
3. Create `.env` from `.env.example`
4. Create `models/`, `data/`, `reports/`, `logs/` directories
5. Install frontend dependencies (if pnpm is available)
6. Verify the installation

## Manual Setup

### 1. Python Backend

```bash
cd backend

# Create virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy example env
cp .env.example .env

# Edit with your settings
vim .env
```

Key settings to review:

```bash
ARMPILOT_HOST=127.0.0.1
ARMPILOT_PORT=8000
ARMPILOT_DEBUG=true
ARMPILOT_LOG_LEVEL=DEBUG
```

### 3. Frontend (Optional)

```bash
cd frontend
pnpm install
```

### 4. Place Model Files

Download a GGUF model and place it in `models/`:

```bash
# Example: TinyLlama 1.1B
wget -P models/ https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### 5. Start Development Server

```bash
# Backend (with auto-reload)
bash scripts/run_server.sh

# Or manually with reload
cd backend
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 6. Verify

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

## Frontend Development

```bash
cd frontend
pnpm dev
```

The Vite dev server runs on port 8443 with hot reload.

## Development Workflow

1. Start backend: `bash scripts/run_server.sh`
2. Start frontend: `cd frontend && pnpm dev`
3. Open API docs: http://localhost:8000/docs
4. Open dashboard: http://localhost:8443

## IDE Configuration

### VS Code

Recommended extensions:
- Python
- Pylance
- Tailwind CSS IntelliSense
- ESLint

Settings (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": "backend/.venv/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "editor.formatOnSave": true
}
```

## Running Tests

```bash
# Run all tests
bash scripts/test_all.sh

# Or with pytest
cd backend
python3 -m pytest tests/ -v
```

## Common Issues

### "Model not found"

Place `.gguf` files in the `models/` directory. The model ID is derived from the filename.

### "Runtime not available"

Install llama-cpp-python with ARM64 support:

```bash
pip install llama-cpp-python --no-cache-dir
```

### Port already in use

Change the port in `.env`:

```bash
ARMPILOT_PORT=8001
```
