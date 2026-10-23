# Runbook — SystemDevAgent + API local + frontend en el pod

Fecha: 2026-10-21. Procedimiento para el piloto DEV de US 696, no para desplegar Kubernetes.

## 0. Elegir perfil antes de arrancar

Hay dos perfiles incompatibles:

| Perfil | API | Frontend | Agentes | Garantía de escritura |
|---|---|---|---|---|
| **Integrado SystemDevAgent** | normal/granted en `127.0.0.1:8001` | apunta a `8001`, login real | discovery e invoke habilitados | **NO es read-only** |
| **Quality segura** | launcher auditado en `127.0.0.1:8000` | apunta a `8000`, tokens sintéticos | discovery desactivado | escrituras PyMongo bloqueadas |

Este documento desarrolla el primer perfil. Para Quality read-only usar
[`RUNBOOK-local-quality-ui.md`](RUNBOOK-local-quality-ui.md). No mezclar launchers ni puertos.

> **Riesgo explícito.** `run_api_local_granted.py` carga la aplicación normal. Su arranque puede
> crear índices, ejecutar seeds/backfills o migraciones. `POST /invoke` persiste tareas y
> `sre_quality_eval` puede escribir `a2a_tasks.agent_eval_results` y avanzar checkpoints. Usar solo
> con autorización para operar contra la DocumentDB compartida. Los smoke GET/card no ejecutan una
> evaluación, aunque el runner puede asegurar índices durante su arranque.

## 1. Topología y prerequisitos

Procesos/terminales:

| Terminal | Proceso | Puerto |
|---|---|---:|
| A | `SystemDevAgent` A2A | 8080 |
| B | API local normal con grant acotado | 8001 |
| C | Next.js | 3000 |
| D | smokes/invoke/polling | — |

Checkouts esperados:

```bash
git -C /root/soarplus-agentics branch --show-current
git -C /root/soarplus-agentics rev-parse HEAD
# feature/696-sre-response-quality
# 5e720a3ebb2ebc766943e4dc45ca1af4b43c9b1f

git -C /root/soarplus-api branch --show-current
git -C /root/soarplus-api rev-parse HEAD
# feature/696-sre-response-quality
# f34bf9c48ab05a845e37dac5263048c64cec1a3d

git -C /root/soarplus-frontend-app1 branch --show-current
git -C /root/soarplus-frontend-app1 rev-parse HEAD
# feature/696-sre-response-quality
# 0032c688ff7db894e96c3d0a441c75334a40241f
```

Estos repositorios tienen modificaciones/untracked preexistentes. No usar `git clean`, `git reset`
ni `git add -A` como parte del runbook.

Herramientas y dependencias:

```bash
command -v uv
python3.12 --version
/root/soarplus-agentics/agents/callagent-orchestrator/.venv/bin/python --version
/root/soarplus-api/.venv/bin/python --version
export PATH="/root/.local/share/pi-node/current/bin:$PATH"
node --version
npm --version
```

El entorno `agents/callagent-orchestrator/.venv` debe conservarse: proporciona ADK 1.27.5,
Motor/Pydantic y dependencias evaluation al venv temporal mediante `.pth`.

Comprobar puertos antes de empezar:

```bash
ss -ltnp | grep -E ':(3000|8000|8001|8080)\b' || true
```

No continuar si un puerto necesario está ocupado sin identificar el proceso propietario.

## 2. Credenciales y datos requeridos

El pod debe tener, sin imprimir valores:

```bash
for name in API_DB_HOST API_DB_USER API_DB_PASS; do
  printenv "$name" >/dev/null || { echo "Falta $name" >&2; exit 1; }
done
```

Para el perfil integrado hacen falta además:

- `GRANT_USER_ID`: `user_id` real de la misma cuenta cuya API key se usará.
- Una API key real de esa cuenta, mantenida en una variable de shell (`MY_API_KEY`) y nunca en Git,
  chat, capturas o comandos guardados.
- El target de evaluación debe estar activo en
  `tools/sre-response-quality/targets.json`.

Introducir valores sensibles sin eco:

```bash
read -rp 'User id real para el grant local: ' GRANT_USER_ID
export GRANT_USER_ID
read -rsp 'API key de la misma cuenta: ' MY_API_KEY; echo
export MY_API_KEY
```

`GRANT_USER_ID` solo añade en memoria `system_agent.sre_quality_eval` a ese usuario. No lo hace
admin, no concede `quality.view` ni `agents.read_all`, y no cambia ownership. El polling debe usar
la misma identidad que creó la tarea (o un admin).

