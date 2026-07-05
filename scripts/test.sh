#!/bin/bash

# WatchList — run the test suite, a file, or a single test, via the project venv.
# Usage:
#   ./scripts/test.sh                                   # all tests
#   ./scripts/test.sh delete                            # tests matching -k "delete"
#   ./scripts/test.sh tests/test_watched.py             # one file
#   ./scripts/test.sh tests/test_watched.py::test_delete_watched_movie   # one test
#   ./scripts/test.sh -k "delete and not owns" -v       # raw pytest args (start with -)
# Extra pytest flags can always be appended:  ./scripts/test.sh delete -s
#
# Ensures: pytest in venv, ../.env present, postgres up, and the <db>_test database exists.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$PROJECT_ROOT/.venv"
PYTEST="$VENV/bin/pytest"

CONTAINER_POSTGRES="watchlist-postgres"
PG_USER="postgres"
PG_DB="watchlist"
TEST_DB="${PG_DB}_test"

# ---------------------------------------------------------------------------
# Help (short-circuits before preconditions — no Docker/venv needed)
# ---------------------------------------------------------------------------

usage() {
    cat <<EOF
WatchList — test runner (pytest via the project venv)

Usage: ./scripts/test.sh [selector] [extra pytest args]

  (no args)              run the whole suite
  <keyword>              run tests matching -k "<keyword>"
                         e.g. ./scripts/test.sh delete
  <path>[::test]         run a file or a single test
                         e.g. ./scripts/test.sh tests/test_watched.py::test_delete_watched_movie
  -<flag> ...            forward raw pytest args
                         e.g. ./scripts/test.sh -k "delete and not owns" -x
  -h, --help             show this help

Extra args are always forwarded to pytest:  ./scripts/test.sh delete -s
Handled for you: pytest present, ../.env present, postgres up, and the
${TEST_DB} database (created if missing).
EOF
}

case "${1:-}" in
    -h | --help | help) usage; exit 0 ;;
esac

# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------

if [ ! -x "$PYTEST" ]; then
    echo "Error: pytest not found in venv ($PYTEST)."
    echo "  $VENV/bin/pip install -r $PROJECT_ROOT/requirements.txt"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Error: $PROJECT_ROOT/.env missing (tests read the DB settings from it)."
    exit 1
fi

if [ "$(docker inspect --format '{{.State.Running}}' "$CONTAINER_POSTGRES" 2>/dev/null)" != "true" ]; then
    echo "Error: PostgreSQL container is not running. Start it first:"
    echo "  ./scripts/infra.sh start"
    exit 1
fi

# The test suite targets a separate <db>_test database (see tests/conftest.py).
# create_all() builds the tables, not the database itself — so ensure it exists.
if ! docker exec "$CONTAINER_POSTGRES" psql -U "$PG_USER" -tAc \
        "SELECT 1 FROM pg_database WHERE datname='$TEST_DB'" | grep -q 1; then
    echo "Creating test database $TEST_DB..."
    docker exec "$CONTAINER_POSTGRES" createdb -U "$PG_USER" "$TEST_DB"
fi

# ---------------------------------------------------------------------------
# Build pytest args and run (always verbose)
# ---------------------------------------------------------------------------
# No args        → whole suite.
# First token is a flag (-x) or a path / node-id (has "/", "::" or ends in .py)
#                → forward all args verbatim.
# Otherwise      → treat the first token as a -k keyword expression, forward the rest.

cd "$PROJECT_ROOT"

if [ "$#" -eq 0 ]; then
    exec "$PYTEST" -v
fi

case "$1" in
    -* | */* | *.py | *::*)
        exec "$PYTEST" -v "$@" ;;
    *)
        keyword="$1"; shift
        exec "$PYTEST" -v -k "$keyword" "$@" ;;
esac
