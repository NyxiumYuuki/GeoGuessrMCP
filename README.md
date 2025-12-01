# GeoGuessr MCP Server

A Model Context Protocol (MCP) server for analyzing GeoGuessr game statistics with **automatic API monitoring** and **dynamic schema adaptation**.

## TODO

- [x] ~~Fix Docker username in compose files and env vars~~
- [x] ~~Add authentication to MCP server to allow access only to specific users~~
- [ ] Fix Code Quality on tests not running
- [ ] Fix Code Quality on black not formatting
- [ ] Add auto monitoring for new endpoints and send notifications by email

## 🌟 Key Features

### Multi-User Support
- **Independent Sessions**: Each API key gets its own GeoGuessr session
- **Multiple Accounts**: Different users can access their own GeoGuessr accounts
- **Single Server**: No need to deploy separate instances per user
- **Automatic Context**: User sessions are automatically managed per request

### Dynamic API Monitoring
- **Automatic endpoint discovery**: Monitors GeoGuessr API endpoints daily
- **Schema change detection**: Automatically detects when API response formats change
- **Self-adapting**: Updates internal data models based on actual API responses
- **No hardcoded assumptions**: Works even when GeoGuessr changes their API

### Comprehensive Analysis
- Profile and statistics retrieval
- Game history and round-by-round analysis
- Performance tracking and trend detection
- Strategy recommendations based on gameplay patterns

### Easy Deployment
- Docker Compose for simple VPS deployment
- Production-ready with nginx and SSL support
- Persistent schema caching between restarts

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- A GeoGuessr account

### 1. Clone and Configure

```bash
git clone https://github.com/NyxiumYuuki/GeoGuessrMCP.git
cd GeoGuessrMCP
cp .env.example .env
```

### 2. Deploy

```bash
docker compose up -d --build
```

That's it! The server is now running on port 8000.

### 3. Configure MCP Server Authentication (Optional)

To secure your MCP server with API key authentication, edit `.env`:

```bash
MCP_AUTH_ENABLED=true
MCP_API_KEYS=your-secure-api-key-here
```

Generate a secure API key:
```bash
openssl rand -hex 32
```

### 4. Connect to Claude

Add to your Claude Desktop configuration:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**Without Authentication:**
```json
{
  "mcpServers": {
    "geoguessr": {
      "type": "streamable-http",
      "url": "http://YOUR_VPS_IP:8000/mcp"
    }
  }
}
```

**With Authentication:**
```json
{
  "mcpServers": {
    "geoguessr": {
      "type": "streamable-http",
      "url": "http://YOUR_VPS_IP:8000/mcp",
      "headers": {
        "Authorization": "Bearer your-secure-api-key-here"
      }
    }
  }
}
```

## 🔐 Authentication

The server supports two types of authentication with **multi-user support**:

### MCP Server Authentication (Controls Access to the MCP Server)

Secures who can connect to your MCP server. When enabled, clients must provide a valid API key.

**Multi-User Support:** Each API key can have its own GeoGuessr session, allowing multiple users to use the same MCP server instance with their own accounts!

**Enable in `.env`:**
```bash
MCP_AUTH_ENABLED=true
MCP_API_KEYS=key1,key2,key3  # Comma-separated for multiple users
```

**Generate secure keys:**
```bash
openssl rand -hex 32
```

**Configure Claude Desktop with authentication:**
```json
{
  "mcpServers": {
    "geoguessr": {
      "type": "streamable-http",
      "url": "https://your-domain.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

**Multi-User Example:**
```bash
# Give each user their own API key
MCP_API_KEYS=alice_key_abc123,bob_key_def456,charlie_key_ghi789

# Alice connects with Authorization: Bearer alice_key_abc123
# Bob connects with Authorization: Bearer bob_key_def456
# Each can login to their own GeoGuessr account!
```

### GeoGuessr API Authentication (Access GeoGuessr Data)

The server also needs authentication to access GeoGuessr's API. In multi-user mode, **each API key holder can login to their own GeoGuessr account:**

### Option 1: Login via Claude (Recommended)
Simply ask Claude:
> "Login to GeoGuessr with email: myemail@example.com and password: mypassword"

### Option 2: Environment Variable
Add to your `.env` file:
```bash
GEOGUESSR_NCFA_COOKIE=your_cookie_value_here
```

### Option 3: Manual Cookie
Use the `set_ncfa_cookie` tool with a cookie extracted from your browser.

## 👥 Multi-User Mode

The server supports multiple users, each with their own GeoGuessr account, using a single MCP server instance.

### How It Works

1. **API Keys**: Each user gets a unique API key
2. **Independent Sessions**: Each API key has its own GeoGuessr login session
3. **Automatic Routing**: The server automatically routes requests to the correct user's session
4. **No Interference**: Users don't affect each other's sessions

### Setup Example

**1. Configure Multiple API Keys:**
```bash
# .env file
MCP_AUTH_ENABLED=true
MCP_API_KEYS=alice_key,bob_key,charlie_key
```

**2. Restart Server:**
```bash
# Development
docker compose restart