## 3. Estado de discovery verificado

El 2026-10-21 se comprobó en lectura que `soarplus-db.agent_registry` contiene:

```json
{
  "real_name": "dev-jcorujo-agent",
  "endpoint": "http://dev-jcorujo-agent.soarplus.svc.cluster.local:8080",
  "stale": false
}
```

El fallback no crea ni actualiza este documento. Después de arrancar el agente hay que verificar que
ese DNS/Service alcanza el proceso local. Si el documento cambia o desaparece, el flujo queda
bloqueado: no improvisar un write en la colección.

La identidad estable para URLs es `dev-jcorujo-agent`. La card anuncia el nombre lógico
`SystemDevAgent`; API acepta ambos cuando discovery ya pobló la caché, pero este runbook usa siempre
el `real_name` estable.

## 4. Reconstruir el venv temporal de SystemDevAgent

`/tmp` es efímero y tiene el espacio amplio del overlay. Tras recrear el pod hay que repetir esta
sección. `dev_pod.py` valida el venv, pero no lo crea.

El commit runner validado existe como objeto pero no es alcanzable desde las refs persistentes. Por
eso se crea un clon temporal, se trae el objeto por hash y se publica **solo dentro del clon temporal**
como `validated-runner`. No se modifica ninguna ref de `/root/soarplus-runner`.

El 2026-10-21 los pasos individuales siguientes se ejecutaron correctamente y produjeron un venv de
265 MiB más una fuente temporal de 776 KiB. El bloque completo desde `/tmp` vacío es una composición
de esos pasos; no se reejecutó una segunda vez de extremo a extremo.

Si ambos directorios existen, no borrarlos: saltar a la validación. Si solo existe uno, detenerse e
investigar el estado parcial.

```bash
set -euo pipefail
HASH=096ac69f2a9d20621f608c610d5f7b192cc15285
VENV=/tmp/sre-system-dev-venv
SRC=/tmp/sre-runner-source-096ac69f2a9d
PY="$VENV/bin/python"
SITE="$VENV/lib/python3.12/site-packages"

if [ -e "$VENV" ] || [ -e "$SRC" ]; then
  if [ -d "$VENV" ] && [ -d "$SRC" ]; then
    echo 'Entorno temporal existente: se validará sin reconstruir'
  else
    echo 'ERROR: estado temporal parcial; no se borra automáticamente' >&2
    exit 1
  fi
else
  uv venv "$VENV" --python 3.12
  mkdir -p "$SITE"
  printf '%s\n' \
    /root/soarplus-agentics/agents/callagent-orchestrator/.venv/lib/python3.12/site-packages \
    > "$SITE/00-callagent-site.pth"

  git clone --no-local /root/soarplus-runner "$SRC"
  git -C "$SRC" fetch /root/soarplus-runner "$HASH"
  git -C "$SRC" branch validated-runner "$HASH"
  test "$(git -C "$SRC" rev-parse refs/heads/validated-runner)" = "$HASH"

  uv pip install --python "$PY" --no-deps --reinstall \
    "soarplus-runner @ git+file://$SRC@validated-runner"

  uv pip install --python "$PY" \
    'litellm==1.82.5' \
    'pypdf==5.3.0' 'docx2txt==0.9' 'openpyxl==3.1.5' \
    'guardrails-ai>=0.6.0' \
    'guardrails-ai-secrets-present>=0.1.0' \
    'guardrails-ai-regex-match>=0.1.0' \
    'guardrails-ai-valid-json>=0.1.0' \
    'guardrails-ai-valid-length>=0.1.0' \
    'guardrails-ai-valid-url>=0.1.0' \
    'guardrails-ai-valid-html>=0.1.0' \
    'guardrails-ai-valid-sql>=0.1.0' \
    'guardrails-ai-exclude-sql-predicates>=0.1.0' \
    'guardrails-ai-ban-list>=0.1.0' \
    'guardrails-ai-detect-system-prompt-leakage>=0.1.0' \
    'guardrails-ai-web-sanitization>=0.1.0' \
    'guardrails-ai-has-url>=0.1.0' \
    'guardrails-ai-internal-domains>=0.1.0' \
    'guardrails-ai-unusual-prompt>=0.0.2' \
    'guardrails-ai-prompt-injection-detector>=0.0.2' \
    'guardrails-ai-llm-critic>=0.1.0'

  # ISS-006: mantener coherente toda la familia OTEL 1.38. Guardrails permite un rango amplio y,
  # sin el pin gRPC, puede resolver 1.45.1 contra SDK/HTTP 1.38.0 y romper su propio import.
  uv pip install --python "$PY" --reinstall \
    'packaging==26.3' \
    'python-dotenv==1.2.2' \
    'opentelemetry-exporter-otlp-proto-http==1.38.0' \
    'opentelemetry-exporter-otlp-proto-grpc==1.38.0'
fi
```

