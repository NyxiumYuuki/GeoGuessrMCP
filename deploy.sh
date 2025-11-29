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
        print_warning "$ENV_FILE not found. Creating from example..."
        if [ -f "$ENV_EXAMPLE" ]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            print_warning "Please edit $ENV_FILE with your actual credentials!"
            print_info "Required: DOCKER_USERNAME and GEOGUESSR_NCFA_COOKIE"
            exit 1
        else
            print_error "No .env.production example found!"
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

    if [ -z "$DOCKER_USERNAME" ] || [ "$DOCKER_USERNAME" == "yourusername" ]; then
        print_error "DOCKER_USERNAME not configured in $ENV_FILE"
        exit 1
    fi
    print_success "DOCKER_USERNAME is set: $DOCKER_USERNAME"

    if [ -z "$GEOGUESSR_NCFA_COOKIE" ] || [ "$GEOGUESSR_NCFA_COOKIE" == "your_actual_ncfa_cookie_value_here" ]; then
        print_warning "GEOGUESSR_NCFA_COOKIE not configured"
        print_info "Most features require authentication. You can set this later."
    else
        print_success "GEOGUESSR_NCFA_COOKIE is configured"
    fi

    if [ -z "$IMAGE_TAG" ]; then
        IMAGE_TAG="latest"
    fi
    print_info "Using image tag: $IMAGE_TAG"
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

    print_info "Pulling image: $DOCKER_USERNAME/geoguessr-mcp:$IMAGE_TAG"
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

    print_info "Waiting for container to be healthy..."
    sleep 5

    # Check health
    HEALTH=$(docker inspect geoguessr-mcp-server --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
    if [ "$HEALTH" == "healthy" ]; then
        print_success "Container is healthy!"
    elif [ "$HEALTH" == "starting" ]; then
        print_warning "Container is still starting... Check logs with:"
        print_info "docker compose -f $COMPOSE_FILE logs -f"
    else
        print_warning "Container health check not yet available. Checking if running..."
        if docker ps | grep -q geoguessr-mcp-server; then
            print_success "Container is running"
        else
            print_error "Container is not running!"
            print_info "Check logs with: docker compose -f $COMPOSE_FILE logs"
            exit 1
        fi
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
    echo "2. Test the health endpoint:"
    echo "   curl https://your-domain.com/health"
    echo ""
    echo "3. Connect Claude Desktop:"
    echo "   Add to claude_desktop_config.json:"
    echo '   "geoguessr-mcp": { "url": "https://your-domain.com" }'
    echo ""

    print_info "Useful Commands:"
    echo ""
    echo "  View logs:        docker compose -f $COMPOSE_FILE logs -f"
    echo "  Restart:          docker compose -f $COMPOSE_FILE restart"
    echo "  Stop:             docker compose -f $COMPOSE_FILE down"
    echo "  Update:           ./deploy.sh"
    echo ""

    print_info "Troubleshooting:"
    echo ""
    echo "  Check status:     docker ps | grep geoguessr-mcp"
    echo "  Check health:     docker inspect geoguessr-mcp-server --format='{{.State.Health.Status}}'"
    echo "  Enter container:  docker exec -it geoguessr-mcp-server /bin/bash"
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
