#!/usr/bin/env bash
set -euo pipefail

readonly OLD_DIST_NAME="mcp-stdio-python-template"
readonly OLD_PACKAGE_NAME="mcp_stdio_python_template"

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/rename-template.sh <new-project-name> [new_python_package_name]

Examples:
  bash scripts/rename-template.sh weather-mcp-server
  bash scripts/rename-template.sh weather-mcp-server weather_tools
USAGE
}

fail() {
  printf 'rename-template: %s\n' "$1" >&2
  exit 1
}

derive_package_name() {
  local dist_name="$1"

  printf '%s' "$dist_name" |
    tr '[:upper:]' '[:lower:]' |
    sed -E 's/[^a-z0-9]+/_/g; s/^_+//; s/_+$//; s/_+/_/g'
}

replace_in_text_files() {
  local new_dist_name="$1"
  local new_package_name="$2"

  while IFS= read -r -d '' file_path; do
    if grep -Iq . "$file_path"; then
      sed -i \
        -e "s/${OLD_DIST_NAME}/${new_dist_name}/g" \
        -e "s/${OLD_PACKAGE_NAME}/${new_package_name}/g" \
        "$file_path"
    fi
  done < <(
    find . -type f \
      ! -path './.git/*' \
      ! -path './.venv/*' \
      ! -path './.mypy_cache/*' \
      ! -path './.pytest_cache/*' \
      ! -path './.ruff_cache/*' \
      ! -path './__pycache__/*' \
      ! -path './*.egg-info/*' \
      ! -name '.env' \
      -print0
  )
}

rename_package_directory() {
  local new_package_name="$1"
  local old_package_dir="src/${OLD_PACKAGE_NAME}"
  local new_package_dir="src/${new_package_name}"

  if [[ ! -d "$old_package_dir" ]]; then
    fail "expected package directory '$old_package_dir' to exist"
  fi

  if [[ -e "$new_package_dir" ]]; then
    fail "target package path '$new_package_dir' already exists"
  fi

  mv "$old_package_dir" "$new_package_dir"
}

main() {
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    return 0
  fi

  local new_dist_name="${1:-}"
  local new_package_name="${2:-}"

  if [[ -z "$new_dist_name" ]]; then
    usage >&2
    return 2
  fi

  if [[ ! -f "pyproject.toml" || ! -d "src" ]]; then
    fail "run this script from the repository root"
  fi

  if [[ ! "$new_dist_name" =~ ^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$ ]]; then
    fail "project name must contain only letters, digits, '.', '_', and '-', and cannot start or end with punctuation"
  fi

  if [[ -z "$new_package_name" ]]; then
    new_package_name="$(derive_package_name "$new_dist_name")"
  fi

  if [[ ! "$new_package_name" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    fail "Python package name must be a valid module identifier"
  fi

  replace_in_text_files "$new_dist_name" "$new_package_name"
  rename_package_directory "$new_package_name"

  printf 'Renamed %s to %s\n' "$OLD_DIST_NAME" "$new_dist_name"
  printf 'Renamed %s to %s\n' "$OLD_PACKAGE_NAME" "$new_package_name"
}

main "$@"