El commit no declara un extra `eval`; no añadir `[eval]`. ADK evaluation ya está disponible mediante
el `.pth` al venv compatible de callagent. No instalar runner editable desde HEAD, no usar `main` y
no crear una ref temporal en el repositorio persistente.

Validar metadata/imports:

```bash
HASH=096ac69f2a9d20621f608c610d5f7b192cc15285
PY=/tmp/sre-system-dev-venv/bin/python
"$PY" - "$HASH" <<'PY'
from importlib.metadata import distribution, version
import json, sys
expected = sys.argv[1]
p = distribution("soarplus-runner")
direct = json.loads(p.read_text("direct_url.json"))
commit = direct.get("vcs_info", {}).get("commit_id")
assert p.version == "0.1.2", p.version
assert direct.get("vcs_info", {}).get("vcs") == "git", direct
assert commit == expected, commit
assert version("google-adk") == "1.27.5"
assert version("motor") == "3.7.1"
assert version("pydantic") == "2.14.1"
assert version("litellm") == "1.82.5"
assert version("packaging") == "26.3"
assert version("python-dotenv") == "1.2.2"
for name in (
    "opentelemetry-exporter-otlp-proto-http",
    "opentelemetry-exporter-otlp-proto-grpc",
    "opentelemetry-sdk",
    "opentelemetry-api",
    "opentelemetry-proto",
    "opentelemetry-exporter-otlp-proto-common",
):
    assert version(name) == "1.38.0", (name, version(name))
assert version("opentelemetry-semantic-conventions") == "0.59b0"
from guardrails import Guard
from opentelemetry.sdk._logs import LogRecord
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
import a2a, google.adk, motor, pydantic, soarplus_runner
try:
    from opentelemetry.sdk._logs import ReadableLogRecord
except ImportError:
    pass  # esperado con SDK 1.38; gRPC 1.38 no intenta importarlo
else:
    raise AssertionError("familia OTEL inesperada: ReadableLogRecord exportado")
print("runner/imports OK", p.version, commit)
PY

uv pip check --python "$PY"
```

Esperado: `runner/imports OK 0.1.2 096ac69...` y `All installed packages are compatible`.
No ejecutar `pip freeze`: metadata de paquetes
preexistentes puede contener URLs de instalación sensibles.

## 5. Preflight de SystemDevAgent sin servir

> **Corrección operativa:** la prueba contable definitiva usa el modo estándar in-process. No usar
> `--user-judge-key` ni `--manual-dev-pilot`: ambos introducen el worker hijo y pueden dejar la
> contabilidad en `tracking_only`.

Provisionar primero una `OPENAI_API_KEY` rotada/aprobada en el entorno del proceso, sin imprimirla.
El preflight estándar no puede depender todavía de la key por request y falla si no existe esta key
de proceso. No usar placeholders al servir.

```bash
cd /root/soarplus-agentics/specs/696-sre-response-quality/integration-pilot
test -n "${OPENAI_API_KEY:-}" || { echo 'Falta OPENAI_API_KEY aprobada' >&2; exit 1; }
/tmp/sre-system-dev-venv/bin/python dev_pod.py
```

Sin `--serve` no se llama al juez y solo se hace preflight. Esperado en el JSON:

```text
ready: true
identity: SystemDevAgent
app_name: dev-jcorujo-agent
runner: 0.1.2 + commit validado
```

Fallos que deben detener el procedimiento:

- `runner_reference_unverified`: instalación del runner sin el hash/direct URL esperado.
- `OPENAI_API_KEY_missing`: falta la key de proceso aprobada.
- Import de ADK/Motor/Pydantic fallido: `.pth` o venv base incorrectos.

## 6. Comprobar AgentCard después del arranque autorizado

En el flujo híbrido no se hace un primer `--serve` de discovery: la API DEV ya aplica su gate y el
agente se arranca una sola vez en modo estándar según la sección 8. Después, en Terminal D:

```bash
curl -fsS http://127.0.0.1:8080/.well-known/agent-card.json \
  | python3 -m json.tool \
|| curl -fsS http://127.0.0.1:8080/.well-known/agent.json \
  | python3 -m json.tool

curl -fsS http://dev-jcorujo-agent.soarplus.svc.cluster.local:8080/.well-known/agent-card.json \
  | python3 -m json.tool \
|| curl -fsS http://dev-jcorujo-agent.soarplus.svc.cluster.local:8080/.well-known/agent.json \
  | python3 -m json.tool
```

