#!/bin/bash

# WatchList — serveur mock des APIs TMDB/OMDB (outillage d'entretien).
# Permet à GET /movies/ de fonctionner SANS clé API : l'app est lancée en
# mode mock (voir ./scripts/run.sh) et ses appels TMDB/OMDB atterrissent ici.
#
# Usage: ./scripts/mock.sh [dev|start|stop|restart|status|logs]   (défaut: status)
#   dev      → premier plan (--reload), Ctrl+C pour arrêter
#   start    → arrière-plan ; PID + log sous scripts/.mock.{pid,log}
#   stop|restart|status|logs → gèrent l'instance d'arrière-plan
#
# Port : $WATCHLIST_MOCK_PORT (défaut 9100). Docs : http://localhost:9100/docs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$PROJECT_ROOT/.venv"
APP="mock_apis:mock_app"
PORT="${WATCHLIST_MOCK_PORT:-9100}"
PIDFILE="$SCRIPT_DIR/.mock.pid"
LOGFILE="$SCRIPT_DIR/.mock.log"

CMD="${1:-status}"

check_venv() {
    if [ ! -x "$VENV/bin/uvicorn" ]; then
        echo "Error: venv introuvable ($VENV/bin/uvicorn manquant)."
        echo "  python3 -m venv $VENV && $VENV/bin/pip install -r $PROJECT_ROOT/requirements.txt"
        exit 1
    fi
}

get_pid()    { [ -f "$PIDFILE" ] && cat "$PIDFILE"; }
is_running() { local p; p="$(get_pid)"; [ -n "$p" ] && kill -0 "$p" 2>/dev/null; }

print_endpoints() {
    echo "  Mock TMDB/OMDB : http://localhost:$PORT   (health: /health, docs: /docs)"
    echo "  App en mode mock :  ./scripts/run.sh dev  (auto)  ou  ./scripts/run.sh mock  (forcé)"
}

# --app-dir met scripts/ sur le sys.path → `import mock_apis` (standalone, ne
# dépend pas de app/ ni de .env).
mock_dev() {
    check_venv
    if is_running; then
        echo "[mock] une instance d'arrière-plan tourne déjà (PID $(get_pid)). $0 stop d'abord."
        exit 1
    fi
    echo "[mock] dev sur le port $PORT (premier plan, --reload). Ctrl+C pour arrêter."
    exec "$VENV/bin/uvicorn" "$APP" --app-dir "$SCRIPT_DIR" --host 0.0.0.0 --port "$PORT" --reload
}

mock_start() {
    check_venv
    if is_running; then
        echo "[mock] déjà lancé (PID $(get_pid), port $PORT)."
        print_endpoints
        return
    fi
    echo "[mock] démarrage sur le port $PORT (arrière-plan)..."
    (
        nohup "$VENV/bin/uvicorn" "$APP" --app-dir "$SCRIPT_DIR" --host 0.0.0.0 --port "$PORT" \
            > "$LOGFILE" 2>&1 &
        echo $! > "$PIDFILE"
    )
    sleep 2
    if is_running; then
        echo "[mock] lancé (PID $(get_pid))."
        print_endpoints
    else
        echo "[mock] échec au démarrage. Logs : $LOGFILE"
        rm -f "$PIDFILE"
        exit 1
    fi
}

mock_stop() {
    if ! is_running; then
        echo "[mock] non lancé."
        rm -f "$PIDFILE"
        return
    fi
    local pid; pid="$(get_pid)"
    echo "[mock] arrêt (PID $pid)..."
    kill "$pid" 2>/dev/null || true
    local n=0
    while kill -0 "$pid" 2>/dev/null && [ $n -lt 10 ]; do sleep 1; n=$((n + 1)); done
    kill -9 "$pid" 2>/dev/null || true
    rm -f "$PIDFILE"
    echo "[mock] arrêté."
}

mock_status() {
    if is_running; then
        echo "[mock] en cours (PID $(get_pid), port $PORT)."
        print_endpoints
    else
        echo "[mock] non lancé."
        rm -f "$PIDFILE"
    fi
}

mock_logs() {
    if [ -f "$LOGFILE" ]; then tail -f "$LOGFILE"; else echo "[mock] pas de log ($LOGFILE). $0 start d'abord."; fi
}

case "$CMD" in
    dev)     mock_dev ;;
    start)   mock_start ;;
    stop)    mock_stop ;;
    restart) mock_stop; sleep 1; mock_start ;;
    status)  mock_status ;;
    logs)    mock_logs ;;
    *)
        echo "Usage: $0 [dev|start|stop|restart|status|logs]"
        exit 1 ;;
esac
