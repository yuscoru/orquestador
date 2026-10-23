#!/usr/bin/env bash
# Shared helpers for pi/launch.sh and pi/team.sh. Source it, do not run it.

ORCH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY="$ORCH/protocols/worker-registry.md"
GROUP="${SOARPLUS_LINK_GROUP:-soarplus}"
PI_TEAM_HOME="${SOARPLUS_PI_HOME:-$HOME/.pi-team}"

die() { echo "${0##*/}: $*" >&2; exit 1; }

# The team session is a label shared by every role: role R keeps its conversation in the Pi
# session `<label>-R`. The pointer file holds the label in use; the default is the group, which
# is the id the first version of the launcher used, so older conversations keep working.
team_session() { cat "$PI_TEAM_HOME/team-session" 2>/dev/null || echo "$GROUP"; }

# Rows of the "Pi team" table in the registry, the only place workers are defined.
registry_rows() {
  awk '/^# Pi team/ { f = 1; next } /^---/ { f = 0 } f && /^\| `/' "$REGISTRY"
}

registry_workers() {
  registry_rows | awk -F'|' '{ gsub(/[ `]/, "", $2); print $2 }'
}

# registry_field <worker> <column: 3 = repository>
registry_field() {
  registry_rows | awk -F'|' -v w="$1" -v c="$2" \
    '{ n = $2; gsub(/[ `]/, "", n); if (n == w) { v = $c; gsub(/^[ `]+|[ `]+$/, "", v); print v } }'
}

repo_path() {
  grep -E "^$1[[:space:]]+->" "$REGISTRY" | awk '{print $3}'
}

all_roles() {
  echo admiral
  registry_workers
}