Ambas comprobaciones deben devolver 200 y una card con `name: SystemDevAgent`. Si localhost funciona
pero el DNS del Service no, la API fallback no podrá descubrir este proceso: detenerse y revisar el
Service/selector, no escribir manualmente el registry.

## 7. Terminal B — arrancar API local granted en 8001

> A partir de aquí se abandona la garantía read-only.

```bash
cd /root/soarplus-api

export DOCUMENTDB_ENDPOINT="${DOCUMENTDB_ENDPOINT:-$API_DB_HOST}"
export DOCUMENTDB_USER="${DOCUMENTDB_USER:-$API_DB_USER}"
export DOCUMENTDB_PASS="${DOCUMENTDB_PASS:-$API_DB_PASS}"
export AWS_REGION="${AWS_REGION:-${aws_region:-eu-west-1}}"
export AGENT_DISCOVERY_DB_FALLBACK=1
export API_HOST=127.0.0.1
export API_PORT=8001
export CORS_ORIGINS='http://localhost:3000'

# GRANT_USER_ID debe haberse exportado en la sección 2.
test -n "${GRANT_USER_ID:-}" || { echo 'Falta GRANT_USER_ID' >&2; exit 1; }

/root/soarplus-api/.venv/bin/python /root/run_api_local_granted.py
```

Esperado:

```text
[LOCAL-GRANT] API en http://localhost:8001 (gate activo, capacidad simulada)
```

Smoke desde Terminal D:

```bash
A=http://127.0.0.1:8001
curl -fsS "$A/health" | python3 -m json.tool
curl -fsS "$A/api/v1/openapi.json" >/dev/null
curl -fsS -H "x-api-key: $MY_API_KEY" "$A/agents/" \
  | python3 -m json.tool
```

En el catálogo debe existir un item con:

```text
name = SystemDevAgent
real_name = dev-jcorujo-agent
```

Si no aparece: revisar card por DNS, registro, logs de discovery y que
`AGENT_DISCOVERY_DB_FALLBACK=1`. No continuar al invoke.

Al resolver las capacidades de la cuenta debe aparecer en logs:

```text
[LOCAL-GRANT] <GRANT_USER_ID> -> ['system_agent.sre_quality_eval']
```

Si la API key no resuelve a ese mismo user id, el flujo sigue bloqueado.

## 8. Terminal A — arrancar estándar con autorización verificada

Después de comprobar el gate de la API DEV y disponer de una key de proceso aprobada:

```bash
cd /root/soarplus-agentics
export EVAL_SCAN=1000
export EVAL_SAMPLE_SIZE=5
test -n "${OPENAI_API_KEY:-}" || { echo 'Falta OPENAI_API_KEY aprobada' >&2; exit 1; }

/tmp/sre-system-dev-venv/bin/python \
  specs/696-sre-response-quality/integration-pilot/dev_pod.py \
  --serve --api-authorization-verified
```

Comprobar el argv del PID: debe omitir `--user-judge-key` y `--manual-dev-pilot`. En este modo el
comando `sre_quality_eval` delega al agente estándar y ejecuta `run_sre_quality_eval` en el mismo
proceso; así `sre_usage_events` puede emitir `UsageMetadata` al sink ADK. La key enviada en la sesión
API puede prevalecer por request; la key de proceso sigue siendo necesaria para el preflight y como
fallback.

`--api-authorization-verified` es un flag del wrapper Agentics, no de API. Declara que el operador ya
verificó el gate anterior. No concede capacidades por sí mismo.

Repetir los smokes de card de la sección 6. No declarar contabilidad correcta hasta que una
evaluación exitosa demuestre `accounting.path=adk_events` y el rollup esperado.

## 9. Preparar la caché Next tras recrear el pod

```bash
cd /root/soarplus-frontend-app1
export PATH="/root/.local/share/pi-node/current/bin:$PATH"
NEXT_CACHE=/tmp/soarplus-frontend-next
mkdir -p "$NEXT_CACHE"

if [ ! -L .next ]; then
  test ! -e .next || { echo 'ERROR: .next real inesperado' >&2; exit 1; }
  ln -s "$NEXT_CACHE" .next
fi

test "$(readlink .next)" = "$NEXT_CACHE" || {
  echo 'ERROR: destino .next inesperado' >&2
  exit 1
}

grep -qxF '/.next' .git/info/exclude || printf '%s\n' '/.next' >> .git/info/exclude
git check-ignore -q .next || { echo 'ERROR: .next no ignorado' >&2; exit 1; }
```

