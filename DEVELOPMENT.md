# Development Guide

This guide covers local development setup, testing, and debugging the GeoGuessr MCP Server.

## Table of Contents

- [Development Setup](#development-setup)
- [Running Locally](#running-locally)
- [Testing with MCP Inspector](#testing-with-mcp-inspector)
- [Testing with Claude Desktop](#testing-with-claude-desktop)
- [Running Tests](#running-tests)
- [Code Quality](#code-quality)
- [Debugging](#debugging)
- [Common Issues](#common-issues)

## Development Setup

### Prerequisites

- Python 3.11 or higher
- `uv` (recommended) or `pip`
- Git
- A GeoGuessr account (for authenticated endpoints)

### 1. Clone the Repository

```bash
git clone https://github.com/NyxiumYuuki/GeoGuessrMCP.git
cd GeoGuessrMCP
```

### 2. Create Virtual Environment

**Using uv (recommended):**
```bash
uv venv
source .venv/bin/activate  # On Linux/macOS
# OR
.venv\Scripts\activate  # On Windows
```

**Using venv:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Linux/macOS
# OR
.venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

**Development dependencies (includes testing tools):**
```bash
uv pip install -e ".[dev]"
# OR
pip install -e ".[dev]"
```

**Production dependencies only:**
```bash
uv pip install -e .
# OR
pip install -e .
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and configure:

**Required for authenticated endpoints:**
```bash
GEOGUESSR_NCFA_COOKIE=your_cookie_here
```

**Optional development settings:**
```bash
# Disable authentication for local testing
MCP_AUTH_ENABLED=false

# Enable debug logging
LOG_LEVEL=DEBUG

# Local schema cache
SCHEMA_CACHE_DIR=./data/schemas

# Server configuration
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_TRANSPORT=streamable-http
```

## Running Locally

### Start the Server

```bash
python -m src.geoguessr_mcp.main
```

The server will start on `http://0.0.0.0:8000` by default.

**Expected output:**
```
INFO - Starting GeoGuessr MCP Server on 0.0.0.0:8000 with streamable-http transport
INFO - MCP server authentication is DISABLED - server is publicly accessible
INFO - Started server process [12345]
INFO - Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Enable Debug Logging

Set `LOG_LEVEL=DEBUG` in `.env` to see detailed request/response logs:

```bash
LOG_LEVEL=DEBUG
```

This enables:
- Request method and path logging
- Request headers logging
- Authentication flow details
- MCP protocol messages
- Schema detection changes

## Testing with MCP Inspector

**MCP Inspector** is a web-based tool for testing MCP servers interactively. It's the recommended way to develop and debug MCP servers.

### 1. Install MCP Inspector

Download from: [https://github.com/modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector)

Or run with npx:
```bash
npx @modelcontextprotocol/inspector
```

MCP Inspector will start on `http://localhost:6274` by default.

### 2. Configure Connection

#### Without Authentication

In MCP Inspector:
1. Select **"Server-Sent Events (SSE)"** or **"Streamable HTTP"** transport
2. Set URL: `http://localhost:8000/mcp`
3. Click **"Connect"**

#### With Authentication

In MCP Inspector:
1. Select **"Streamable HTTP"** transport
2. Set URL: `http://localhost:8000/mcp`
3. Click **"Custom Headers"**
4. Add header:
   - **Name:** `Authorization`
   - **Value:** `Bearer YOUR_API_KEY`
5. Click **"Connect"**

**Generate API key:**
```bash
openssl rand -hex 32
```

Add to `.env`:
```bash
MCP_AUTH_ENABLED=true
MCP_API_KEYS=your-generated-key-here
```

### 3. Test the Connection

After connecting, you should see:
- ✅ **Connection Status:** Connected
- ✅ **Protocol Version:** 2025-06-18
- ✅ **Server Info:** GeoGuessr MCP v1.22.0

### 4. Explore Available Tools

In the **"Tools"** tab, you should see:

**Authentication Tools:**
- `login(email, password)` - Login with GeoGuessr credentials
- `logout()` - Logout current session
- `set_ncfa_cookie(cookie)` - Set authentication cookie manually
- `get_current_session_token()` - Get current session status

**Profile Tools:**
- `get_profile(username)` - Get user profile
- `get_current_user_profile()` - Get your profile
- `get_user_stats(user_id)` - Get detailed stats

**Game Tools:**
- `get_game(game_id)` - Get game details
- `get_recent_games(count)` - Get recent games
- `get_activity_feed(count)` - Get activity feed

**Analysis Tools:**
- `get_performance_summary()` - Comprehensive performance overview
- `analyze_recent_games(count)` - Analyze recent gameplay
- `get_strategy_recommendations()` - Get improvement tips

**Monitoring Tools:**
- `check_api_status()` - Check API endpoint availability
- `list_available_endpoints()` - List all monitored endpoints
- `get_endpoint_schema(path)` - Get schema for specific endpoint
- `explore_endpoint(path)` - Manually explore new endpoints

### 5. Test a Tool

Try calling a simple tool:

1. Select `get_current_session_token()` from the tools list
2. Click **"Call Tool"**
3. Check the response

**Expected response (not authenticated):**
```json
{
  "has_token": false,
  "message": "No authentication cookie set. Use login() or set_ncfa_cookie()."
}
```

**Expected response (authenticated):**
```json
{
  "has_token": true,
  "user_id": "your-user-id",
  "username": "your-username"
}
```

### 6. Debugging Connection Issues

If you see errors in MCP Inspector, check the server logs:

**Common issues:**

**❌ OPTIONS 405 Method Not Allowed**
- **Cause:** CORS middleware not configured
- **Fix:** Ensure middleware is properly applied (should be fixed in latest version)

**❌ POST 401 Unauthorized**
- **Cause:** Missing or invalid API key
- **Fix:** Add correct `Authorization: Bearer YOUR_KEY` header

**❌ POST 400 Bad Request**
- **Cause:** Session ID not maintained (CORS headers not exposed)
- **Fix:** Ensure `expose_headers` includes `mcp-session-id` (should be fixed in latest version)

**❌ Connection timeout**
- **Cause:** Server not running or firewall blocking
- **Fix:** Check server is running on `localhost:8000`

## Testing with Claude Desktop

For testing the full MCP integration with Claude Desktop:

### 1. Configure Claude Desktop

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**Without authentication:**
```json
{
  "mcpServers": {
    "geoguessr-local": {
      "type": "streamable-http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**With authentication:**
```json
{
  "mcpServers": {
    "geoguessr-local": {
      "type": "streamable-http",
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

### 2. Restart Claude Desktop

After modifying the config, completely quit and restart Claude Desktop.

### 3. Test in Claude

In a new conversation:

```
Can you check my GeoGuessr profile?
```

Claude should automatically use the MCP server tools to fetch your profile.

## Running Tests

### Unit Tests

```bash
pytest src/tests/unit/ -v
```

### Integration Tests

**Requires authentication:**
```bash
# Set GEOGUESSR_NCFA_COOKIE in .env first
pytest src/tests/integration/ -v
```

### All Tests with Coverage

```bash
pytest --cov=src/geoguessr_mcp src/tests/ -v
```

### Coverage Report

```bash
pytest --cov=src/geoguessr_mcp --cov-report=html src/tests/
open htmlcov/index.html  # View coverage report
```

## Code Quality

### Format Code with Black

```bash
black src/ tests/
```

**Configuration:** Line length 100 (see `pyproject.toml`)

### Lint with Ruff

```bash
ruff check src/ tests/
```

**Auto-fix:**
```bash
ruff check --fix src/ tests/
```

### Type Check with MyPy

```bash
mypy src/
```

### Pre-commit Hooks

Install pre-commit hooks to automatically run checks:

```bash
pre-commit install
```

This will run Black, Ruff, and MyPy before each commit.

## Debugging

### Enable Debug Mode

Set in `.env`:
```bash
LOG_LEVEL=DEBUG
```

Restart the server to see:
- All HTTP requests with headers
- Authentication flow
- MCP protocol messages
- Schema detection and changes

### Debug Authentication

Check if your GeoGuessr cookie is valid:

```bash
# In Python console
from src.geoguessr_mcp.auth import session_manager
import asyncio

async def test():
    token = session_manager.get_current_session_token()
    print(f"Token: {token}")

asyncio.run(test())
```

### Debug API Calls

Test API endpoints directly:

```bash
# Install httpx
pip install httpx

# Test endpoint
python -c "
import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://www.geoguessr.com/api/v3/profiles',
            cookies={'_ncfa': 'YOUR_COOKIE'}
        )
        print(response.json())

asyncio.run(test())
"
```

### Debug Schema Detection

Check schema cache:

```bash
ls -la data/schemas/
cat data/schemas/schemas.json | python -m json.tool
```

Force schema refresh:

```bash
rm -rf data/schemas/*
# Restart server - schemas will be regenerated
```

### View Server Logs

**Real-time logs:**
```bash
tail -f server.log  # If using file logging
```

**Docker logs:**
```bash
docker compose logs -f geoguessr-mcp
```

## Common Issues

### Issue: Module not found errors

**Solution:**
```bash
# Ensure you're in the project root
pip install -e ".[dev]"
```

### Issue: Permission denied on schema cache

**Solution:**
```bash
mkdir -p data/schemas
chmod 755 data/schemas
```

Or use a different path in `.env`:
```bash
SCHEMA_CACHE_DIR=/tmp/geoguessr-schemas
```

### Issue: Port 8000 already in use

**Solution:**
```bash
# Use different port
echo "MCP_PORT=8001" >> .env
```

Or kill the process using port 8000:
```bash
# Linux/macOS
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue: CORS errors in browser

**Solution:**
Ensure CORS middleware is properly configured with `expose_headers`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id", "mcp-protocol-version"],
)
```

### Issue: Session not maintained (400 errors)

**Symptoms:**
- First POST succeeds (200 OK)
- Second POST fails (400 Bad Request)
- Logs show new session created each time

**Solution:**
The `mcp-session-id` header must be exposed via CORS (fixed in latest version).

Check server logs for:
```
expose_headers=["mcp-session-id", "mcp-protocol-version"]
```

## Contributing

### Development Workflow

1. Create a feature branch
2. Make changes
3. Run tests: `pytest`
4. Run code quality checks: `black`, `ruff`, `mypy`
5. Commit with descriptive message
6. Push and create pull request

### Code Style

- **Formatting:** Black (line length 100)
- **Linting:** Ruff
- **Type hints:** Required for all functions
- **Docstrings:** Google style for public APIs
- **Tests:** Required for new features

### Project Structure

```
src/geoguessr_mcp/
├── api/              # GeoGuessr API client
├── auth/             # Authentication & session management
├── middleware/       # MCP server middleware (auth, CORS)
├── models/           # Data models (Profile, Stats, Games)
├── monitoring/       # API monitoring & schema detection
│   ├── endpoint/     # Endpoint monitoring
│   └── schema/       # Schema detection & registry
├── services/         # Business logic services
├── tools/            # MCP tool definitions
├── config.py         # Configuration management
└── main.py           # Application entry point
```

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [FastMCP Guide](https://github.com/jlowin/fastmcp)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [GeoGuessr API (unofficial)](https://www.geoguessr.com/api)
- [Starlette Middleware](https://www.starlette.io/middleware/)

## Support

For issues and questions:
- Check this guide first
- Review server logs with `LOG_LEVEL=DEBUG`
- Check existing issues on GitHub
- Create a new issue with logs and reproduction steps
