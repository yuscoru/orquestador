#!/usr/bin/env bash
# Run the SOAR+ team of Pi agents as windows of one tmux session.
#
#   pi/team.sh up                 start every role, admiral first (it becomes the pi-link hub)
#   pi/team.sh down               stop every role
#   pi/team.sh status             is everything up? per-role table; exit 1 if not
#   pi/team.sh attach [role]      open a role; each terminal keeps its own role (without a role: the shared session)
#   pi/team.sh watch              all roles at once, tiled and live
#   pi/team.sh start|stop|restart <role>
#   pi/team.sh session list|current|new [label]|resume <label> [--force]
#                                 every role switches together to a new or an earlier session
#
# tmux keeps the agents alive when VS Code disconnects. Detach with Ctrl-b d.
# Nothing starts by itself: after a pod restart run `up` (it reinstalls tmux if it is gone).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

SESSION="${SOARPLUS_TMUX_SESSION:-soarplus}"
S="=$SESSION" # exact match: plain names would also match the soarplus-view-* and -tile-* sessions

valid_role() { grep -qx "$1" < <(all_roles) || die "unknown role '$1' (known: $(all_roles | tr '\n' ' '))"; }
need_tmux() { command -v tmux >/dev/null || die "tmux is not installed; run: pi/team.sh up"; }
has_session() { tmux has-session -t "$S" 2>/dev/null; }
has_window() { tmux list-windows -t "$S" -F '#{window_name}' 2>/dev/null | grep -qx "$1"; }
pane_dead() { [[ "$(tmux display -p -t "$S:$1" '#{pane_dead}')" == "1" ]]; }
hub_status() { curl -sf --max-time 2 127.0.0.1:9900/status; }

# tmux lives outside /root, so it disappears when the container is recreated.
ensure_tmux() {
  if ! command -v tmux >/dev/null; then
    echo "tmux is missing (lost with the container); installing it with apt-get"
    apt-get install -y --no-install-recommends tmux >/dev/null 2>&1 \
      || { apt-get update -qq && apt-get install -y --no-install-recommends tmux >/dev/null; } \
      || die "could not install tmux"
  fi
  grep -qs 'extended-keys on' "$HOME/.tmux.conf" || echo 'set -g extended-keys on' >> "$HOME/.tmux.conf"
  grep -qs 'extended-keys-format' "$HOME/.tmux.conf" || echo 'set -g extended-keys-format csi-u' >> "$HOME/.tmux.conf"
  # Pi runs inline, so a conversation's history is tmux's scrollback; the default keeps only 2000 lines.
  grep -qs 'history-limit' "$HOME/.tmux.conf" || echo 'set -g history-limit 50000' >> "$HOME/.tmux.conf"
  grep -qs 'set -g mouse' "$HOME/.tmux.conf" || echo 'set -g mouse on' >> "$HOME/.tmux.conf"
}

start_role() {
  local role="$1" cmd="$ORCH/pi/launch.sh $1"
  if ! has_session; then
    tmux new-session -d -s "$SESSION" -n "$role" -c "$ORCH" "$cmd"
  elif ! has_window "$role"; then
    tmux new-window -d -t "$S:" -n "$role" -c "$ORCH" "$cmd"
  elif pane_dead "$role"; then
    tmux respawn-window -k -t "$S:$role" "$cmd"
  else
    echo "$role: already running"; return
  fi
  # Keep a crashed agent's window (and its error) instead of letting it vanish.
  tmux set-option -w -t "$S:$role" remain-on-exit on
  echo "$role: started"
}

stop_role() {
  has_window "$1" && tmux kill-window -t "$S:$1" && echo "$1: stopped" || echo "$1: not running"
}

# $1 is an extended regex over the extra sessions' suffix; view-* back `attach`, tile-*/watch back `watch`.
kill_extra_sessions() {
  tmux list-sessions -F '#{session_name}' 2>/dev/null | grep -E "^$SESSION-($1)" \
    | while read -r name; do tmux kill-session -t "=$name" 2>/dev/null; done || true
}

# One line per connected terminal: "<link name> <status>".
roster() {
  hub_status 2>/dev/null | python3 -c 'import sys, json
for t in json.load(sys.stdin)["terminals"]:
    print(t["name"], t.get("status", "?"))' 2>/dev/null || true
}

# Team sessions known on disk, newest first: "<epoch> <label>". The admiral's file names them.
list_sessions() {
  local f base
  for f in "$PI_TEAM_HOME"/admiral/sessions/*/*.jsonl; do
    [[ -e "$f" ]] || continue
    base="${f##*/}"; base="${base#*_}"; base="${base%.jsonl}"
    echo "$(stat -c %Y "$f") ${base%-admiral}"
  done | sort -rn
}

show_sessions() {
  local current epoch label
  current="$(team_session)"
  printf '  %-24s %s\n' SESSION 'LAST ACTIVITY (admiral)'
  while read -r epoch label; do
    printf '%s %-24s %s\n' "$([[ "$label" == "$current" ]] && echo '*' || echo ' ')" "$label" "$(date -d "@$epoch" '+%F %H:%M')"
  done < <(list_sessions)
  echo "(* = in use)"
}

# Workers that are in the roster and not idle, as "role (status)".
busy_workers() {
  roster | awk -v g="@$GROUP" '{ n = $1; sub(g "$", "", n); if (n != "admiral" && $2 != "idle") print n " (" $2 ")" }'
}