Para limpiar una compilación previa, no borrar el enlace:

```bash
find "$NEXT_CACHE" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
```

## 10. Terminal C — arrancar frontend integrado

```bash
cd /root/soarplus-frontend-app1
export PATH="/root/.local/share/pi-node/current/bin:$PATH"
# El CJS de PostCSS se ejecuta desde el destino real de .next en /tmp.
export NODE_PATH="/root/soarplus-frontend-app1/node_modules${NODE_PATH:+:$NODE_PATH}"
NEXT_PUBLIC_ENDPOINT=http://127.0.0.1:8001 npm run dev
```

Verificar desde el pod:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/
# 200
```

Forwarding VS Code:

| Puerto remoto | Puerto local |
|---:|---:|
| 3000 | 3000 |
| 8001 | 8001 |

Abrir `http://localhost:3000`, no `127.0.0.1` ni una URL pública. El CORS de la API debe permitir
exactamente `http://localhost:3000`.

Este perfil requiere login real. No inyectar `local-viewer`, `local-admin` ni `local-noaccess`:
esos tokens solo existen en el launcher Quality read-only.

Después del login confirmar en Network:

```text
GET /user/me       -> 200
GET /user/settings -> 200
```

El frontend guarda la `llm_api_key` de settings como `liteLLMToken` y la usa como `x-api-key` para
`/agents`. No mostrar ni copiar su valor.

## 11. Verificar SystemDevAgent en la UI

1. Abrir **Subsystem-agents**.
2. Confirmar que `GET /agents` devuelve 200.
3. Localizar `SystemDevAgent` / `dev-jcorujo-agent` en la columna izquierda.
4. Seleccionarlo.
5. Una invocación desde esta pantalla solo envía `{query}` y prueba el flujo genérico.

La UI actual no envía `command`, `eval_targets` ni `trigger`. Escribir “sre_quality_eval” en el texto
no activa el comando SRE. Para evaluar usar la llamada HTTP explícita siguiente.

## 12. Invocación SRE explícita — operación con escritura

Antes de ejecutar, inspeccionar los targets activos y escoger uno deliberadamente:

```bash
python3 -m json.tool \
  /root/soarplus-agentics/tools/sre-response-quality/targets.json \
  | less
```

No usar `manual`: triggers válidos son `scheduled`, `prompt_change`, `agent_change`, `tool_change`,
`model_change`, `threshold_change`.

Ejemplo, sustituyendo el target por uno activo autorizado:

```bash
A=http://127.0.0.1:8001
TARGET='jira-agent'

BODY=$(python3 - "$TARGET" <<'PY'
import json, sys
print(json.dumps({
    "query": "Evaluar el histórico reciente del target permitido",
    "command": "sre_quality_eval",
    "eval_targets": [sys.argv[1]],
    "trigger": "scheduled",
}))
PY
)

RESPONSE=$(curl -fsS -X POST "$A/agents/dev-jcorujo-agent/invoke" \
  -H 'content-type: application/json' \
  -H "x-api-key: $MY_API_KEY" \
  -d "$BODY")

echo "$RESPONSE" | python3 -m json.tool
TASK_ID=$(printf '%s' "$RESPONSE" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
printf 'TASK_ID=%s\n' "$TASK_ID"
```

La respuesta es una task A2A con campo `id`, no `{task_id: ...}`.

Polling con la misma API key/identidad:

```bash
while :; do
  BODY=$(curl -fsS \
    -H "x-api-key: $MY_API_KEY" \
    "$A/agents/dev-jcorujo-agent/task/$TASK_ID") || exit 1
  printf '%s\n' "$BODY" | python3 -m json.tool
  STATE=$(printf '%s' "$BODY" \
    | python3 -c 'import json,sys; print((json.load(sys.stdin).get("status") or {}).get("state", ""))')
  case "$STATE" in
    completed|failed|canceled|cancelled) break ;;
  esac
  sleep 5
done
```

No reenviar automáticamente si vence un timeout: la tarea A2A puede seguir ejecutándose. El
resultado terminal aparece en `status.message.parts[].text`.

## 13. Quality dentro del perfil integrado

La misma API `8001` también expone `/quality`, pero:

- ya no hay garantía read-only;
- el usuario real necesita `quality.view` o admin;
- `GRANT_USER_ID` no concede `quality.view`;
- cualquier inicialización normal de API ya pudo escribir.

