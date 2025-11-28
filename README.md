# GeoGuessr MCP Server

A Model Context Protocol (MCP) server for analyzing your GeoGuessr account data. This server allows Claude AI to access and analyze your GeoGuessr statistics, game history, achievements, and more.

## Authentication Options

The server supports **three authentication methods**:

1. **Login with credentials** (Recommended) - Use the `login` tool with your GeoGuessr email and password
2. **Manual cookie** - Use the `set_ncfa_cookie` tool with a cookie extracted from your browser
3. **Environment variable** - Set `GEOGUESSR_NCFA_COOKIE` for server-wide default authentication

### Using Login (Easiest)

Simply ask Claude to login:
```
"Login to GeoGuessr with email: myemail@example.com and password: mypassword"
```

The server will authenticate with GeoGuessr and create a session. Your credentials are only used once to obtain an authentication token - they are **not stored** on the server.

### Security Notes

- Credentials are sent directly to GeoGuessr's official API over HTTPS
- Session tokens are stored in memory only (lost on server restart)
- For persistent authentication, use the environment variable method
- Always use HTTPS in production to protect credentials in transit

## Features

### Authentication Tools
- **login** - Authenticate with email/password
- **logout** - End the current session
- **set_ncfa_cookie** - Set authentication cookie manually
- **set_session_token** - Restore a previous session
- **get_auth_status** - Check current authentication status

### Profile & Stats
- **get_my_profile** - Get your user profile information
- **get_my_stats** - Get detailed statistics displayed on your profile
- **get_extended_stats** - Get additional stats not shown on profile
- **get_my_achievements** - Get all your achievements
- **get_my_trophies** - Get your trophy collection
- **get_trophy_case** - Get your displayed trophy case

### Games & Activity
- **get_activity_feed** - Get recent activity (games, achievements, etc.)
- **get_game_details** - Get detailed info about a specific game
- **get_unfinished_games** - Get games you haven't completed
- **get_streak_game** - Get country streak game details
- **analyze_recent_games** - Analyze your recent games with statistics

### Competitive Modes
- **get_battle_royale_game** - Get Battle Royale game stats
- **get_duel_game** - Get duel game information
- **get_game_lobby** - Get lobby info with player stats
- **get_current_season_stats** - Get current season statistics
- **get_season_game_info** - Get season info for specific game modes
- **get_tournaments** - Get tournament information

### Challenges
- **get_daily_challenge** - Get today's or previous daily challenges
- **get_challenge_details** - Get details about a specific challenge

### Social
- **get_friends** - Get your friends list
- **get_friends_summary** - Get friends with requests and recommendations
- **get_notifications** - Get your notifications
- **search_user** - Search for other players

### Maps
- **get_my_maps** - Get maps you've created
- **get_liked_maps** - Get maps you've liked
- **get_map_info** - Get info about any map
- **get_popular_maps** - Get popular/featured/official maps
- **get_personalized_maps** - Get map recommendations
- **get_map_scores** - Get high scores for a map

### Explorer & Progress
- **get_explorer_progress** - Get your explorer mode progress
- **get_objectives** - Get current objectives
- **get_unclaimed_objectives** - Get rewards to claim
- **get_unclaimed_badges** - Get badges to claim

### Analysis
- **get_performance_summary** - Get comprehensive performance overview

## Prerequisites

- Docker and Docker Compose installed on your VPS
- A GeoGuessr account (Pro subscription recommended for full API access)
- Your GeoGuessr `_ncfa` authentication cookie

## Quick Start

### 1. Clone or copy the files to your VPS

```bash
mkdir -p ~/geoguessr-mcp
cd ~/geoguessr-mcp
# Copy all the files here
```

### 2. Build and run (no configuration required!)

```bash
docker compose up -d --build
```

That's it! The server now supports login via credentials, so you don't need to configure anything upfront.

### 3. (Optional) Configure default authentication

If you want server-wide default authentication without logging in each time:

#### Option A: Get your GeoGuessr authentication cookie

