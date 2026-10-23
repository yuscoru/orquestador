# Pi team configuration templates

These templates capture portable, non-secret team configuration. They are not a backup of
credentials, model stores, binaries, live session state or machine-specific runtime paths.

- `AGENTS.md`: role instructions used by the team.
- `settings.example.json`: package/skill settings; review absolute paths before copying to a new pod.
- `trust.example.json`: project trust templates; review paths before copying.

Never copy `.pi-team/env.sh` (contains credentials), `models-store.json`, role `bin/`, or the live
`team-session` marker into Git. Keep credentials in root-only secret storage. Generated integration
caches and live sessions remain ephemeral.