Para una validación segura de Quality, parar este frontend/API y seguir el runbook read-only en
`8000`. Un frontend solo tiene un `NEXT_PUBLIC_ENDPOINT`; no puede repartir Quality a 8000 y Agents
a 8001 sin cambios de código.

## 14. Parada ordenada

1. Guardar cualquier `TASK_ID` aún activo; detener el cliente no cancela la tarea remota.
2. Frontend Terminal C: `Ctrl-C`.
3. API Terminal B: `Ctrl-C`.
4. Agent Terminal A: `Ctrl-C`.
5. Confirmar puertos:

```bash
ss -ltnp | grep -E ':(3000|8001|8080)\b' || true
```

No matar por patrón amplio. Si un proceso no termina, identificar PID exacto, enviar `TERM`, esperar
y usar `KILL` solo como último recurso.

Limpiar credenciales de los shells usados:

```bash
unset MY_API_KEY GRANT_USER_ID
```

En el navegador, si se desea eliminar el estado local:

```javascript
localStorage.removeItem("session-storage");
localStorage.removeItem("app-storage");
location.href = "/login";
```

## 15. Recuperación después de recrear el pod

`/tmp` desaparece; `/root` normalmente persiste.

Repetir:

1. Sección 4: `/tmp/sre-system-dev-venv`.
2. Sección 5: preflight.
3. Secciones 6–8: agente/API y autorización.
4. Sección 9: `mkdir -p /tmp/soarplus-frontend-next` (el enlace persistente puede estar huérfano).
5. Sección 10: exportar `NODE_PATH` del checkout y arrancar frontend.

Si se perdió también `/root`, hay que recuperar checkouts, dependencias, `.next` symlink y exclusión
local. Ninguno de esos elementos de `/tmp` se considera persistente.

## 16. Diagnóstico rápido

| Síntoma | Causa probable / acción |
|---|---|
| Sin `--serve` no escucha 8080 | Ese modo solo ejecuta preflight |
| `runner_reference_unverified` | Runner no instalado desde el hash validado |
| Card funciona en localhost pero no por Service DNS | Service/selector no alcanza este pod; discovery bloqueado |
| `/agents/` no contiene SystemDevAgent | Fallback/registry/card/cache; revisar logs y `AGENT_DISCOVERY_DB_FALLBACK=1` |
| Invoke 403 | API key no corresponde a `GRANT_USER_ID` o falta capability efectiva |
| Polling 403/404 | Identidad distinta de la creadora o falta ownership/admin/read_all |
| Subsystem-agents deshabilitado | `/user/settings` no devolvió API key; login/cuenta incorrectos |
| Quality no aparece en perfil integrado | El usuario real no tiene `quality.view`; el grant SRE no la añade |
| Sesión desaparece | `/user/me` o `/user/settings` falló, o frontend apunta a otra API |
| `.next` huérfano tras recrear pod | `mkdir -p /tmp/soarplus-frontend-next` |
| `Cannot find module '@tailwindcss/postcss'` desde `/tmp/.../.next` | Reiniciar Next exportando `NODE_PATH=/root/soarplus-frontend-app1/node_modules...` |
| API 8000/8001 colisiona | No mezclar launcher read-only y granted en el mismo puerto |

## 17. Diferencia con publicación Kubernetes

Este runbook no publica manifests ni usa `kubectl`. El Deployment productivo:

- clona Agentics en `/app`;
- crea `/app/agents/system-agent/.venv`;
- instala runner y `.[evaluation]`;
- ejecuta `python -m system-agent`;
- expone `system-agent:8080`.

El piloto DEV usa identidad `dev-jcorujo-agent`, venv temporal y wrapper `dev_pod.py`. Aplicar patches,
reiniciar pods, desplegar o promover imágenes necesita autorización de infraestructura independiente.

## 18. Evidencia y limitaciones de este runbook

Verificado por lectura de código/repositorios y análisis coordinado de Agentics, API y Frontend:

- card/discovery admite logical `SystemDevAgent` y real `dev-jcorujo-agent`;
- registry DEV existe en lectura con endpoint de Service;
- grant local añade solo `system_agent.sre_quality_eval` al user id elegido;
- API normal/granted no es read-only;
- triggers y response/poll shape se ajustan al código actual;
- frontend Subsystem-agents usa `x-api-key`, no el Bearer sintético;
- symlink Next y exclusión local ya están configurados;
- reparación del venv temporal, metadata/imports y preflight no-servidor pasaron el 2026-10-21;
  los comandos individuales de reconstrucción fueron ejecutados, aunque el bloque limpio completo no
  se repitió una segunda vez desde `/tmp` vacío.

