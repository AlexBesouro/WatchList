#!/bin/bash

# WatchList — local app runner (FastAPI, app.main:my_app) using the project venv.
# Usage: ./scripts/run.sh [dev|start|stop|restart|status|logs]   (default: status)
#
# - `dev`      runs in foreground with --reload (Ctrl+C to stop).
# - `start`    runs in background; PID + log under scripts/.watchlist.{pid,log}.
# - `stop|restart|status|logs` manage the background instance.
#
# Requires the infra (postgres + redis) up: ./scripts/infra.sh start && ./scripts/infra.sh init

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$PROJECT_ROOT/.venv"
APP="app.main:my_app"
PORT="${WATCHLIST_PORT:-8000}"
MOCK_PORT="${WATCHLIST_MOCK_PORT:-9100}"
PIDFILE="$SCRIPT_DIR/.watchlist.pid"
LOGFILE="$SCRIPT_DIR/.watchlist.log"

CMD="${1:-status}"

# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------

check_venv() {
    if [ ! -x "$VENV/bin/uvicorn" ]; then
        echo "Error: venv not found at $VENV (uvicorn missing)."
        echo "  python3 -m venv $VENV && $VENV/bin/pip install -r $PROJECT_ROOT/requirements.txt"
        exit 1
    fi
}

check_env() {
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo "Warning: $PROJECT_ROOT/.env missing — the app will fail to import."
        echo "  cp $PROJECT_ROOT/.env_example $PROJECT_ROOT/.env   # then fill it"
    fi
}

get_pid()    { [ -f "$PIDFILE" ] && cat "$PIDFILE"; }
is_running() { local p; p="$(get_pid)"; [ -n "$p" ] && kill -0 "$p" 2>/dev/null; }

# Mode mock : redirige TMDB/OMDB vers le serveur mock local (./scripts/mock.sh),
# pour que GET /movies/ marche sans clé API. Non destructif : on exporte des
# variables d'env qui priment sur .env (précédence pydantic-settings), sans
# toucher au fichier. Décision : WATCHLIST_MOCK=1/0 explicite prioritaire ;
# sinon "auto" → ON si les clés du .env sont encore des placeholders (CHANGE_ME).
maybe_enable_mock() {
    local want="${WATCHLIST_MOCK:-auto}"
    if [ "$want" = "auto" ]; then
        if grep -qE '^AUTHORIZATION=.*CHANGE_ME' "$PROJECT_ROOT/.env" 2>/dev/null; then
            want=1
        else
            want=0
        fi
    fi
    [ "$want" = "1" ] || return 0

    export TMDB_URL="http://localhost:$MOCK_PORT/"
    export OMDB_URL="http://localhost:$MOCK_PORT/"
    export AUTHORIZATION="mock-token"
    export OMDB_API_KEY="mock-key"
    echo "[watchlist] mode MOCK activé — TMDB/OMDB → http://localhost:$MOCK_PORT"
    if ! curl -sf "http://localhost:$MOCK_PORT/health" >/dev/null 2>&1; then
        echo "[watchlist]   ⚠ serveur mock injoignable sur :$MOCK_PORT — démarre l'infra : ./scripts/infra.sh start"
        echo "[watchlist]     (ou le mock seul : ./scripts/infra.sh mock start)"
    fi
}

print_endpoints() {
    echo "  URL:  http://localhost:$PORT"
    echo "  Docs: http://localhost:$PORT/docs"
}

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

app_dev() {
    check_venv
    check_env
    if is_running; then
        echo "[watchlist] a background instance is running (PID $(get_pid))."
        echo "Stop it first with: $0 stop"
        exit 1
    fi
    maybe_enable_mock
    echo "[watchlist] dev mode on port $PORT (foreground, --reload). Press Ctrl+C to stop."
    echo ""
    cd "$PROJECT_ROOT"
    exec "$VENV/bin/uvicorn" "$APP" --host 0.0.0.0 --port "$PORT" --reload
}

# Force le mode mock puis lance l'app en dev — évite d'exporter WATCHLIST_MOCK
# à la main. NE démarre PAS le serveur mock : ça, c'est le rôle de l'infra
# (./scripts/infra.sh start, ou ./scripts/infra.sh mock start). Si le serveur
# n'écoute pas, maybe_enable_mock (via app_dev) l'indique.
app_mock() {
    export WATCHLIST_MOCK=1
    app_dev
}

app_start() {
    check_venv
    check_env
    if is_running; then
        echo "[watchlist] already running (PID $(get_pid), port $PORT)."
        return
    fi
    maybe_enable_mock
    echo "[watchlist] starting on port $PORT (background)..."
    (
        cd "$PROJECT_ROOT"
        nohup "$VENV/bin/uvicorn" "$APP" --host 0.0.0.0 --port "$PORT" > "$LOGFILE" 2>&1 &
        echo $! > "$PIDFILE"
    )
    sleep 2
    if is_running; then
        echo "[watchlist] started (PID $(get_pid))."
        print_endpoints
        echo "  Logs: $0 logs"
    else
        echo "[watchlist] failed to start. Check logs: $LOGFILE"
        rm -f "$PIDFILE"
        exit 1
    fi
}

app_stop() {
    if ! is_running; then
        echo "[watchlist] not running."
        rm -f "$PIDFILE"
        return
    fi
    local pid; pid="$(get_pid)"
    echo "[watchlist] stopping (PID $pid)..."
    kill "$pid" 2>/dev/null || true
    local n=0
    while kill -0 "$pid" 2>/dev/null && [ $n -lt 10 ]; do sleep 1; n=$((n + 1)); done
    if kill -0 "$pid" 2>/dev/null; then
        echo "[watchlist] force killing..."
        kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$PIDFILE"
    echo "[watchlist] stopped."
}

app_status() {
    if is_running; then
        echo "[watchlist] running (PID $(get_pid), port $PORT)."
        print_endpoints
    else
        echo "[watchlist] not running."
        rm -f "$PIDFILE"
    fi
}

app_logs() {
    if [ -f "$LOGFILE" ]; then
        tail -f "$LOGFILE"
    else
        echo "[watchlist] no log file at $LOGFILE. Start it first with: $0 start"
    fi
}

# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

case "$CMD" in
    dev)     app_dev ;;
    mock)    app_mock ;;
    start)   app_start ;;
    stop)    app_stop ;;
    restart) app_stop; sleep 1; app_start ;;
    status)  app_status ;;
    logs)    app_logs ;;
    *)
        echo "Usage: $0 [dev|mock|start|stop|restart|status|logs]"
        echo ""
        echo "  dev      Start in foreground with --reload (Ctrl+C to stop)"
        echo "  mock     Like 'dev' but forces MOCK mode (GET /movies/ without API keys)."
        echo "           The mock server itself is run by the infra: ./scripts/infra.sh start"
        echo "  start    Start in background"
        echo "  stop     Stop the background instance"
        echo "  restart  Restart the background instance"
        echo "  status   Show status (default)"
        echo "  logs     Follow the background log"
        exit 1 ;;
esac
