# CLAUDE.md - Development Guide for AI Assistants

This document provides context for AI assistants (like Claude) working on the GeoGuessr MCP Server project.

## Project Overview

**GeoGuessr MCP Server** is a Model Context Protocol (MCP) server that provides Claude with tools to analyze GeoGuessr game statistics. The server features automatic API monitoring and dynamic schema adaptation to handle API changes gracefully.

### Key Architecture Components

```
geoguessr-mcp/
├── src/geoguessr_mcp/
│   ├── api/              # GeoGuessr API client and response handling
│   ├── auth/             # GeoGuessr authentication management
│   ├── middleware/       # MCP server authentication middleware
│   ├── models/           # Data models (Profile, Stats, Games, etc.)
│   ├── monitoring/       # Dynamic schema detection and API monitoring
│   │   ├── endpoint/     # Endpoint monitoring logic
│   │   └── schema/       # Schema detection and registry
│   ├── services/         # Business logic services
│   ├── tools/            # MCP tool definitions
│   ├── config.py         # Configuration and settings
│   └── main.py           # Application entry point
├── scripts/              # Deployment scripts
│   └── deploy.sh         # Automated production deployment
├── tests/                # Unit and integration tests
├── Dockerfile            # Container definition
├── docker-compose.yml    # Development deployment
└── docker-compose.prod.yml # Production deployment with nginx
```

## Core Concepts

### 1. Dynamic Schema System

The server automatically adapts to GeoGuessr API changes:

- **Schema Detection**: Analyzes API responses to detect field types, structure, and nesting
- **Change Detection**: Uses hash-based comparison to identify schema modifications
- **Persistence**: Caches schemas to disk for survival across restarts
- **Monitoring**: Runs periodic checks (every 24 hours by default) on all known endpoints

**Key Files**:
- `src/geoguessr_mcp/monitoring/schema/schema_detector.py` - Analyzes response structure
- `src/geoguessr_mcp/monitoring/schema/schema_registry.py` - Manages schema storage
- `src/geoguessr_mcp/monitoring/endpoint/endpoint_monitor.py` - Periodic monitoring

### 2. MCP Tool Architecture

Tools are organized by domain:
- **auth_tools.py** - Authentication (login, logout, cookie management)
- **profile_tools.py** - User profiles and statistics
- **game_tools.py** - Game history and details
- **analysis_tools.py** - Performance analysis and recommendations
- **monitoring_tools.py** - API health and endpoint exploration

Each tool returns a `DynamicResponse` which includes both the data and schema information.

### 3. Authentication Systems

The server has two authentication layers:

#### MCP Server Authentication (Access Control)
Controls who can connect to the MCP server:
- **Bearer Token**: API key-based authentication via `Authorization` header
- **Configuration**: `MCP_AUTH_ENABLED` and `MCP_API_KEYS` environment variables
- **Middleware**: `src/geoguessr_mcp/middleware/auth.py` - Validates API keys
- **Optional**: Can be disabled for local/trusted deployments

#### GeoGuessr API Authentication (Data Access)
The server supports three methods to access GeoGuessr's API:
1. **Environment variable**: `GEOGUESSR_NCFA_COOKIE` in .env
2. **Login tool**: Email/password authentication via MCP
3. **Manual cookie**: Direct cookie setting via tool

Session state is managed in `src/geoguessr_mcp/auth/session.py`.

## Docker Deployment

### Official Docker Image

The server is available as a pre-built image: **`nyxiumyuuki/geoguessr-mcp:latest`**

### Build Process

The Dockerfile uses a multi-stage approach:
1. Install dependencies from `pyproject.toml` using `uv` for speed
2. Copy source code
3. Run the server via `python -m geoguessr_mcp.main`

**Important**: The Dockerfile does NOT use a separate `requirements.txt`. It installs directly from `pyproject.toml`.

### Deployment Options

1. **Pre-built Image**: `docker compose up -d` (uses nyxiumyuuki/geoguessr-mcp:latest)
2. **Local Build**: Uncomment build section in docker-compose.yml
3. **Production**: Use `docker-compose.prod.yml` with nginx reverse proxy
4. **Automated**: Use `./scripts/deploy.sh` for production deployment

### MCP Server Authentication Configuration

The server supports optional Bearer token authentication:
- Set `MCP_AUTH_ENABLED=true` to enable
- Set `MCP_API_KEYS=key1,key2,key3` for comma-separated keys
- Generate secure keys with `openssl rand -hex 32`
- Clients connect with `Authorization: Bearer YOUR_API_KEY` header
- Middleware is in `src/geoguessr_mcp/middleware/auth.py`

### Monitoring Configuration

Monitoring runs every 24 hours by default:
- Set `MONITORING_ENABLED=true` to enable
- Set `MONITORING_INTERVAL_HOURS=24` for interval
- Schemas are persisted in `/app/data/schemas` volume

## Development Workflow

### Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires auth)
pytest tests/integration/ -v

# With coverage
pytest --cov=src/geoguessr_mcp tests/
```

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run server locally
python -m geoguessr_mcp.main

# Or use the entry point
geoguessr-mcp
```

### Code Quality

- **Formatter**: Black (line length 100)
- **Linter**: Ruff
- **Type Checker**: MyPy (strict mode)

Run checks:
```bash
black src/ tests/
ruff check src/ tests/
mypy src/
```