No se ejecutaron durante la elaboración inicial del runbook: `--serve`, arranque de API/frontend,
login real, invoke ni escritura de evaluación. Posteriormente el usuario ejecutó operaciones DEV
indicadas en la sección 19; no confundir esa evidencia con validación de todo el runbook. Cada
preflight debe pasar en la ejecución real; si no, detenerse en ese punto.

## 19. Modos del agente, límites de evaluación y trazabilidad

### 19.1 Piloto con worker hijo frente a ejecución estándar

| Modo | Activación | Dónde corre el evaluador | Clave del juez | Contabilidad |
|---|---|---|---|---|
| Piloto aislado | `--user-judge-key` (o `--manual-dev-pilot`) | `dev_eval_worker.py` como proceso hijo | se copia únicamente al entorno del hijo | normalmente `tracking_only`; el `ContextVar` del padre no cruza el proceso |
| Estándar/in-process | sin `--user-judge-key` ni `--manual-dev-pilot` | `system-agent.tools_sre_quality` en el proceso del agente | `OPENAI_API_KEY` del proceso | puede producir `adk_events` mediante `sre_usage_events` |

El piloto crea el hijo con pipes stdin/stdout, stderr descartado y respuesta JSON saneada. Solo le
reenvía `command`, `trigger`, `eval_targets` y la clave bajo `llm_api_key`/`OPENAI_API_KEY`; no debe
imprimirla. El agente estándar detecta el comando y ejecuta `run_sre_quality_eval` en proceso.

La API normal crea `session.state` con identidad, parámetros y key del usuario. En modo hijo se
reduce deliberadamente el contexto para aislar la key. Ninguna clave debe incluirse en payloads,
headers de trazas, logs, runbooks o capturas.

### 19.2 Arranque estándar sin worker hijo

Usar este modo solo cuando se quiera comprobar la ruta definitiva in-process y se disponga de una
clave de juez aprobada como secreto de proceso. No usar `preflight-only` para servir.

1. Detener el proceso actual por PID exacto o `Ctrl-C`; no matar por patrón.
2. Cargar la clave desde un secret mount aprobado sin imprimirla.
3. Configurar límites explícitos.
4. Arrancar sin `--user-judge-key` y sin `--manual-dev-pilot`:

```bash
cd /root/soarplus-agentics

# Ejemplo: el fichero debe proceder de un secret mount autorizado y no estar en Git.
# set -a; . /ruta/aprobada/systemdev-judge.env; set +a
# test -n "${OPENAI_API_KEY:-}" || { echo 'Falta OPENAI_API_KEY' >&2; exit 1; }

export EVAL_SCAN=1000
export EVAL_SAMPLE_SIZE=5

/tmp/sre-system-dev-venv/bin/python \
  specs/696-sre-response-quality/integration-pilot/dev_pod.py \
  --serve --api-authorization-verified
```

`--api-authorization-verified` es una afirmación del operador al wrapper, no una concesión. Debe
usarse solo después de comprobar el gate/API correspondiente. Este arranque no escribe DB por sí
mismo, salvo posibles garantías internas del runner; la evaluación empieza al recibir un invoke.

### 19.3 `EVAL_SCAN` no es `EVAL_SAMPLE_SIZE`

- `EVAL_SCAN` (default `300`) es el máximo de históricos inspeccionados desde el cursor. El query lee
  `EVAL_SCAN + 1` para detectar overflow. Si encuentra más, aborta con:
  ```text
  delta scan limit exceeded; checkpoint must not advance
  ```
  En ese caso no debe avanzar checkpoint ni asumirse que hubo evaluación.
- `EVAL_SAMPLE_SIZE` (fallback legacy `EVAL_MAX_CASES`, default `0`) limita cuántos casos elegibles se
  puntúan. `0` significa todos. Con valor `5`, el muestreo usa como máximo
  `min(casos_elegibles, 5)`.
- `EVAL_SEED` default `7` hace determinista el muestreo.

Aumentar `EVAL_SCAN` cambia cuánto se inspecciona; no obliga a puntuar más casos. Elegir el valor con
conocimiento del backlog y coste, no como respuesta automática a un overflow.

### 19.4 Escrituras y lecturas durante una evaluación

| Acción | Efecto esperado |
|---|---|
| Preflight/card/health | sin evaluación; no score |
| POST invoke por API | escribe task/historial inicial |
| Evaluación | escribe tracking en `a2a_tasks.agent_logs`; en éxito puede escribir `agent_eval_results` y checkpoint |
| GET task | lectura |
| Consulta de tracking | lectura |