1. Log in to [GeoGuessr](https://www.geoguessr.com) in your browser
2. Open Developer Tools (F12 or Ctrl+Shift+I)
3. Go to the **Application** tab (Chrome) or **Storage** tab (Firefox)
4. Under **Cookies**, find `www.geoguessr.com`
5. Look for the cookie named `_ncfa`
6. Copy its value

```bash
cp .env.example .env
nano .env  # Add your cookie
```

```env
GEOGUESSR_NCFA_COOKIE=your_actual_cookie_value_here
```

#### Option B: Just use login when connected

When connected to Claude, simply say:
> "Login to GeoGuessr with my email and password"

Claude will prompt you for credentials and authenticate.

### 4. Restart if you added environment variables

```bash
docker compose up -d --build
```

### 5. Verify it's running

```bash
docker compose logs -f
```

You should see:
```
Starting GeoGuessr MCP Server on 0.0.0.0:8000 with streamable-http transport
```

## Connecting to Claude

### Claude Desktop (macOS/Windows)

Add to your Claude Desktop configuration file:

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

### VS Code with Copilot

1. Open VS Code
2. Run the command: `MCP: Add Server`
3. Choose "HTTP (Streamable HTTP)" as the transport
4. Enter URL: `http://YOUR_VPS_IP:8000/mcp`

### Claude.ai (if MCP support is enabled)

Add the server through Claude.ai's integrations settings with:
- URL: `http://YOUR_VPS_IP:8000/mcp`
- Transport: Streamable HTTP

## Using with Claude

Once connected, you can ask Claude questions like:

**First, authenticate (if not using environment variable):**
- "Login to GeoGuessr with email: myemail@example.com password: mypassword"
- "Check my GeoGuessr authentication status"

**Then analyze your data:**
- "Show me my GeoGuessr profile and stats"
- "Analyze my last 10 games and tell me how I'm doing"
- "What achievements have I unlocked?"
- "How am I doing in the current competitive season?"
- "Show me my activity feed from the last week"
- "What maps have I liked?"
- "Search for a player named [username]"
- "Get the details of my last Battle Royale game"

**When done (optional):**
- "Logout from GeoGuessr"

## Production Deployment

### Adding SSL with Nginx (Recommended)

For production, you should add SSL. Create an `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream mcp_server {
        server geoguessr-mcp:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        location / {
            proxy_pass http://mcp_server;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 86400;
        }
    }
}
```

### Adding API Key Authentication

For additional security, you can add API key authentication. Modify the server.py to check for an `x-api-key` header.

### Firewall Configuration

```bash
# Allow only specific IPs or use a firewall
sudo ufw allow from YOUR_IP to any port 8000
```

## Troubleshooting

### "GEOGUESSR_NCFA_COOKIE environment variable not set"

Make sure your `.env` file exists and contains the cookie:
```bash
cat .env | grep GEOGUESSR
```

### Cookie expired

GeoGuessr cookies expire periodically. If API calls start failing, get a fresh cookie from your browser.

### Connection refused

1. Check if the container is running: `docker compose ps`
2. Check logs: `docker compose logs geoguessr-mcp`
3. Verify the port is exposed: `docker port geoguessr-mcp-server`

### API rate limiting

GeoGuessr may rate-limit excessive API calls. Space out requests if you're hitting limits.

## Cookie Security

⚠️ **Important Security Notes:**

1. The `_ncfa` cookie provides full access to your GeoGuessr account
2. Never share your `.env` file or commit it to version control
3. Consider running the server on a private network
4. Use SSL in production
5. Regularly rotate your cookie

## Development

To run locally without Docker:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export GEOGUESSR_NCFA_COOKIE="your_cookie_here"

# Run the server
python server.py
```

## API Reference

The server uses the unofficial GeoGuessr API. Key endpoints:

- `https://www.geoguessr.com/api/v3/` - Main API (v3)
- `https://www.geoguessr.com/api/v4/` - Newer API (v4)
- `https://game-server.geoguessr.com/api/` - Game server API

Note: This is an unofficial API and may change without notice.

## License

MIT License - Feel free to modify and distribute.

## Disclaimer

This project is not affiliated with, endorsed by, or connected to GeoGuessr AB. Use at your own risk and in accordance with GeoGuessr's Terms of Service.