# Point the whole team at <label> and restart every running role on it.
switch_session() {
  local label="$1" force="${2:-}" busy role
  busy="$(busy_workers)"
  if [[ -n "$busy" && "$force" != --force ]]; then
    die "not switching, still working: $(tr '\n' ' ' <<<"$busy")(wait for them, or --force)"
  fi
  mkdir -p "$PI_TEAM_HOME"
  echo "$label" > "$PI_TEAM_HOME/team-session"
  echo "team session: $label"
  has_session || { echo "team not running; pi/team.sh up will use it"; return 0; }
  for role in $(registry_workers); do
    if has_window "$role"; then stop_role "$role"; start_role "$role"; fi
  done
  has_window admiral || return 0
  if [[ "${SOARPLUS_ROLE:-}" == admiral ]]; then
    # Restarting the admiral kills the process running this script, so tmux does it instead.
    tmux run-shell -b "sleep 3; '$ORCH/pi/team.sh' restart admiral"
    echo "admiral restarts in 3 s on session '$label'"
  else
    stop_role admiral; start_role admiral
  fi
}

session_cmd() {
  local label
  case "${1:-}" in
    list) show_sessions ;;
    current) team_session ;;
    new)
      label="${2:-s$(date +%Y%m%d-%H%M)}"
      [[ "$label" =~ ^[A-Za-z0-9.-]+$ ]] || die "invalid label '$label' (letters, digits, '.' and '-')"
      if list_sessions | awk '{ print $2 }' | grep -qx "$label"; then die "session '$label' already exists; use: session resume $label"; fi
      switch_session "$label" "${3:-}" ;;
    resume)
      label="${2:?label (see: session list)}"
      list_sessions | awk '{ print $2 }' | grep -qx "$label" || die "no session '$label' (see: session list)"
      switch_session "$label" "${3:-}" ;;
    *) die "usage: team.sh session list|current|new [label]|resume <label> [--force]" ;;
  esac
}

show_status() {
  local connected ok=1 role tstate link
  command -v tmux >/dev/null || { echo "tmux is not installed; run: pi/team.sh up"; return 1; }
  connected="$(roster)"
  has_session || echo "tmux session '$SESSION' is not running"
  [[ -n "$connected" ]] || echo "no pi-link hub on :9900"
  printf '%-10s %-9s %s\n' ROLE TMUX LINK
  for role in $(all_roles); do
    if ! has_session || ! has_window "$role"; then tstate=missing
    elif pane_dead "$role"; then tstate=DEAD
    else tstate=running; fi
    link="$(awk -v n="$role@$GROUP" '$1 == n { print $2 }' <<<"$connected")"
    if [[ -n "$link" ]]; then link="connected ($link)"; else link="NOT connected"; fi
    printf '%-10s %-9s %s\n' "$role" "$tstate" "$link"
    [[ "$tstate" == running && "$link" != "NOT connected" ]] || ok=0
  done
  if (( ok )); then echo "OK: the whole team is up and connected"
  else echo "INCOMPLETE: start it with: pi/team.sh up  (a role 'running' but NOT connected is stuck, e.g. waiting on a prompt: pi/team.sh attach <role>)"; return 1; fi
}

# Clients of one session all follow its current window. A grouped session shares the windows but
# keeps its own current one, so every terminal (and every tile) can sit on a different role.
attach_role() {
  local view="$SESSION-view-$1"
  has_window "$1" || die "role '$1' is not running; run: pi/team.sh start $1"
  tmux has-session -t "=$view" 2>/dev/null || tmux new-session -d -t "$S" -s "$view"
  tmux select-window -t "=$view:$1"
  exec tmux attach -t "=$view"
}

watch_team() {
  has_session || die "team not running; run: pi/team.sh up"
  kill_extra_sessions 'tile-|watch$'
  local role first=1 tile
  for role in $(all_roles); do
    has_window "$role" || continue
    tile="$SESSION-tile-$role"
    tmux new-session -d -t "$S" -s "$tile"
    tmux select-window -t "=$tile:$role"
    tmux set-option -t "$tile" status off
    if (( first )); then
      tmux new-session -d -s "$SESSION-watch" "TMUX= tmux attach -t =$tile"; first=0
    else
      tmux split-window -t "$SESSION-watch" "TMUX= tmux attach -t =$tile"
      tmux select-layout -t "$SESSION-watch" tiled
    fi
  done
  (( first )) && die "no role is running"
  # Mouse only in this view (Shift+drag still selects text): click a tile to focus it.
  tmux set-option -t "$SESSION-watch" mouse on
  tmux set-option -t "$SESSION-watch" status-right "click: pane | Ctrl-b arrows: pane | Ctrl-b z: zoom | Ctrl-b d: leave"
  exec tmux attach -t "=$SESSION-watch"
}

case "${1:-}" in
  up)
    ensure_tmux
    for role in $(all_roles); do
      start_role "$role"
      # The first role to connect becomes the hub; give admiral time to take it.
      if [[ "$role" == admiral ]]; then
        for _ in $(seq 1 20); do hub_status >/dev/null && break; sleep 1; done
      fi
    done ;;
  down)
    need_tmux
    kill_extra_sessions 'view-|tile-|watch$'
    has_session && tmux kill-session -t "$S" && echo "team stopped" || echo "team not running" ;;
  status) show_status ;;
  attach)
    need_tmux
    has_session || die "team not running; run: pi/team.sh up"
    if [[ -n "${2:-}" ]]; then valid_role "$2"; attach_role "$2"; fi
    exec tmux attach -t "$S" ;;
  watch)   need_tmux; watch_team ;;
  start)   need_tmux; valid_role "${2:?role}"; start_role "$2" ;;
  stop)    need_tmux; valid_role "${2:?role}"; stop_role "$2" ;;
  restart) need_tmux; valid_role "${2:?role}"; stop_role "$2"; start_role "$2" ;;
  session) session_cmd "${@:2}" ;;
  *) die "usage: team.sh up|down|status|attach [role]|watch|start|stop|restart <role>|session ..." ;;
esac