# Production
docker compose -f docker-compose.prod.yml restart
```

**3. Each User Connects:**
```json
// Alice's Claude Desktop config
{
  "mcpServers": {
    "geoguessr": {
      "url": "https://your-domain.com/mcp",
      "headers": {"Authorization": "Bearer alice_key"}
    }
  }
}

// Bob's Claude Desktop config
{
  "mcpServers": {
    "geoguessr": {
      "url": "https://your-domain.com/mcp",
      "headers": {"Authorization": "Bearer bob_key"}
    }
  }
}
```

**4. Each User Logs In:**
- Alice asks Claude: "Login to GeoGuessr with my credentials"
- Bob asks Claude: "Login to GeoGuessr with my credentials"
- Sessions are completely independent!

### Adding New Users

To add a new user to an existing deployment:

1. Edit `.env` and add the new API key to `MCP_API_KEYS`
2. Restart the server: `docker compose restart`
3. Share the new API key with the user
4. User configures their Claude Desktop with the API key
5. User logs in to their GeoGuessr account via Claude

**The server restarts in ~2-3 seconds** and all existing users remain logged in!

## 📊 Available Tools

### Authentication
| Tool | Description |
|------|-------------|
| `login` | Authenticate with email/password |
| `logout` | End current session |
| `set_ncfa_cookie` | Set authentication cookie manually |
| `get_auth_status` | Check authentication status |

### Profile & Stats
| Tool | Description |
|------|-------------|
| `get_my_profile` | Get your profile information |
| `get_my_stats` | Get your game statistics |
| `get_extended_stats` | Get additional statistics |
| `get_achievements` | Get your achievements |
| `get_comprehensive_profile` | Get combined profile data |

### Games & Activity
| Tool | Description |
|------|-------------|
| `get_activity_feed` | Get recent activity |
| `get_recent_games` | Get recent games with details |
| `get_game_details` | Get specific game information |
| `get_season_stats` | Get competitive season stats |
| `get_daily_challenge` | Get daily challenge info |

### Analysis
| Tool | Description |
|------|-------------|
| `analyze_recent_games` | Analyze performance trends |
| `get_performance_summary` | Comprehensive performance overview |
| `get_strategy_recommendations` | Get personalized improvement tips |

### API Monitoring
| Tool | Description |
|------|-------------|
| `check_api_status` | Check all endpoint availability |
| `get_endpoint_schema` | Get schema for specific endpoint |
| `list_available_endpoints` | List all known endpoints |
| `explore_endpoint` | Discover new API endpoints |

## 🔄 Dynamic Schema System

The server automatically adapts to API changes:

```
┌─────────────────────┐      ┌──────────────────┐
│   API Response      │ ───▶ │  Schema Detector │
└─────────────────────┘      └────────┬─────────┘
                                      │
                                      ▼
┌─────────────────────┐      ┌──────────────────┐
│  Schema Registry    │ ◀─── │  Compare Hash    │
│  (Persisted)        │      └──────────────────┘
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Dynamic Response   │ ───▶ Available to LLM
│  with Schema Info   │
└─────────────────────┘
```

### How It Works

1. **Daily Monitoring**: The server checks all known endpoints every 24 hours
2. **Schema Detection**: Analyzes response structure, field types, and nesting
3. **Change Detection**: Computes schema hash to detect modifications
4. **Persistence**: Schemas are cached to disk and survive restarts
5. **Dynamic Access**: Tools return data with schema information for the LLM

### Example: Exploring Unknown Endpoints

```
User: "Can you explore the /v3/some-new-endpoint API?"

