#!/bin/bash

# ===================================================================
# Neutrino Energy Pipeline - Deployment Script
# ===================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Docker and Docker Compose
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "All prerequisites are satisfied."
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    if [ ! -f .env ]; then
        if [ -f .env.template ]; then
            print_warning ".env file not found. Copying from template..."
            cp .env.template .env
            print_warning "Please edit .env file with your configuration before continuing."
            print_warning "Required: ELECTRICITY_MAPS_TOKEN and secure passwords."
            read -p "Press Enter when you've configured .env file..."
        else
            print_error ".env.template not found. Cannot create environment file."
            exit 1
        fi
    fi
    
    # Validate required environment variables
    source .env
    if [ -z "$ELECTRICITY_MAPS_TOKEN" ] || [ "$ELECTRICITY_MAPS_TOKEN" = "your_electricity_maps_api_token_here" ]; then
        print_error "ELECTRICITY_MAPS_TOKEN is not configured in .env file."
        exit 1
    fi
    
    print_success "Environment configuration validated."
}

# Function to build and start services
deploy_services() {
    print_status "Building and starting services..."
    
    # Build images
    print_status "Building Docker images..."
    docker-compose build --no-cache
    
    # Start services
    print_status "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    print_status "Checking service health..."
    docker-compose ps
}

# Function to setup Grafana dashboards
setup_grafana() {
    print_status "Setting up Grafana..."
    
    # Wait for Grafana to be ready
    timeout=60
    count=0
    while [ $count -lt $timeout ]; do
        if curl -s http://localhost:3000/api/health >/dev/null 2>&1; then
            break
        fi
        sleep 1
        count=$((count + 1))
    done
    
    if [ $count -eq $timeout ]; then
        print_warning "Grafana health check timeout. Please check manually."
    else
        print_success "Grafana is ready at http://localhost:3000"
    fi
}

# Function to run initial data sync
initial_data_sync() {
    print_status "Running initial data synchronization..."
    
    # Run the pipeline manually once to populate initial data
    if docker-compose exec -T energy-pipeline python etl_energy_data.py; then
        print_success "Initial data sync completed."
    else
        print_warning "Initial data sync failed. Check logs with: docker-compose logs energy-pipeline"
    fi
}

# Function to display access information
display_access_info() {
    print_success "==================================================================="
    print_success "🚀 Neutrino Energy Pipeline Deployment Complete!"
    print_success "==================================================================="
    echo ""
    print_status "Access your services:"
    echo "  📊 Grafana Dashboard: http://localhost:3000"
    echo "  🗄️  Mongo Express:    http://localhost:8081"
    echo "  🐘 PostgreSQL:       localhost:5432"
    echo ""
    print_status "Useful commands:"
    echo "  📋 View logs:         docker-compose logs -f [service-name]"
    echo "  ✅ Check status:      docker-compose ps"
    echo "  🔄 Restart service:   docker-compose restart [service-name]"
    echo "  🛑 Stop all:          docker-compose down"
    echo ""
    print_status "Documentation:"
    echo "  📖 Full guide:        See DOCKER_README.md"
    echo "  🐛 Troubleshooting:   See DOCKER_README.md#troubleshooting"
    echo ""
    print_success "Happy monitoring! 🌱⚡"
}

# Function to show help
show_help() {
    echo "Neutrino Energy Pipeline Deployment Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  deploy      Full deployment (default)"
    echo "  start       Start existing services"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  logs        Show logs"
    echo "  status      Show service status"
    echo "  clean       Clean up (remove containers and volumes)"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy   # Full deployment"
    echo "  $0 start    # Start services"
    echo "  $0 logs     # View logs"
}

# Main deployment function
main_deploy() {
    echo "🚀 Starting Neutrino Energy Pipeline Deployment..."
    echo ""
    
    check_prerequisites
    setup_environment
    deploy_services
    setup_grafana
    initial_data_sync
    display_access_info
}

# Parse command line arguments
case "${1:-deploy}" in
    deploy)
        main_deploy
        ;;
    start)
        print_status "Starting services..."
        docker-compose up -d
        print_success "Services started."
        ;;
    stop)
        print_status "Stopping services..."
        docker-compose down
        print_success "Services stopped."
        ;;
    restart)
        print_status "Restarting services..."
        docker-compose restart
        print_success "Services restarted."
        ;;
    logs)
        docker-compose logs -f
        ;;
    status)
        docker-compose ps
        ;;
    clean)
        read -p "This will remove all containers and volumes. Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Cleaning up..."
            docker-compose down -v
            docker system prune -f
            print_success "Cleanup completed."
        else
            print_status "Cleanup cancelled."
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
