#!/usr/bin/env bash
# Start one SOAR+ role as a Pi agent on the pi-link network.
#
#   pi/launch.sh <role> [extra pi args...]
#
# <role> is `admiral` or a worker from the "Pi team" table in
# protocols/worker-registry.md. Each role gets its own Pi agent directory
# (its own AGENTS.md, settings and sessions), the closest equivalent to the
# per-role container of a Docker setup. See pi/team.md.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

[[ $# -ge 1 ]] || die "usage: launch.sh <role> [pi args...]"
ROLE="$1"; shift
grep -qx "$ROLE" < <(all_roles) || die "unknown role '$ROLE' (known: $(all_roles | tr '\n' ' '))"

# One session per role: a second one would get a suffixed link name and share the role's repository.
link_taken() { curl -sf --max-time 1 127.0.0.1:9900/status | grep -q "\"name\":\"$ROLE@$GROUP\""; }
for _ in 1 2 3; do link_taken || break; sleep 1; done # a restarted role may still be listed briefly
link_taken && die "'$ROLE' is already connected to pi-link; to open it use: pi/team.sh attach $ROLE"

case "$ROLE" in
  admiral) KIND="admiral"; REPO="soarplus-dev-orchestration"; REPO_PATH="$ORCH" ;;
  *) KIND="worker"
     REPO="$(registry_field "$ROLE" 3)"
     REPO_PATH="$(repo_path "$REPO")"
     [[ -d "$REPO_PATH/.git" ]] || die "repository '$REPO' not found at '${REPO_PATH:-?}'" ;;
esac

PI_LINK_PKG="$HOME/.pi/agent/npm/node_modules/pi-link"
[[ -d "$PI_LINK_PKG" ]] || die "pi-link is not installed; run: pi install npm:pi-link@0.5.2"

AGENT_DIR="$PI_TEAM_HOME/$ROLE"
mkdir -p "$AGENT_DIR"

# One login for the whole team: log in once with plain `pi`, then every role reuses it.
[[ -e "$HOME/.pi/agent/auth.json" ]] && ln -sfn "$HOME/.pi/agent/auth.json" "$AGENT_DIR/auth.json"
if [[ -d "$REPO_PATH/.github/skills" ]]; then
  # Repo-provided Pi skills (e.g. feature-delivery): Pi does not scan .github/skills by itself.
  printf '{ "packages": ["%s"], "skills": ["%s"] }\n' "$PI_LINK_PKG" "$REPO_PATH/.github/skills" > "$AGENT_DIR/settings.json"
else
  printf '{ "packages": ["%s"] }\n' "$PI_LINK_PKG" > "$AGENT_DIR/settings.json"
fi

cat "$ORCH/pi/team.md" "$ORCH/pi/roles/$KIND.md" \
  | sed -e "s|{{ROLE}}|$ROLE|g" -e "s|{{GROUP}}|$GROUP|g" -e "s|{{ORCH}}|$ORCH|g" \
        -e "s|{{REPO}}|$REPO|g" -e "s|{{REPO_PATH}}|$REPO_PATH|g" \
  > "$AGENT_DIR/AGENTS.md"

export PI_CODING_AGENT_DIR="$AGENT_DIR" SOARPLUS_ROLE="$ROLE" SOARPLUS_ORCH="$ORCH"
cd "$REPO_PATH"
# The session is the team's current one (pi/team.sh session), created on first use, resumed after.
LABEL="$(team_session)"
exec pi --link-name "$ROLE@$GROUP" --name "$ROLE ($LABEL)" --session-id "$LABEL-$ROLE" "$@"
