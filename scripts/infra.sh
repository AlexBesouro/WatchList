#!/bin/bash

# WatchList Infrastructure — Local Development
# Single entry point for the infra services WatchList needs (PostgreSQL + Redis).
# Uses docker compose with project name "watchlist" so Docker Desktop groups them.
# Usage: ./scripts/infra.sh [start|stop|restart|status|logs|clean|init|psql|cli]
# Per-service logs: ./scripts/infra.sh logs postgres | ./scripts/infra.sh logs redis

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
COMPOSE_CMD="docker compose -p watchlist -f $COMPOSE_FILE"
VENV="$PROJECT_ROOT/.venv"

# Connection settings (kept in sync with docker-compose.yml and ../.env)
CONTAINER_POSTGRES="watchlist-postgres"
CONTAINER_REDIS="watchlist-redis"
PG_HOST="localhost"
PG_PORT="5442"
PG_USER="postgres"
PG_PASSWORD="watchlist"
PG_DB="watchlist"
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_DB="0"

CMD="${1:-start}"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

is_running() {
    [ "$(docker inspect --format '{{.State.Running}}' "$1" 2>/dev/null)" = "true" ]
}

is_pg_ready() {
    docker exec "$CONTAINER_POSTGRES" pg_isready -U "$PG_USER" -d "$PG_DB" >/dev/null 2>&1
}

wait_for_pg() {
    echo "Waiting for PostgreSQL to be ready..."
    local n=0
    until is_pg_ready || [ $n -ge 30 ]; do sleep 1; n=$((n + 1)); done
    if ! is_pg_ready; then
        echo "Error: PostgreSQL not ready after 30s. Check: $0 logs postgres"
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Infrastructure lifecycle (docker compose)
# ---------------------------------------------------------------------------

infra_start() {
    echo "Starting WatchList infrastructure (postgres + redis)..."
    $COMPOSE_CMD up -d
    wait_for_pg
    print_summary
}

infra_stop() {
    echo "Stopping WatchList infrastructure..."
    $COMPOSE_CMD stop
}

infra_restart() {
    echo "Restarting WatchList infrastructure..."
    $COMPOSE_CMD restart
    wait_for_pg
    print_summary
}

infra_status() {
    $COMPOSE_CMD ps
}

infra_logs() {
    # Pass extra args to filter by service: ./scripts/infra.sh logs postgres
    shift 2>/dev/null || true
    $COMPOSE_CMD logs -f "$@"
}

infra_clean() {
    echo "Removing all WatchList containers and volumes (this wipes the DB)..."
    $COMPOSE_CMD down -v
    echo "Done."
}

# ---------------------------------------------------------------------------
# Database initialization (Alembic migrations)
# ---------------------------------------------------------------------------

init_db() {
    if ! is_running "$CONTAINER_POSTGRES"; then
        echo "PostgreSQL is not running. Starting infrastructure first..."
        infra_start
    else
        wait_for_pg
    fi

    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo "Error: $PROJECT_ROOT/.env missing (Alembic reads the DB URL from it)."
        echo "  cp $PROJECT_ROOT/.env_example $PROJECT_ROOT/.env   # then fill it"
        exit 1
    fi

    if [ ! -x "$VENV/bin/alembic" ]; then
        echo "Error: alembic not found in venv ($VENV/bin/alembic)."
        echo "  python3 -m venv $VENV && $VENV/bin/pip install -r $PROJECT_ROOT/requirements.txt"
        exit 1
    fi

    echo "Running Alembic migrations (upgrade head)..."
    (cd "$PROJECT_ROOT" && "$VENV/bin/alembic" upgrade head)

    echo ""
    echo "Database initialized. Tables:"
    docker exec -i "$CONTAINER_POSTGRES" psql -U "$PG_USER" -d "$PG_DB" -c "\dt"
}

# ---------------------------------------------------------------------------
# Service-specific commands
# ---------------------------------------------------------------------------

psql_connect() {
    if is_running "$CONTAINER_POSTGRES"; then
        echo "Connecting to PostgreSQL..."
        docker exec -it "$CONTAINER_POSTGRES" psql -U "$PG_USER" -d "$PG_DB"
    else
        echo "PostgreSQL is not running. Start it first with: $0 start"
        exit 1
    fi
}

redis_cli() {
    if is_running "$CONTAINER_REDIS"; then
        echo "Connecting to Redis CLI..."
        docker exec -it "$CONTAINER_REDIS" redis-cli
    else
        echo "Redis is not running. Start it first with: $0 start"
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print_summary() {
    cat <<INFO

──────────────────────────────────────────────────────────────────────
  WatchList — Local Infrastructure — Connection info
──────────────────────────────────────────────────────────────────────
  PostgreSQL
    Host:       $PG_HOST
    Port:       $PG_PORT
    Database:   $PG_DB
    User:       $PG_USER
    Password:   $PG_PASSWORD
    URL:        postgresql://$PG_USER:$PG_PASSWORD@$PG_HOST:$PG_PORT/$PG_DB
    psql CLI:   ./scripts/infra.sh psql

  Redis
    Host:       $REDIS_HOST
    Port:       $REDIS_PORT
    DB index:   $REDIS_DB
    Password:   (none)
    URL:        redis://$REDIS_HOST:$REDIS_PORT/$REDIS_DB
    redis CLI:  ./scripts/infra.sh cli
──────────────────────────────────────────────────────────────────────
  Next:  ./scripts/infra.sh init   (Alembic migrations)
         ./scripts/run.sh dev      (start the API → http://localhost:8000/docs)
──────────────────────────────────────────────────────────────────────
INFO
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

case "$CMD" in
    start)          infra_start ;;
    stop)           infra_stop ;;
    restart)        infra_restart ;;
    status)         infra_status ;;
    logs)           infra_logs "$@" ;;
    clean)          infra_clean ;;
    init|init-db)   init_db ;;
    psql)           psql_connect ;;
    cli)            redis_cli ;;
    info|conn)      print_summary ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|clean|init|psql|cli|info}"
        echo ""
        echo "Lifecycle (docker compose — postgres + redis):"
        echo "  start    - Start the containers (default)"
        echo "  stop     - Stop the containers"
        echo "  restart  - Restart the containers"
        echo "  status   - Show container statuses"
        echo "  logs     - Follow logs (optionally: logs postgres | logs redis)"
        echo "  clean    - Remove containers AND volumes (wipes the database)"
        echo ""
        echo "Database:"
        echo "  init     - Run Alembic migrations (upgrade head)"
        echo "  psql     - Connect to PostgreSQL CLI"
        echo ""
        echo "Redis:"
        echo "  cli      - Connect to Redis CLI"
        echo ""
        echo "Info:"
        echo "  info     - Print connection details (host/db/user/password/URL) without starting anything"
        exit 1 ;;
esac
