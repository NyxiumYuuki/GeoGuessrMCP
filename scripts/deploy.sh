#!/bin/bash
# GeoGuessr MCP Server - Production Deployment Script
# This script helps deploy the application to a VPS with nginx-proxy-manager

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
ENV_EXAMPLE=".env.production"

# Helper functions
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running on VPS or local
check_environment() {
    print_header "Step 1: Environment Check"

    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "docker-compose.prod.yml not found!"
        exit 1
    fi
    print_success "Found $COMPOSE_FILE"

    if [ ! -f "$ENV_FILE" ]; then
        print_warning "$ENV_FILE not found. Creating from .env.example..."
        if [ -f ".env.example" ]; then
            cp ".env.example" "$ENV_FILE"
            print_warning "Please edit $ENV_FILE with your actual configuration!"
            print_info "Configure GEOGUESSR_NCFA_COOKIE and MCP_API_KEYS if using authentication"
            exit 1
        else
            print_error "No .env.example found!"
            exit 1
        fi
    fi
    print_success "Found $ENV_FILE"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        exit 1
    fi
    print_success "Docker is installed"

    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed!"
        exit 1
    fi
    print_success "Docker Compose is installed"
}

# Check if .env is properly configured
check_config() {
    print_header "Step 2: Configuration Check"

    source "$ENV_FILE"

    print_info "Using Docker image: nyxiumyuuki/geoguessr-mcp:latest"

    if [ -z "$GEOGUESSR_NCFA_COOKIE" ]; then
        print_warning "GEOGUESSR_NCFA_COOKIE not configured"
        print_info "Most GeoGuessr features require authentication. You can set this later."
    else
        print_success "GEOGUESSR_NCFA_COOKIE is configured"
    fi

    if [ "$MCP_AUTH_ENABLED" == "true" ]; then
        if [ -z "$MCP_API_KEYS" ]; then
            print_error "MCP_AUTH_ENABLED is true but MCP_API_KEYS is not set!"
            print_info "Either disable authentication or configure API keys"
            exit 1
        fi
        print_success "MCP server authentication is ENABLED"
    else
        print_warning "MCP server authentication is DISABLED - server will be publicly accessible"
    fi
}

# Check if firefly_network exists
check_network() {
    print_header "Step 3: Docker Network Check"

    if docker network inspect firefly_network &> /dev/null; then
        print_success "firefly_network exists"
    else
        print_warning "firefly_network does not exist"
        print_info "Creating firefly_network..."
        docker network create firefly_network
        print_success "Created firefly_network"
    fi
}

# Pull latest image
pull_image() {
    print_header "Step 4: Pull Docker Image"

    print_info "Pulling image: nyxiumyuuki/geoguessr-mcp:latest"
    docker compose -f "$COMPOSE_FILE" pull
    print_success "Image pulled successfully"
}

# Stop and remove old container
stop_old() {
    print_header "Step 5: Stop Old Container (if exists)"

    if docker ps -a | grep -q geoguessr-mcp-server; then
        print_info "Stopping old container..."
        docker compose -f "$COMPOSE_FILE" down
        print_success "Old container stopped"
    else
        print_info "No existing container found"
    fi
}

# Start new container
start_new() {
    print_header "Step 6: Start New Container"

    print_info "Starting container in detached mode..."
    docker compose -f "$COMPOSE_FILE" up -d
    print_success "Container started"

    print_info "Waiting for container to start..."
    sleep 3

    # Check if running
    if docker ps | grep -q geoguessr-mcp-server; then
        print_success "Container is running"
    else
        print_error "Container is not running!"
        print_info "Check logs with: docker compose -f $COMPOSE_FILE logs"
        exit 1
    fi
}

# Show logs
show_logs() {
    print_header "Step 7: Recent Logs"

    docker compose -f "$COMPOSE_FILE" logs --tail=20
}

# Show next steps
show_next_steps() {
    print_header "Deployment Complete!"

    echo -e "${GREEN}Your GeoGuessr MCP Server is now running!${NC}\n"

    print_info "Next Steps:"
    echo ""
    echo "1. Configure nginx-proxy-manager:"
    echo "   - Access admin panel: http://$(hostname -I | awk '{print $1}'):81"
    echo "   - Add new Proxy Host"
    echo "   - Forward Hostname/IP: geoguessr-mcp-server"
    echo "   - Forward Port: 8000"
    echo "   - Enable SSL with Let's Encrypt"
    echo ""
    echo "2. Test the MCP endpoint:"
    echo "   curl https://your-domain.com/mcp"
    echo "   (With auth): curl -H 'Authorization: Bearer YOUR_API_KEY' https://your-domain.com/mcp"
    echo ""
    echo "3. Connect Claude Desktop:"
    echo "   Add to claude_desktop_config.json:"
    echo '   {'
    echo '     "mcpServers": {'
    echo '       "geoguessr": {'
    echo '         "type": "streamable-http",'
    echo '         "url": "https://your-domain.com/mcp",'
    echo '         "headers": {'
    echo '           "Authorization": "Bearer YOUR_API_KEY"'
    echo '         }'
    echo '       }'
    echo '     }'
    echo '   }'
    echo ""

    print_info "Useful Commands:"
    echo ""
    echo "  View logs:        docker compose -f $COMPOSE_FILE logs -f"
    echo "  Restart:          docker compose -f $COMPOSE_FILE restart"
    echo "  Stop:             docker compose -f $COMPOSE_FILE down"
    echo "  Update:           scripts/deploy.sh"
    echo ""

    print_info "Troubleshooting:"
    echo ""
    echo "  Check status:     docker ps | grep geoguessr-mcp"
    echo "  Enter container:  docker exec -it geoguessr-mcp-server /bin/bash"
    echo "  View all logs:    docker compose -f $COMPOSE_FILE logs --tail=100"
    echo ""

    print_info "For detailed documentation, see: DEPLOYMENT.md"
}

# Main deployment flow
main() {
    print_header "GeoGuessr MCP Server - Production Deployment"

    check_environment
    check_config
    check_network
    pull_image
    stop_old
    start_new
    show_logs
    show_next_steps
}

# Run main function
main
