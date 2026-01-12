#!/bin/bash
# ════════════════════════════════════════════════════════════════════════════════
# ContentOrbit Enterprise - Startup Script
# ════════════════════════════════════════════════════════════════════════════════
# Unified startup script for all deployment modes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                                                                   ║"
echo "║   🚀 ContentOrbit Enterprise                                      ║"
echo "║   Production-Grade Content Automation Platform                    ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ════════════════════════════════════════════════════════════════════════════════
# Configuration
# ════════════════════════════════════════════════════════════════════════════════

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${PROJECT_DIR}/data"
LOG_DIR="${DATA_DIR}/logs"
VENV_DIR="${PROJECT_DIR}/venv"

# Default ports
DASHBOARD_PORT=${DASHBOARD_PORT:-8501}

# ════════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ════════════════════════════════════════════════════════════════════════════════

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_error "Python not found! Please install Python 3.11+"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log_info "Python version: $PYTHON_VERSION"
}

setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log_info "Creating virtual environment..."
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi
    
    source "$VENV_DIR/bin/activate" 2>/dev/null || source "$VENV_DIR/Scripts/activate" 2>/dev/null
    log_info "Virtual environment activated"
}

install_deps() {
    log_info "Installing dependencies..."
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    log_info "Dependencies installed"
}

setup_dirs() {
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOG_DIR"
    log_info "Data directories created"
}

# ════════════════════════════════════════════════════════════════════════════════
# Main Commands
# ════════════════════════════════════════════════════════════════════════════════

start_dashboard() {
    log_info "Starting Dashboard on port $DASHBOARD_PORT..."
    cd "$PROJECT_DIR"
    streamlit run dashboard/main_dashboard.py \
        --server.port=$DASHBOARD_PORT \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --browser.gatherUsageStats=false
}

start_bot() {
    log_info "Starting Bot Worker..."
    cd "$PROJECT_DIR"
    $PYTHON_CMD main_bot.py
}

start_all() {
    log_info "Starting all services..."
    
    # Start bot in background
    log_info "Starting Bot Worker in background..."
    nohup $PYTHON_CMD main_bot.py > "$LOG_DIR/bot.log" 2>&1 &
    BOT_PID=$!
    echo $BOT_PID > "$DATA_DIR/bot.pid"
    log_info "Bot started with PID: $BOT_PID"
    
    # Start dashboard in foreground
    start_dashboard
}

stop_all() {
    log_info "Stopping all services..."
    
    if [ -f "$DATA_DIR/bot.pid" ]; then
        BOT_PID=$(cat "$DATA_DIR/bot.pid")
        if kill -0 $BOT_PID 2>/dev/null; then
            kill $BOT_PID
            log_info "Bot stopped (PID: $BOT_PID)"
        fi
        rm -f "$DATA_DIR/bot.pid"
    fi
    
    # Kill any streamlit processes
    pkill -f "streamlit run" 2>/dev/null || true
    log_info "All services stopped"
}

start_docker() {
    log_info "Starting with Docker Compose..."
    docker-compose up -d
    log_info "Services started. Dashboard: http://localhost:$DASHBOARD_PORT"
}

stop_docker() {
    log_info "Stopping Docker services..."
    docker-compose down
}

show_status() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "                        SERVICE STATUS                              "
    echo "═══════════════════════════════════════════════════════════════════"
    
    # Check bot
    if [ -f "$DATA_DIR/bot.pid" ]; then
        BOT_PID=$(cat "$DATA_DIR/bot.pid")
        if kill -0 $BOT_PID 2>/dev/null; then
            echo -e "Bot Worker:     ${GREEN}● Running${NC} (PID: $BOT_PID)"
        else
            echo -e "Bot Worker:     ${RED}○ Stopped${NC}"
        fi
    else
        echo -e "Bot Worker:     ${RED}○ Stopped${NC}"
    fi
    
    # Check dashboard
    if pgrep -f "streamlit run" > /dev/null; then
        echo -e "Dashboard:      ${GREEN}● Running${NC}"
    else
        echo -e "Dashboard:      ${RED}○ Stopped${NC}"
    fi
    
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
}

show_help() {
    echo ""
    echo "Usage: ./start.sh [command]"
    echo ""
    echo "Commands:"
    echo "  dashboard    Start the Streamlit dashboard only"
    echo "  bot          Start the bot worker only"
    echo "  start        Start all services (bot in background, dashboard in foreground)"
    echo "  stop         Stop all services"
    echo "  status       Show service status"
    echo "  docker       Start with Docker Compose"
    echo "  docker-stop  Stop Docker services"
    echo "  setup        Install dependencies and setup directories"
    echo "  help         Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  DASHBOARD_PORT    Dashboard port (default: 8501)"
    echo "  DASHBOARD_PASSWORD Password for dashboard login"
    echo ""
}

# ════════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ════════════════════════════════════════════════════════════════════════════════

main() {
    cd "$PROJECT_DIR"
    
    case "${1:-help}" in
        dashboard)
            check_python
            setup_venv
            setup_dirs
            start_dashboard
            ;;
        bot)
            check_python
            setup_venv
            setup_dirs
            start_bot
            ;;
        start)
            check_python
            setup_venv
            setup_dirs
            start_all
            ;;
        stop)
            stop_all
            ;;
        status)
            show_status
            ;;
        docker)
            start_docker
            ;;
        docker-stop)
            stop_docker
            ;;
        setup)
            check_python
            setup_venv
            install_deps
            setup_dirs
            log_info "Setup complete! Run './start.sh start' to begin."
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
