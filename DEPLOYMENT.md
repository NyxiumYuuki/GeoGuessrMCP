# Production Deployment Guide - VPS with SSL

This guide covers deploying the GeoGuessr MCP Server to your VPS using your existing nginx-proxy-manager for SSL/HTTPS.

## Prerequisites

- VPS with Docker and Docker Compose installed
- Existing nginx-proxy-manager running (port 81 for admin interface)
- Domain or subdomain pointing to your VPS (e.g., `geoguessr-mcp.yourdomain.com`)
- Docker Hub account (for hosting your image)

## Deployment Architecture

```
                                    ┌─────────────────────┐
Internet ──────HTTPS (443)─────────►│ nginx-proxy-manager │
                                    │   (Firefly stack)   │
                                    └──────────┬──────────┘
                                               │
                                 firefly_network (Docker network)
                                               │
                          ┌────────────────────┼────────────────────┐
                          │                    │                    │
                    ┌─────▼──────┐      ┌──────▼──────┐    ┌───────▼────────┐
                    │  Firefly   │      │  GeoGuessr  │    │  Other apps... │
                    │    App     │      │  MCP Server │    │                │
                    └────────────┘      └─────────────┘    └────────────────┘
```

## Step 1: Build and Push Docker Image

### 1.1 Build the Image

On your local machine or directly on the VPS:

```bash
# Navigate to project directory
cd /path/to/GeoGuessrMCP

# Build the image
docker build -t yourusername/geoguessr-mcp:latest .

# Optional: Build multi-architecture image (if deploying to ARM64)
docker buildx build --platform linux/amd64,linux/arm64 \
  -t yourusername/geoguessr-mcp:latest --push .
```

### 1.2 Push to Docker Hub

```bash
# Login to Docker Hub
docker login

# Push the image
docker push yourusername/geoguessr-mcp:latest

# Optionally tag with version
docker tag yourusername/geoguessr-mcp:latest yourusername/geoguessr-mcp:v1.0.0
docker push yourusername/geoguessr-mcp:v1.0.0
```

## Step 2: Prepare VPS Directory

### 2.1 Create Project Directory

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Create directory at same level as /firefly
cd /
sudo mkdir -p geoguessr-mcp
sudo chown $USER:$USER geoguessr-mcp
cd geoguessr-mcp
```

### 2.2 Upload Required Files

Transfer these files to your VPS `/geoguessr-mcp` directory:
- `docker-compose.prod.yml`
- `.env` (production configuration)

```bash
# From your local machine
scp docker-compose.prod.yml user@your-vps-ip:/geoguessr-mcp/
scp .env.production user@your-vps-ip:/geoguessr-mcp/.env
```

### 2.3 Configure Environment Variables

```bash
# On VPS - edit .env file
cd /geoguessr-mcp
nano .env
```

Update the following variables:

```bash
# Docker image configuration
DOCKER_USERNAME=yourusername
IMAGE_TAG=latest

# GeoGuessr authentication (REQUIRED for most features)
GEOGUESSR_NCFA_COOKIE=your_ncfa_cookie_here

# Monitoring (recommended for production)
MONITORING_ENABLED=true
MONITORING_INTERVAL_HOURS=24

# Logging
LOG_LEVEL=INFO

# Schema cache directory (default is fine)
SCHEMA_CACHE_DIR=/app/data/schemas
```

## Step 3: Deploy the Container

### 3.1 Pull and Start the Container

```bash
cd /geoguessr-mcp

# Pull the latest image
docker compose -f docker-compose.prod.yml pull

# Start the service
docker compose -f docker-compose.prod.yml up -d

# Check logs
docker compose -f docker-compose.prod.yml logs -f
```

### 3.2 Verify Container is Running

```bash
# Check container status
docker ps | grep geoguessr-mcp

# Check health status
docker inspect geoguessr-mcp-server --format='{{.State.Health.Status}}'

# Should output: healthy
```

## Step 4: Configure nginx-proxy-manager

### 4.1 Access nginx-proxy-manager Admin

1. Open browser and navigate to: `http://your-vps-ip:81`
2. Login with your credentials (default: `admin@example.com` / `changeme`)

### 4.2 Add Proxy Host

1. Click **"Hosts"** → **"Proxy Hosts"** → **"Add Proxy Host"**

2. **Details Tab:**
   - **Domain Names:** `geoguessr-mcp.yourdomain.com` (your subdomain)
   - **Scheme:** `http`
   - **Forward Hostname/IP:** `geoguessr-mcp-server` (container name)
   - **Forward Port:** `8000`
   - **Cache Assets:** ✓ (enable)
   - **Block Common Exploits:** ✓ (enable)
   - **Websockets Support:** ✓ (enable - required for MCP)

3. **SSL Tab:**
   - **SSL Certificate:** Select "Request a new SSL Certificate"
   - **Force SSL:** ✓ (enable)
   - **HTTP/2 Support:** ✓ (enable)
   - **HSTS Enabled:** ✓ (enable)
   - **Email Address for Let's Encrypt:** your-email@example.com
   - **I Agree to the Let's Encrypt Terms of Service:** ✓

4. Click **"Save"**

nginx-proxy-manager will now:
- Request an SSL certificate from Let's Encrypt
- Configure automatic HTTPS redirection
- Proxy requests to your GeoGuessr MCP container

