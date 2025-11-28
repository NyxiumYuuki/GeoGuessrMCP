# Development Guide: GeoGuessr MCP Server

This guide covers multiple ways to develop the GeoGuessr MCP Server using PyCharm, including remote development options.

## Table of Contents

1. [Option 1: PyCharm Remote Development (Gateway)](#option-1-pycharm-remote-development-gateway)
2. [Option 2: PyCharm with Docker Interpreter](#option-2-pycharm-with-docker-interpreter)
3. [Option 3: Dev Containers](#option-3-dev-containers)
4. [Option 4: SSH Remote Interpreter](#option-4-ssh-remote-interpreter)
5. [Running Tests](#running-tests)
6. [Debugging](#debugging)

---

## Option 1: PyCharm Remote Development (Gateway)

**Best for:** Full IDE experience on a remote server with PyCharm Professional.

### Prerequisites
- PyCharm Professional 2023.2+ or JetBrains Gateway
- SSH access to your VPS

### Setup Steps

1. **Install JetBrains Gateway** (or use PyCharm Professional's remote dev feature)
   - Download from: https://www.jetbrains.com/remote-development/gateway/

2. **Connect to your VPS**
   ```
   Gateway → New Connection → SSH
   Host: your-vps-ip
   User: your-username
   Authentication: Key pair or password
   ```

3. **Clone the project on the server**
   ```bash
   ssh user@your-vps
   git clone https://github.com/yourusername/geoguessr-mcp.git
   cd geoguessr-mcp
   ```

4. **Open in Gateway**
   - Select IDE: PyCharm Professional
   - Project directory: `/home/user/geoguessr-mcp`
   - Click "Download and Start IDE"

5. **Configure the environment**
   - Gateway will install a remote IDE backend
   - Set up your Python interpreter (see below)
   - Copy `.env.example` to `.env` and add your cookie

### Configure Python Interpreter in Gateway

1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Add Local Interpreter
3. Select "Virtualenv Environment" → New
4. Location: `/home/user/geoguessr-mcp/.venv`
5. Base interpreter: `/usr/bin/python3.12`
6. Click OK

---

## Option 2: PyCharm with Docker Interpreter

**Best for:** Consistent dev environment, running PyCharm locally with Docker.

### Prerequisites
- PyCharm Professional
- Docker installed locally
- Docker Compose installed

### Setup Steps

1. **Open the project locally in PyCharm**

2. **Build the dev container**
   ```bash
   cd geoguessr-mcp
   docker compose -f .devcontainer/docker-compose.dev.yml build
   ```

3. **Configure Docker Interpreter**
   
   a. File → Settings → Project → Python Interpreter
   
   b. Click the gear icon → Add
   
   c. Select "Docker Compose"
   
   d. Configuration file: `.devcontainer/docker-compose.dev.yml`
   
   e. Service: `dev`
   
   f. Python interpreter: `/usr/local/bin/python`
   
   g. Click OK

4. **Configure Environment Variables**
   
   a. Run → Edit Configurations
   
   b. Select your run configuration
   
   c. Environment variables: Add `GEOGUESSR_NCFA_COOKIE=your_cookie`
   
   Or create a `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env with your cookie
   ```

5. **Run/Debug**
   - Use the run configurations provided in `.idea/runConfigurations/`

### Docker Compose Commands

```bash
# Start dev container
docker compose -f .devcontainer/docker-compose.dev.yml up -d

# View logs
docker compose -f .devcontainer/docker-compose.dev.yml logs -f

# Stop
docker compose -f .devcontainer/docker-compose.dev.yml down

# Rebuild
docker compose -f .devcontainer/docker-compose.dev.yml build --no-cache
```

---

## Option 3: Dev Containers

**Best for:** VS Code users or PyCharm 2024.1+ with Dev Containers support.

### Using VS Code

1. Install the "Dev Containers" extension

2. Open the project folder

3. Click "Reopen in Container" when prompted (or F1 → "Dev Containers: Reopen in Container")

4. VS Code will build and connect to the dev container

### Using PyCharm (2024.1+)

PyCharm 2024.1+ has experimental Dev Containers support:

1. File → Remote Development → Dev Containers

2. Select the `.devcontainer/devcontainer.json` file

3. PyCharm will build and connect to the container

### Manual Container Development

If your IDE doesn't support dev containers natively:

```bash
# Start the dev container
docker compose -f .devcontainer/docker-compose.dev.yml up -d

# Exec into the container
docker exec -it geoguessr-mcp-dev-1 bash

# Inside container: run the server
cd /workspace
python server.py

# Inside container: run tests
pytest -v
```

---

## Option 4: SSH Remote Interpreter

**Best for:** PyCharm Professional users who want to run code directly on VPS.

### Setup Steps

1. **Prepare your VPS**
   ```bash
   ssh user@your-vps
   
   # Install Python 3.12
   sudo apt update
   sudo apt install python3.12 python3.12-venv python3.12-dev
   
   # Clone the project
   git clone https://github.com/yourusername/geoguessr-mcp.git
   cd geoguessr-mcp
   
   # Create virtual environment
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt -r requirements-dev.txt
   ```

2. **Configure PyCharm SSH Interpreter**
   
   a. File → Settings → Project → Python Interpreter
   
   b. Click gear → Add → SSH Interpreter
   
   c. New server configuration:
      - Host: your-vps-ip
      - Username: your-username
      - Authentication: Key pair
   
   d. Next → Interpreter path: `/home/user/geoguessr-mcp/.venv/bin/python`
   
   e. Sync folders:
      - Local: Your local project path
      - Remote: `/home/user/geoguessr-mcp`

3. **Configure deployment**
   
   a. Tools → Deployment → Configuration
   
   b. Add SFTP server
   
   c. Enable automatic upload (Tools → Deployment → Automatic Upload)

---

## Running Tests

### From PyCharm
- Use the "Run Tests" configuration
- Or right-click on `tests/` → Run 'pytest in tests'

### From Command Line

```bash
# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=. --cov-report=html

# Run specific test file
pytest tests/test_server.py -v

# Run only unit tests (skip integration)
pytest -v -m "not integration"

# Run integration tests (requires real cookie)
GEOGUESSR_NCFA_COOKIE=your_real_cookie pytest -v -m integration
```

---

## Debugging

### PyCharm Debugger

1. Set breakpoints by clicking in the gutter

2. Run → Debug 'Debug MCP Server'

3. Use the debugger panel to:
   - Step through code (F8)
   - Step into functions (F7)
   - Evaluate expressions
   - View variables

### Remote Debugging (debugpy)

For debugging in Docker or remote environments:

1. **Modify server.py** to enable debugpy:
   ```python
   import debugpy
   debugpy.listen(("0.0.0.0", 5678))
   print("Waiting for debugger...")
   debugpy.wait_for_client()
   ```

2. **Configure PyCharm Remote Debug**
   
   a. Run → Edit Configurations → Add → Python Debug Server
   
   b. IDE host name: `localhost`
   
   c. Port: `5678`
   
   d. Path mappings:
      - Local: `/path/to/local/project`
      - Remote: `/workspace`

3. **Start debugging**
   - Start the server (it will wait for debugger)
   - Run the "Python Debug Server" configuration in PyCharm
   - Server will continue execution

### Logging

The server uses Python's logging module. Increase verbosity:

```python
# In server.py, change:
logging.basicConfig(level=logging.DEBUG)
```

Or via environment:
```bash
export LOG_LEVEL=DEBUG
python server.py
```

---

## Code Quality

### Format Code

```bash
# Black
black .

# Ruff (lint + fix)
ruff check --fix .
```

### Type Checking

```bash
mypy server.py
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Project Structure

```
geoguessr-mcp/
├── .devcontainer/           # Dev container configuration
│   ├── devcontainer.json
│   ├── docker-compose.dev.yml
│   └── Dockerfile.dev
├── .idea/                   # PyCharm settings
│   └── runConfigurations/
├── tests/                   # Test files
│   ├── __init__.py
│   └── test_server.py
├── server.py                # Main MCP server
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── pyproject.toml          # Project configuration
├── Dockerfile              # Production Dockerfile
├── docker-compose.yml      # Production compose
└── README.md
```

---

## Tips

1. **Hot Reload**: Use `watchfiles` for auto-restart during development:
   ```bash
   pip install watchfiles
   watchfiles "python server.py" .
   ```

2. **Test MCP Connection**: Use the test script:
   ```bash
   python test_server.py http://localhost:8000/mcp
   ```

3. **Environment Variables**: Always use `.env` file locally, never commit secrets

4. **Cookie Expiration**: GeoGuessr cookies expire - if tests start failing, get a fresh cookie