## Common Tasks

### Adding a New Tool

1. Create tool function in appropriate `tools/*.py` file
2. Use `@mcp.tool()` decorator
3. Return `DynamicResponse` or structured data
4. Add to tool registration in `__init__.py`
5. Write unit tests

Example:
```python
@mcp.tool()
async def my_new_tool(param: str) -> str:
    """Tool description for Claude."""
    # Implementation
    return result
```

### Adding a New Endpoint to Monitor

1. Add endpoint definition to `MONITORED_ENDPOINTS` in `endpoint_monitor.py`
2. Specify path, method, params, and description
3. Schema detection happens automatically

Example:
```python
EndpointDefinition(
    path="/v3/profiles/new-data",
    description="New profile data endpoint",
)
```

### Updating Configuration

Configuration is managed via environment variables in `config.py`:
- Add new setting to `Settings` dataclass
- Use `field(default_factory=lambda: os.getenv(...))` pattern
- Document in README.md environment variables section

## Testing Strategy

### Unit Tests
- Mock external API calls using `respx`
- Test each component in isolation
- Located in `tests/unit/`

### Integration Tests
- Use fixtures from `tests/conftest.py`
- Mock authentication for CI/CD
- Test full request/response flows
- Located in `tests/integration/`

### Fixtures
- `mock_auth_session` - Provides authenticated session
- `mock_http_client` - Mocked httpx client
- `sample_*` - Sample API responses

## Key Dependencies

- **mcp[cli]** - Model Context Protocol framework
- **httpx** - Async HTTP client for API calls
- **uvicorn** - ASGI server
- **starlette** - Web framework (used by FastMCP)
- **python-dotenv** - Environment variable management

## Troubleshooting

### Common Issues

1. **"server.py not found"**: The entry point is `main.py`, not `server.py`
2. **Schema not persisting**: Check volume mount for `/app/data/schemas`
3. **Monitoring not running**: Verify `MONITORING_ENABLED=true` and check logs
4. **Auth failures**: Ensure valid NCFA cookie or use login tool

### Debugging

Enable debug logging:
```bash
LOG_LEVEL=DEBUG docker compose up
```

Check monitoring status via tool:
```python
# In Claude
check_api_status()
```

## CI/CD Considerations

### Building for Production

```bash
# Multi-architecture build
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t username/geoguessr-mcp:latest \
  --push .

# Single architecture
docker build -t username/geoguessr-mcp:latest .
docker push username/geoguessr-mcp:latest
```

### Environment Variables for Deployment

Required:
- `GEOGUESSR_NCFA_COOKIE` - For authenticated endpoints

Optional:
- `MONITORING_INTERVAL_HOURS` - Default: 24
- `LOG_LEVEL` - Default: INFO
- `MCP_PORT` - Default: 8000

## Schema Registry Details

### Schema Hash Computation

Schemas are identified by a hash of:
- Field names and types
- Nested structure
- Array element types
- Null/undefined handling

### Schema Change Detection

When a schema changes:
1. New hash is computed
2. Comparison with previous hash
3. If different, `schema_changed` flag is set
4. New schema is persisted to disk
5. Monitoring result includes change notification

### Schema Persistence Format

Schemas are stored as JSON in `SCHEMA_CACHE_DIR`:
```json
{
  "endpoint": "/v3/profiles",
  "schema_hash": "abc123...",
  "fields": [...],
  "last_updated": "2025-11-29T...",
  "http_status": 200
}
```

## API Monitoring System

### Monitored Endpoints

Currently monitoring ~15 endpoints:
- Profile & Stats (v3, v4)
- Games & Social (feed, friends, badges)
- Competitive (seasons)
- Explorer & Objectives
- Challenges (daily)

### Monitoring Loop

1. Every 24 hours (configurable)
2. Checks each endpoint sequentially
3. 0.5s delay between requests (rate limiting)
4. Updates schema registry on changes
5. Logs availability and response times
6. Generates monitoring report

### Monitoring Tools

Users can:
- `check_api_status()` - Get current status of all endpoints
- `get_endpoint_schema(path)` - Get schema for specific endpoint
- `list_available_endpoints()` - List all known endpoints
- `explore_endpoint(path)` - Manually check a new endpoint

## Best Practices

1. **Always use DynamicResponse** for tools that return API data
2. **Mock authentication** in tests using fixtures
3. **Keep schemas generic** - don't hardcode field expectations
4. **Log schema changes** at INFO level for visibility
5. **Use async/await** consistently throughout the codebase
6. **Handle rate limiting** with delays between requests
7. **Validate configuration** in Settings.__post_init__
8. **Document tools** with clear docstrings for Claude

## Future Enhancements

Potential areas for improvement:
- [ ] Add metrics collection (Prometheus/Grafana)
- [ ] Implement rate limiting middleware
- [ ] Add caching layer for frequently accessed data
- [ ] Support for webhooks/real-time updates
- [ ] Advanced analytics and ML-based recommendations
- [ ] Multi-user support with session management
- [ ] GraphQL endpoint for flexible queries

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [FastMCP Guide](https://github.com/jlowin/fastmcp)
- [GeoGuessr API (unofficial)](https://www.geoguessr.com/api)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Last Updated**: 2025-11-29
**Maintainer**: See pyproject.toml for author information
