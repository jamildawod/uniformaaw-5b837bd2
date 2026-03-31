#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/opt/uniforma"
TOOLS_DIR="$BASE_DIR/tools"

# ================================
# CLEAN HELP (kort + tydlig)
# ================================
print_help() {
cat <<EOT

🧠 hjälpuniforma (CLI)

status       → snabb översikt
system       → full systemdiagnos
backend      → analysera backend
frontend     → analysera frontend
all          → kör allt

whereami     → visa projektläge
ports        → visa portar
logs         → docker/loggar
env          → env variabler

build-check  → testa build
health       → api check
docker       → container status

EOT
}

# ================================
# COMMANDS
# ================================

run_status() {
  echo "=== STATUS ==="
  git -C "$BASE_DIR" status --short 2>/dev/null || echo "ingen git"
}

run_system() {
  bash "$TOOLS_DIR/diagnose_system.sh"
}

run_backend() {
  bash "$TOOLS_DIR/inspect_backend.sh" "${1:-$BASE_DIR/backend}"
}

run_frontend() {
  bash "$TOOLS_DIR/inspect_frontend.sh" "${1:-$BASE_DIR/frontend}"
}

run_whereami() {
  echo "=== WHERE ==="
  ls "$BASE_DIR"
}

run_ports() {
  lsof -iTCP -sTCP:LISTEN -P || true
}

run_logs() {
  docker ps -a || true
}

run_env() {
  env | grep -E 'NODE|API|DB|PORT' || true
}

run_build_check() {
  cd "$BASE_DIR/frontend" && npm run build || echo "fail"
}

run_health() {
  curl -s http://localhost:8000/health || echo "api nere"
}

run_docker() {
  docker ps -a || true
}

# ================================
# ROUTER
# ================================

CMD="${1:-help}"

case "$CMD" in
  help|"") print_help ;;

  status) run_status ;;
  system) run_system ;;
  backend) run_backend "$2" ;;
  frontend) run_frontend "$2" ;;
  all)
    run_system
    run_backend
    run_frontend
    ;;

  whereami) run_whereami ;;
  ports) run_ports ;;
  logs) run_logs ;;
  env) run_env ;;

  build-check) run_build_check ;;
  health) run_health ;;
  docker) run_docker ;;

  *)
    echo "❌ okänt: $CMD"
    print_help
    ;;
esac