Claude uses explore_endpoint tool:
{
  "success": true,
  "discovered_fields": ["id", "name", "data", "timestamp"],
  "schema_description": "Endpoint: /v3/some-new-endpoint\nFields:\n  - id: string\n  - name: string\n  - data: object\n  - timestamp: datetime"
}
```

## 🏭 Production Deployment

The server is available as a pre-built Docker image: **`nyxiumyuuki/geoguessr-mcp:latest`**

### Method 1: Quick Deploy with Script

For VPS deployment with existing nginx-proxy-manager:

```bash
# Clone repository on VPS
git clone https://github.com/NyxiumYuuki/GeoGuessrMCP.git
cd GeoGuessrMCP

# Configure environment
cp .env.example .env
# Edit .env with your settings:
# - GEOGUESSR_NCFA_COOKIE (for GeoGuessr API access)
# - MCP_AUTH_ENABLED=true (optional, for MCP server security)
# - MCP_API_KEYS (if authentication enabled)

# Run deployment script
./scripts/deploy.sh
```

### Method 2: Manual Docker Compose Deploy

#### Development/Testing Setup

```bash
# Using docker-compose.yml (development)
docker compose up -d
```

#### Production Setup with nginx-proxy-manager

```bash
# Using docker-compose.prod.yml (production)
docker compose -f docker-compose.prod.yml up -d
```

**Configure SSL in nginx-proxy-manager:**
- Access admin panel: `http://your-vps-ip:81`
- Add Proxy Host for your domain
- Forward to: `geoguessr-mcp-server:8000`
- Enable SSL with Let's Encrypt

**📖 For detailed VPS deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**

### Method 3: Direct Docker Run

If you prefer not to use Docker Compose:

```bash
# Pull the image
docker pull nyxiumyuuki/geoguessr-mcp:latest

# Create a volume for schema cache
docker volume create geoguessr-schemas

# Run the container (without authentication)
docker run -d \
  --name geoguessr-mcp \
  --restart unless-stopped \
  -p 8000:8000 \
  -e GEOGUESSR_NCFA_COOKIE=your_cookie \
  -e MCP_AUTH_ENABLED=false \
  -e MONITORING_ENABLED=true \
  -e MONITORING_INTERVAL_HOURS=24 \
  -e LOG_LEVEL=INFO \
  -v geoguessr-schemas:/app/data/schemas \
  nyxiumyuuki/geoguessr-mcp:latest

# Run with MCP authentication enabled
docker run -d \
  --name geoguessr-mcp \
  --restart unless-stopped \
  -p 8000:8000 \
  -e GEOGUESSR_NCFA_COOKIE=your_cookie \
  -e MCP_AUTH_ENABLED=true \
  -e MCP_API_KEYS=your-api-key-1,your-api-key-2 \
  -e MONITORING_ENABLED=true \
  -e MONITORING_INTERVAL_HOURS=24 \
  -e LOG_LEVEL=INFO \
  -v geoguessr-schemas:/app/data/schemas \
  nyxiumyuuki/geoguessr-mcp:latest
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEOGUESSR_NCFA_COOKIE` | - | GeoGuessr API authentication cookie |
| `MCP_AUTH_ENABLED` | false | Enable MCP server authentication |
| `MCP_API_KEYS` | - | Comma-separated API keys for MCP access |
| `MCP_PORT` | 8000 | Server port |
| `MCP_TRANSPORT` | streamable-http | MCP transport protocol |
| `MONITORING_ENABLED` | true | Enable API monitoring |
| `MONITORING_INTERVAL_HOURS` | 24 | Monitoring check interval (runs every 24h) |
| `SCHEMA_CACHE_DIR` | /app/data/schemas | Directory for schema persistence |
| `LOG_LEVEL` | INFO | Logging verbosity |

## 🧪 Development

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest -v

# Run server locally
python -m geoguessr_mcp.main
```

### Project Structure

```
geoguessr-mcp/
├── src/geoguessr_mcp/
│   ├── api/              # API client and endpoints
│   ├── auth/             # Authentication
│   ├── models/           # Data models
│   ├── monitoring/       # Schema detection & monitoring
│   ├── services/         # Business logic
│   ├── tools/            # MCP tool definitions
│   ├── config.py         # Configuration
│   └── main.py           # Entry point
├── tests/
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── nginx/                # Production nginx config
├── docker-compose.yml    # Development deployment
├── docker-compose.prod.yml # Production deployment
└── Dockerfile
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details.

## ⚠️ Disclaimer

This project uses the unofficial GeoGuessr API which may change without notice. The dynamic schema system helps mitigate this, but some features may break if GeoGuessr makes significant API changes.

This project is not affiliated with GeoGuessr AB.