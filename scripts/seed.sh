#!/bin/bash

# WatchList — (re)seed de la base applicative avec des données de démo.
# Remet la base `watchlist` dans un ÉTAT INITIAL connu : 2 users + leurs films.
# Idempotent : relancer redonne le même état (TRUNCATE puis ré-insertion).
#
# Usage:
#   ./scripts/seed.sh            # reset + seed
#   ./scripts/seed.sh -h|--help  # aide
#
# Écrit dans la base RÉELLE de l'app (pas `watchlist_test`).
# Prérequis : infra up + migrations appliquées
#   ./scripts/infra.sh start && ./scripts/infra.sh init

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$PROJECT_ROOT/.venv"
PYTHON="$VENV/bin/python"

CONTAINER_POSTGRES="watchlist-postgres"

usage() {
    cat <<EOF
WatchList — seed / reset des données de démo

Usage: ./scripts/seed.sh [-h|--help]

Remet la base applicative \`watchlist\` dans un état initial connu :
  - vide les 3 tables (users, watched, to-watch),
  - recrée 2 utilisateurs (alice@watchlist.dev, bob@watchlist.dev),
    mot de passe commun : Password_1,
  - leur attribue des films « vus » et « à voir ».

Idempotent : relancer redonne exactement le même état.
Handled for you : venv présent, ../.env présent, postgres up.
EOF
}

case "${1:-}" in
    -h | --help | help) usage; exit 0 ;;
esac

# ---------------------------------------------------------------------------
# Preconditions (même logique que test.sh)
# ---------------------------------------------------------------------------

if [ ! -x "$PYTHON" ]; then
    echo "Error: python introuvable dans le venv ($PYTHON)."
    echo "  python3 -m venv $VENV && $VENV/bin/pip install -r $PROJECT_ROOT/requirements.txt"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Error: $PROJECT_ROOT/.env manquant (le seed lit les réglages DB dedans)."
    exit 1
fi

if [ "$(docker inspect --format '{{.State.Running}}' "$CONTAINER_POSTGRES" 2>/dev/null)" != "true" ]; then
    echo "Error: le conteneur PostgreSQL ne tourne pas. Démarre-le d'abord :"
    echo "  ./scripts/infra.sh start && ./scripts/infra.sh init"
    exit 1
fi

# ---------------------------------------------------------------------------
# Run — PYTHONPATH=racine pour que `import app` fonctionne depuis scripts/
# ---------------------------------------------------------------------------

cd "$PROJECT_ROOT"
exec env PYTHONPATH="$PROJECT_ROOT" "$PYTHON" scripts/seed.py
