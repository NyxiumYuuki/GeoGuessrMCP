# GeoGuessr MCP Server

A Model Context Protocol (MCP) server for analyzing GeoGuessr game statistics with **automatic API monitoring** and **dynamic schema adaptation**.

## TODO

- [ ] Fix Docker username in compose files and env vars
- [ ] Add authentication to MCP server to allow access only to specific users
- [ ] Fix Code Quality on tests not running
- [ ] Fix Code Quality on black not formatting
- [ ] Add auto monitoring for new endpoints and send notifications by email

## 🌟 Key Features

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

### 3. Connect to Claude

Add to your Claude Desktop configuration:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

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

## 🔐 Authentication

The server supports multiple authentication methods:

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

### Method 1: Build and Push Docker Image

For VPS deployment, it's recommended to build and push your image to Docker Hub:

```bash
# 1. Build the image
docker build -t yourusername/geoguessr-mcp:latest .

# 2. Login to Docker Hub
docker login

# 3. Push the image
docker push yourusername/geoguessr-mcp:latest

# 4. On your VPS, pull and run
docker pull yourusername/geoguessr-mcp:latest
```

### Method 2: Deploy with Docker Compose on VPS

#### Development/Testing Setup

```bash
# Clone repository on VPS
git clone https://github.com/yourusername/geoguessr-mcp.git
cd geoguessr-mcp

# Create .env file
cat > .env << EOF
GEOGUESSR_NCFA_COOKIE=your_cookie_here
DOCKER_USERNAME=yourusername
IMAGE_TAG=latest
EOF

# Deploy
docker compose up -d
```

#### Production Setup with SSL (VPS with nginx-proxy-manager)

If you have an existing nginx-proxy-manager setup (like with Firefly III), you can easily deploy this alongside it:

1. **Build and push your image to Docker Hub:**
```bash
docker build -t yourusername/geoguessr-mcp:latest .
docker push yourusername/geoguessr-mcp:latest
```

2. **Deploy on VPS using the automated script:**
```bash
# On your VPS
cd /geoguessr-mcp
cp .env.production .env
# Edit .env with your DOCKER_USERNAME and GEOGUESSR_NCFA_COOKIE
./deploy.sh
```

3. **Configure SSL in nginx-proxy-manager:**
   - Access admin panel: `http://your-vps-ip:81`
   - Add Proxy Host for your domain
   - Forward to: `geoguessr-mcp-server:8000`
   - Enable SSL with Let's Encrypt

**📖 For detailed VPS deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**

### Method 3: Direct Docker Run

If you prefer not to use Docker Compose:

```bash
# Pull the image
docker pull yourusername/geoguessr-mcp:latest

# Create a volume for schema cache
docker volume create geoguessr-schemas

# Run the container
docker run -d \
  --name geoguessr-mcp \
  --restart unless-stopped \
  -p 8000:8000 \
  -e GEOGUESSR_NCFA_COOKIE=your_cookie \
  -e MONITORING_ENABLED=true \
  -e MONITORING_INTERVAL_HOURS=24 \
  -e LOG_LEVEL=INFO \
  -v geoguessr-schemas:/app/data/schemas \
  yourusername/geoguessr-mcp:latest
```

### Building Multi-Architecture Images

For deployment on different CPU architectures (ARM64, AMD64):

```bash
# Enable buildx
docker buildx create --use

# Build and push multi-arch image
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t yourusername/geoguessr-mcp:latest \
  --push .
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEOGUESSR_NCFA_COOKIE` | - | Default authentication cookie |
| `MCP_PORT` | 8000 | Server port |
| `MCP_TRANSPORT` | streamable-http | MCP transport protocol |
| `MONITORING_ENABLED` | true | Enable API monitoring |
| `MONITORING_INTERVAL_HOURS` | 24 | Monitoring check interval (runs every 24h) |
| `SCHEMA_CACHE_DIR` | /app/data/schemas | Directory for schema persistence |
| `LOG_LEVEL` | INFO | Logging verbosity |
| `DOCKER_USERNAME` | yourusername | Your Docker Hub username (for compose files) |
| `IMAGE_TAG` | latest | Docker image tag |

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