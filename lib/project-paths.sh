#!/usr/bin/env bash
# Source in a project. Each consumer supplies the checkout as the first argument.
load_project_paths() {
  local paths
  paths="$(python3 "$1/lib/project_config.py" "$1" paths)" || return 2
  # shellcheck disable=SC2034 # These variables are consumed by the sourcing script.
  {
    IFS= read -r TACK_ARCHITECTURE
    IFS= read -r TACK_PLANS
    IFS= read -r TACK_HANDOFFS
  } <<EOF
$paths
EOF
}
