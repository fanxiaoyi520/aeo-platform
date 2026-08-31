#!/usr/bin/env bash
# Backup PostgreSQL + Chroma volumes for production compose (M06 §5).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="infra/compose/docker-compose.prod.yml"
ENV_FILE=".env.prod"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${ROOT}/backups/${TIMESTAMP}"

cd "$ROOT"

compose() {
  if [[ -f "$ENV_FILE" ]]; then
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
  else
    docker compose -f "$COMPOSE_FILE" "$@"
  fi
}

if ! compose ps --status running --services 2>/dev/null | grep -qx postgres; then
  echo "Error: postgres service is not running. Start prod stack first: ./scripts/prod-up.ps1" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"

echo "==> Backing up PostgreSQL to ${BACKUP_DIR}/postgres.sql"
compose exec -T postgres pg_dump -U aeo -d aeo --clean --if-exists > "${BACKUP_DIR}/postgres.sql"

echo "==> Backing up Chroma data to ${BACKUP_DIR}/chroma_data.tar.gz"
compose exec -T api tar czf - -C /app/data/chroma . > "${BACKUP_DIR}/chroma_data.tar.gz"

cat > "${BACKUP_DIR}/manifest.txt" <<EOF
timestamp=${TIMESTAMP}
postgres=postgres.sql
chroma=chroma_data.tar.gz
compose_file=${COMPOSE_FILE}
EOF

echo "==> Backup complete: ${BACKUP_DIR}"
ls -lh "${BACKUP_DIR}"
