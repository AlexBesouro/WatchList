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
MOCK_HOST="localhost"
MOCK_PORT="${WATCHLIST_MOCK_PORT:-9100}"

# Le dispatch lit $1 (cible ou commande) et $2 (action) directement — voir le bas du fichier.

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

# Actions génériques sur les services docker compose.
# $1 vide = tous les services (postgres + redis) ; sinon "postgres" | "redis".
svc_start() {
    local svc="${1:-}"
    echo "Starting ${svc:-postgres + redis}..."
    $COMPOSE_CMD up -d $svc
    if [ -z "$svc" ] || [ "$svc" = "postgres" ]; then wait_for_pg; fi
    print_summary
}

svc_stop() {
    local svc="${1:-}"
    echo "Stopping ${svc:-postgres + redis}..."
    $COMPOSE_CMD stop $svc
}

svc_restart() {
    local svc="${1:-}"
    echo "Restarting ${svc:-postgres + redis}..."
    $COMPOSE_CMD restart $svc
    if [ -z "$svc" ] || [ "$svc" = "postgres" ]; then wait_for_pg; fi
    print_summary
}

svc_status() {
    $COMPOSE_CMD ps ${1:-}
}

svc_logs() {
    $COMPOSE_CMD logs -f ${1:-}
}

# Action sur un service docker unique (postgres|redis) ou tous ("" = postgres+redis).
svc_action() {
    local svc="$1" action="$2"
    case "$action" in
        start)   svc_start "$svc" ;;
        stop)    svc_stop "$svc" ;;
        restart) svc_restart "$svc" ;;
        status)  svc_status "$svc" ;;
        logs)    svc_logs "$svc" ;;
        *) echo "Action inconnue: $action (start|stop|restart|status|logs)"; exit 1 ;;
    esac
}

# "all" = services docker (postgres + redis) + serveur mock, en une commande.
all_action() {
    local action="$1"
    case "$action" in
        start)
            mock_control start || echo "[infra] ⚠ mock non démarré (voir ./scripts/infra.sh mock logs)"
            svc_start "" ;;
        stop)
            mock_control stop || true
            svc_stop "" ;;
        restart)
            mock_control restart || echo "[infra] ⚠ mock non redémarré"
            svc_restart "" ;;
        status)
            svc_status ""
            echo
            mock_control status || true ;;
        logs)
            echo "[infra] (logs du mock à part : ./scripts/infra.sh mock logs)"
            svc_logs "" ;;
        *) echo "Action inconnue: $action (start|stop|restart|status|logs)"; exit 1 ;;
    esac
}

# Aiguille (cible, action) → implémentation.
# cible ∈ {all, postgres|pg, redis, mock} ; action ∈ {start,stop,restart,status,logs}.
# "all" englobe les services docker ET le serveur mock (un seul point d'entrée).
service_action() {
    local target="$1" action="${2:-status}"
    case "$target" in
        all)           all_action "$action" ;;
        postgres | pg) svc_action postgres "$action" ;;
        redis)         svc_action redis "$action" ;;
        mock)          mock_control "$action" ;;
        *) echo "Cible inconnue: $target (all|postgres|redis|mock)"; exit 1 ;;
    esac
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

# Serveur mock TMDB/OMDB (process uvicorn, pas un service docker) — délègue à
# scripts/mock.sh. Se pilote individuellement : ./scripts/infra.sh mock [start|stop|status|logs]
mock_control() {
    "$SCRIPT_DIR/mock.sh" "${1:-start}"
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

  Mock TMDB/OMDB  (démarré avec l'infra — GET /movies/ sans clé API)
    URL:        http://$MOCK_HOST:$MOCK_PORT   (health: /health)
    Serveur:    ./scripts/infra.sh mock start|stop|status   (le mock seul)
    App:        ./scripts/run.sh dev    (mode mock auto tant que .env garde les clés CHANGE_ME)
                ./scripts/run.sh mock   (force le mode mock)
──────────────────────────────────────────────────────────────────────
  Next:  ./scripts/infra.sh init   (Alembic migrations)
         ./scripts/seed.sh         (données de démo : 2 users + films)
         ./scripts/run.sh dev      (start the API → http://localhost:8000/docs)
──────────────────────────────────────────────────────────────────────
INFO
}

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------

usage() {
    cat <<EOF
WatchList — infra locale (point d'entrée unique)

Usage:
  $0 <cible> <action>      grammaire flexible
  $0 <action>              raccourci = action sur "all" (postgres + redis)
  $0 <commande>            commandes hors cycle de vie

Cibles :  all | postgres (pg) | redis | mock
Actions:  start | stop | restart | status | logs      (défaut: status)

Exemples :
  $0 start                 # démarre postgres + redis        (= $0 all start)
  $0 all restart           # redémarre postgres + redis
  $0 redis logs            # suit les logs de redis
  $0 postgres status       # statut de postgres uniquement
  $0 mock start            # démarre le mock TMDB/OMDB (GET /movies/ sans clé API)

Commandes :
  init     Applique les migrations Alembic (upgrade head)
  psql     Ouvre psql dans le conteneur postgres
  cli      Ouvre redis-cli dans le conteneur redis
  clean    Supprime conteneurs ET volumes (efface la base)
  info     Affiche les infos de connexion sans rien démarrer
EOF
}

# ---------------------------------------------------------------------------
# Main — grammaire "<cible> <action>" + alias legacy + commandes
# ---------------------------------------------------------------------------

FIRST="${1:-}"
case "$FIRST" in
    # Grammaire <cible> <action> (action par défaut: status)
    all | postgres | pg | redis | mock)
        service_action "$FIRST" "${2:-status}" ;;

    # Alias legacy = <action> sur "all" (postgres + redis)
    start | stop | restart | status)
        service_action all "$FIRST" ;;
    logs)
        shift; svc_logs "${1:-}" ;;

    # Commandes hors cycle de vie
    clean)          infra_clean ;;
    init | init-db) init_db ;;
    psql)           psql_connect ;;
    cli)            redis_cli ;;
    info | conn)    print_summary ;;
    "" | -h | --help | help) usage ;;
    *)              echo "Commande/cible inconnue: $FIRST"; echo; usage; exit 1 ;;
esac