### 4.3 Verify SSL is Working

```bash
# Test the endpoint
curl https://geoguessr-mcp.yourdomain.com/health

# Should return: {"status": "healthy"}
```

## Step 5: Connect Claude Desktop

### 5.1 Update Claude Desktop Configuration

On your local machine, edit `claude_desktop_config.json`:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "geoguessr-mcp": {
      "url": "https://geoguessr-mcp.yourdomain.com"
    }
  }
}
```

### 5.2 Restart Claude Desktop

Close and reopen Claude Desktop. The MCP server should now appear in the tools list.

## Step 6: Monitoring and Maintenance

### 6.1 View Logs

```bash
# Follow logs in real-time
docker compose -f docker-compose.prod.yml logs -f geoguessr-mcp

# View last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 geoguessr-mcp
```

### 6.2 Update the Application

```bash
cd /geoguessr-mcp

# Pull latest image
docker compose -f docker-compose.prod.yml pull

# Recreate container with new image
docker compose -f docker-compose.prod.yml up -d

# Remove old images
docker image prune -f
```

### 6.3 Backup Schema Data

The schema cache is persisted in a Docker volume. To backup:

```bash
# Create backup directory
mkdir -p ~/backups

# Backup the volume
docker run --rm \
  -v geoguessr-mcp-schemas-prod:/data \
  -v ~/backups:/backup \
  alpine tar czf /backup/geoguessr-schemas-$(date +%Y%m%d).tar.gz -C /data .
```

### 6.4 SSL Certificate Renewal

Let's Encrypt certificates are valid for 90 days. nginx-proxy-manager automatically renews them. To manually check:

1. Go to nginx-proxy-manager admin (port 81)
2. Navigate to **"SSL Certificates"**
3. Check expiry date
4. Click **"Renew"** if needed

## Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker compose -f docker-compose.prod.yml logs geoguessr-mcp

# Common issues:
# - Missing .env file
# - Invalid NCFA cookie
# - Network connection issues
```

### SSL Certificate Failed

1. Ensure DNS is pointing to your VPS IP
2. Check firewall allows ports 80 and 443
3. Verify email address is valid
4. Check nginx-proxy-manager logs:

```bash
docker logs proxy_app
```

### Can't Connect from Claude Desktop

1. Verify container is healthy: `docker ps`
2. Test locally on VPS: `curl http://localhost:8000/health`
3. Test through proxy: `curl https://geoguessr-mcp.yourdomain.com/health`
4. Check nginx-proxy-manager proxy host configuration
5. Verify firewall allows HTTPS (port 443)

### Schema Not Persisting

```bash
# Check volume exists
docker volume ls | grep geoguessr-mcp-schemas-prod

# Inspect volume
docker volume inspect geoguessr-mcp-schemas-prod

# If missing, recreate:
docker compose -f docker-compose.prod.yml down
docker volume create geoguessr-mcp-schemas-prod
docker compose -f docker-compose.prod.yml up -d
```

## Security Best Practices

### 1. Secure Environment Variables

```bash
# Ensure .env file is not world-readable
chmod 600 .env

# Never commit .env to git
# (already in .gitignore)
```

### 2. Update nginx-proxy-manager Default Credentials

After first login:
1. Go to **"Users"**
2. Edit the admin user
3. Change email and password
4. Enable 2FA if available

### 3. Configure Firewall

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP (for Let's Encrypt)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 4. Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images monthly
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### 5. Monitor Access Logs

nginx-proxy-manager provides access logs:
1. Admin interface → **"Hosts"** → **"Proxy Hosts"**
2. Click on your host → **"Access List"** tab
3. Optionally restrict by IP addresses

## Performance Optimization

### 1. Enable Caching in nginx-proxy-manager

Add custom nginx configuration:

```nginx
# In proxy host "Advanced" tab
proxy_cache_path /tmp/cache levels=1:2 keys_zone=geoguessr_cache:10m max_size=100m inactive=60m;
proxy_cache geoguessr_cache;
proxy_cache_valid 200 10m;
proxy_cache_valid 404 1m;
add_header X-Cache-Status $upstream_cache_status;
```

### 2. Adjust Container Resources

If needed, limit resources in `docker-compose.prod.yml`:

```yaml
services:
  geoguessr-mcp:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

## Monitoring Tools

### Check API Endpoint Status

Use the MCP tools in Claude:

```
Use the check_api_status() tool to see:
- All monitored endpoints
- Response times
- Schema changes
- Error rates
```

### Container Health Metrics

```bash
# CPU and memory usage
docker stats geoguessr-mcp-server

# Detailed inspection
docker inspect geoguessr-mcp-server
```

## Rollback Procedure

If an update causes issues:

```bash
cd /geoguessr-mcp

# Stop current version
docker compose -f docker-compose.prod.yml down

# Update .env to use previous tag
nano .env
# Change: IMAGE_TAG=v1.0.0  (or previous version)

# Restart with old version
docker compose -f docker-compose.prod.yml up -d
```

## Getting Help

- **Issues:** https://github.com/yourusername/geoguessr-mcp/issues
- **Logs:** Always include container logs when reporting issues
- **nginx-proxy-manager docs:** https://nginxproxymanager.com/guide/

---

**Last Updated:** 2025-11-29