El API local read-only no debe usarse para invoke. En arquitectura híbrida, invocar contra API dev y
leer Quality mediante el launcher local protegido.

### 19.5 Task y tracking durable por `eval_run_id`

Primero consultar la task autenticada:

```bash
curl -fsS \
  -H "x-api-key: $MY_API_KEY" \
  "$API_BASE/agents/dev-jcorujo-agent/task/$TASK_ID" \
  | python3 -m json.tool
```

Extraer de la respuesta/resultados el `eval_run_id`, target y estado. En el worker hijo,
`task_id`/`context_id` de tracking pueden quedar `null`; por eso
`/agents/agent-logs/context/<contextId>` puede no encontrar las trazas. La clave durable es
`tracking.eval_run_id`; mientras no se conozca, usar temporalmente rango de timestamp + target.

Consulta Mongo **solo lectura**, únicamente si `MONGO_URI` ya está provisionado en el shell:

```bash
read -rp 'eval_run_id: ' RUN_ID
export RUN_ID
/root/soarplus-api/.venv/bin/python - <<'PY'
import os
from pymongo import MongoClient
run_id = os.environ["RUN_ID"]
client = MongoClient(os.environ["MONGO_URI"])
projection = {
    "_id": 0,
    "timestamp": 1,
    "tracking.event": 1,
    "tracking.sequence": 1,
    "tracking.counts": 1,
}
query = {
    "logger": "sre_quality.tracking",
    "tracking.eval_run_id": run_id,
}
for doc in client["a2a_tasks"]["agent_logs"].find(query, projection).sort("timestamp", 1):
    print(doc)
client.close()
PY
unset RUN_ID
```

No imprimir documentos completos fuera de esa allow-list: pueden contener payloads o información
operativa. `sre_quality.tracking` en DocumentDB es la fuente durable. Stderr y
`EVAL_TRACK_LOG_FILE` son fallback local no durable.

Eventos esperables incluyen `target_started`, selección/ventana, fases, casos/LLM, heartbeat,
persistencia, `target_finished` o `target_failed`.

### 19.6 Tokens y gap contable del proceso hijo

`sre_usage_events` convierte deltas de usage en eventos ADK con `UsageMetadata`. En el proceso hijo,
el `ContextVar current_usage_sink` del padre no cruza el límite de proceso; por eso ejecuciones
observadas guardan:

```text
raw_eval_history.tracking.accounting.path = tracking_only
```

en vez de `adk_events`. El tracking contiene tokens observados y cobertura parcial, pero actualmente
`money`, `currency` y `pricing_source` pueden ser `null`; además la atribución puede usar el
modelo/provider de la task y no el juez real. La API de task actual no expone
`token_usage_details` de forma general.

Corregirlo requiere una feature distinta: canal IPC privado de telemetría sin credenciales, consumo
concurrente por el padre y reemisión al sink/ADK, además de propagar `judge_model`/provider y pricing.
No eliminar el aislamiento de key como arreglo rápido.

### 19.7 Operación observada y diagnóstico de overflow

En una ejecución estándar observada el 2026-10-21:

```text
task_id: 1a7f1556-1eef-4c5b-8f54-98c6d933c221
target: jira-agent
eval_run_id: 92b341d6c7024740ad7a162df89df822
resultado: target_failed / ValueError
scan_limit: 300
cursor_fetch: 301
persisted: false
checkpoint avanzado: false
llm_started/finished: 0/0
```

Esto demuestra el detector `EVAL_SCAN + 1`; no demuestra contabilidad exitosa ni llamada al juez.
La respuesta correcta es revisar backlog y decidir un `EVAL_SCAN` explícito, reiniciar con seguridad
y lanzar una nueva task; no editar el checkpoint ni reusar la task fallida.

### 19.8 Reinicio seguro

1. Confirmar estado terminal o guardar `TASK_ID`/`eval_run_id` de tareas activas.
2. Detener el agente actual con `Ctrl-C` o `TERM` al PID exacto y esperar.
3. Verificar que 8080 quedó libre.
4. Cargar secrets/variables sin eco y arrancar el modo elegido.
5. Verificar card local y por Service DNS antes de invocar.
6. Usar un target activo, trigger válido (`scheduled`/`agent_change`, no `manual`) y una sola task por
   target.
7. Hacer polling; no reenviar por timeout mientras la task remota pueda seguir viva.
8. Comprobar tracking/persistencia/checkpoint antes de declarar éxito.
