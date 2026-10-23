# Runbook — prueba local completa de Quality (US 696)

Fecha: 2026-10-20. Cubre API read-only, frontend Next.js, forwarding a Windows, usuarios
sintéticos y validación de la vista `/quality` contra datos reales de DocumentDB dev.

Este perfil desactiva discovery y no permite invocar agentes. Para levantar `SystemDevAgent`, API
normal/granted y frontend con login real, usar
[`RUNBOOK-local-systemdev-api-frontend.md`](RUNBOOK-local-systemdev-api-frontend.md). Los dos
perfiles son deliberadamente distintos y no deben compartir el mismo puerto API.

## 0. Reglas de seguridad

La API local lee la DocumentDB compartida de dev. Para estas pruebas:

- **NO usar** `/root/soarplus-api/scripts/run_local.sh`: importa la aplicación normal y permite
  escrituras de init (índices, migraciones, seeds/backfills RBAC, usage_metrics y discovery).
- **NO usar** `/root/run_api_local_granted.py`: inyecta una capability en memoria, pero **no es
  read-only**; el init normal de la aplicación sigue activo. `AGENT_DISCOVERY_DB_FALLBACK=1`
  protege específicamente de marcar agentes stale, no neutraliza el resto de escrituras.
- Usar únicamente el launcher UI auditado de este runbook. Fuerza loopback, bloquea los métodos de
  escritura de PyMongo, neutraliza init/backfills y desactiva por completo agent discovery.
- Si aparece `[READONLY-GUARD] bloqueado <colección>.<método>`, la escritura fue impedida: detener
  la operación que la provocó e investigar. Para navegar por Quality no debe aparecer.
- Los tokens sintéticos saltan autenticación real: nunca exponer el puerto 8000 públicamente.

La garantía definitiva sería un usuario DocumentDB con permisos server-side de solo lectura. El
launcher proporciona defensa fail-closed para todos los métodos de escritura usados por el código
actual, verificados mediante análisis estático.

## 1. Estado y prerequisitos

Repositorios/ramas:

```bash
git -C /root/soarplus-api branch --show-current
# feature/696-sre-response-quality (API f34bf9c está en origin)

git -C /root/soarplus-frontend-app1 branch --show-current
# feature/696-sre-response-quality (frontend 0032c68 en origin)
```

Node/npm en shells interactivos:

```bash
export PATH="/root/.local/share/pi-node/current/bin:$PATH"
node --version
npm --version
```

Dependencias frontend ya instaladas por `npm ci`. Si faltan:

```bash
cd /root/soarplus-frontend-app1
npm ci
```

Variables de conexión DocumentDB provistas por el pod: `API_DB_HOST`, `API_DB_USER`,
`API_DB_PASS`. El launcher las mapea a `DOCUMENTDB_*` y aborta si falta alguna.

## 2. Instalar el launcher API UI seguro

Copia canónica:

```text
/root/soarplus-dev-orchestration/scripts/run_api_local_ui.py
```

Instalar en `/root`:

```bash
install -m 700 \
  /root/soarplus-dev-orchestration/scripts/run_api_local_ui.py \
  /root/run_api_local_ui.py
```

Verificar que ambas copias coinciden:

```bash
sha256sum \
  /root/soarplus-dev-orchestration/scripts/run_api_local_ui.py \
  /root/run_api_local_ui.py
```

Deben imprimir el mismo hash. El launcher usa por defecto ids exclusivamente sintéticos
(`local-test-viewer`, `local-test-noaccess`, `local-test-admin`) y stubea tanto `/user/me` como
`/user/settings`; no reutiliza ningún user_id real ni lee sus settings.

## 3. Levantar la API read-only

Terminal A:

```bash
unset GRANT_USER_ID
/root/soarplus-api/.venv/bin/python /root/run_api_local_ui.py
```

Salida esperada:

```text
[LOCAL-UI] http://127.0.0.1:8000 read-only; tokens: local-viewer, local-noaccess, local-admin
[READONLY-GUARD] agent discovery background omitido
```

El proceso debe escuchar solo en `127.0.0.1:8000`:

```bash
ss -ltnp | grep ':8000'
```

### 3.1 Smoke de la API

Otra terminal:

```bash
curl -s http://127.0.0.1:8000/health
# {"status":"ok"}
```

Viewer sintético:

```bash
curl -s -H 'Authorization: Bearer local-viewer' \
  http://127.0.0.1:8000/user/me | python3 -m json.tool

curl -s -H 'Authorization: Bearer local-viewer' \
  http://127.0.0.1:8000/user/settings | python3 -m json.tool
```

Esperado:

```text
user_id = local-test-viewer
is_admin = false
effective_capabilities = ["quality.view"]
/user/settings = {"llm_api_key": null, "ia_language": null}
```

Matriz del gate:

```bash
B=http://127.0.0.1:8000
curl -s -o /dev/null -w '%{http_code}\n' "$B/quality/targets"                         # 401
curl -s -o /dev/null -w '%{http_code}\n' -H 'Authorization: Bearer local-noaccess' "$B/quality/targets"  # 403
curl -s -o /dev/null -w '%{http_code}\n' -H 'Authorization: Bearer local-viewer' "$B/quality/targets"    # 200
curl -s -o /dev/null -w '%{http_code}\n' -H 'Authorization: Bearer local-admin' "$B/quality/targets"     # 200
```

## 4. Levantar el frontend contra la API local

El pod define normalmente `NEXT_PUBLIC_ENDPOINT` con la API desplegada de test. Ejecutar
`npm run dev` sin override hace que `local-viewer` se envíe a esa API, reciba 401 y que el frontend
borre la sesión. Hay que reemplazarlo explícitamente al arrancar Next.js.

Terminal B:

```bash
export PATH="/root/.local/share/pi-node/current/bin:$PATH"
cd /root/soarplus-frontend-app1

# .next vive en el overlay efímero amplio, no en el volumen /root de 10 GB.
NEXT_CACHE=/tmp/soarplus-frontend-next
mkdir -p "$NEXT_CACHE"

# El enlace se crea una sola vez y persiste en /root. No sustituir un .next real silenciosamente.
if [ ! -L .next ]; then
  if [ -e .next ]; then
    echo "ERROR: .next existe y no es un enlace; revisar antes de borrarlo" >&2
    exit 1
  fi
  ln -s "$NEXT_CACHE" .next
fi

# La regla versionada `/.next/` solo cubre directorios, no el symlink. Ignorarlo localmente para
# que nunca se cuele en un commit; .git/info/exclude no se versiona.
grep -qxF '/.next' .git/info/exclude || printf '%s\n' '/.next' >> .git/info/exclude

# Verificación fail-closed: evita limpiar otro destino si alguien cambió el enlace.
if [ "$(readlink .next)" != "$NEXT_CACHE" ]; then
  echo "ERROR: .next no apunta a $NEXT_CACHE" >&2
  exit 1
fi
if ! git check-ignore -q .next; then
  echo "ERROR: el symlink .next no está ignorado localmente" >&2
  exit 1
fi

# Elimina una compilación previa que pudiera contener el endpoint remoto, conservando el enlace.
find "$NEXT_CACHE" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +

# Turbopack ejecuta CJS generado desde el destino real en /tmp. Sin NODE_PATH, ese código no puede
# resolver @tailwindcss/postcss del checkout.
export NODE_PATH="/root/soarplus-frontend-app1/node_modules${NODE_PATH:+:$NODE_PATH}"

NEXT_PUBLIC_ENDPOINT=http://127.0.0.1:8000 npm run dev
```

Esperado: Next.js en puerto 3000 y `/quality` en la lista de rutas.

### 4.1 Persistencia y recreación del pod

`/root` es el volumen persistente pequeño; `/tmp` pertenece al overlay amplio pero es efímero. Al
recrear el pod, el enlace `.next` permanece y su destino desaparece. Antes de cualquier `npm run
dev` o `npm run build` hay que recrear el destino y exportar la ruta de resolución de módulos:

```bash
mkdir -p /tmp/soarplus-frontend-next
export NODE_PATH="/root/soarplus-frontend-app1/node_modules${NODE_PATH:+:$NODE_PATH}"
```

`NODE_PATH` debe definirse en el proceso padre de Next; no ponerlo en `NEXT_PUBLIC_*` ni en
`.env.local`. El symlink externaliza los artefactos, pero Node resuelve el PostCSS generado desde la
ruta real `/tmp/...` y necesita este fallback al `node_modules` del checkout.

Un enlace temporalmente huérfano es esperado tras recrear el pod. No ejecutar `rm -rf .next`: eso
borraría el enlace, no limpiaría la caché. Para limpiar Next usar el `find "$NEXT_CACHE" ...` anterior.
La entrada local `/.next` vive en `.git/info/exclude`: persiste mientras persista el checkout, pero no
viaja con Git. Si se pierde también el volumen `/root`, se pierde el checkout completo y hay que
recrear el repositorio, el enlace y esa entrada local de exclusión.

Comprobar desde el pod:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/
# 200
```

## 5. Forwarding a Windows

En VS Code → panel **Ports**, añadir o comprobar:

| Puerto remoto | Puerto local |
|---:|---:|
| 3000 | 3000 |
| 8000 | 8000 |

Abrir exactamente:

```text
http://localhost:3000
```

No usar `127.0.0.1:3000` ni una URL pública de forwarding: la API permite CORS para el origen
exacto `http://localhost:3000`. El navegador (SPA) llama directamente a
`http://127.0.0.1:8000`, por eso también necesita el forwarding 8000.

## 6. Preparar DevTools

Antes de inyectar una sesión:

1. F12 → **Network** → marcar **Preserve log**.
2. F12 → ⚙️/F1 → Console → activar **Preserve log upon navigation**.
3. En Console, habilitar todos los niveles, incluido Errors.
4. Si Chrome bloquea pegar, escribir manualmente `allow pasting` y pulsar Enter.

`location.href` recarga la página y normalmente limpia la consola. Los mensajes
`Download the React DevTools...` y `[HMR] connected` son informativos, no errores.

## 7. Usuario normal con `quality.view`

F12 → Console:

```javascript
localStorage.setItem(
  "session-storage",
  JSON.stringify({
    state: {
      accessToken: "local-viewer",
      refreshToken: "local-viewer",
      user: null,
      isAuthenticated: true,
      _hasHydrated: false
    },
    version: 0
  })
);
location.href = "/";
```

Después de cargar:

- Network debe mostrar `http://127.0.0.1:8000/user/me` → 200.
- Network debe mostrar `http://127.0.0.1:8000/user/settings` → 200.
- Debe aparecer el item de menú **Quality**.
- `/quality/targets` debe devolver 200.

Comprobar el store:

```javascript
JSON.parse(localStorage.getItem("session-storage")).state
```

Esperado: token `local-viewer`, `isAuthenticated: true`, usuario no-admin y
`effective_capabilities: ["quality.view"]`.

## 8. Admin sin capability (bypass)

F12 → Console:

```javascript
const session = JSON.parse(localStorage.getItem("session-storage"));
session.state.accessToken = "local-admin";
session.state.refreshToken = "local-admin";
session.state.user = null;
localStorage.setItem("session-storage", JSON.stringify(session));
location.href = "/";
```

Esperado en `/user/me`:

```text
is_admin = true
effective_capabilities = []
```

Aun sin capability explícita, debe ver Quality y obtener 200 gracias al bypass admin, tanto en UI
(`useCan`) como en backend (`authorize_capability_or_admin`).

## 9. Usuario sin acceso

F12 → Console:

```javascript
const session = JSON.parse(localStorage.getItem("session-storage"));
session.state.accessToken = "local-noaccess";
session.state.refreshToken = "local-noaccess";
session.state.user = null;
localStorage.setItem("session-storage", JSON.stringify(session));
location.href = "/";
```

Esperado:

- `is_admin = false`, `effective_capabilities = []`.
- Quality no aparece en el menú.
- Navegar manualmente a `http://localhost:3000/quality` redirige a `/`.
- Llamar directamente a `/quality/targets` con ese Bearer devuelve 403.

## 10. Checklist funcional de la vista Quality

Entrar de nuevo como `local-viewer` o `local-admin` y comprobar:

1. El catálogo carga, muestra `total` y mantiene el orden `(target_type, target)` servido por R1.
2. Seleccionar un target muestra como máximo 5 evaluaciones, de más nueva a más antigua.
3. La UI muestra el `total` de la serie completa aunque solo reciba 5 puntos.
4. Las dos métricas aparecen en gráfica y tabla; valores ausentes se muestran como ausencia, nunca 0.
5. Un punto legacy con `status: null` se muestra como `unknown (legacy)` y marcador diferenciado.
6. El tamaño de muestra aparece por punto.
7. Labels, escala y polaridad proceden de R5 `/quality/metrics`.
8. Cambiar a `local-noaccess` oculta el menú y protege la ruta.
9. Cambiar a `local-admin` prueba el bypass sin capability explícita.

Casos que no existen en los datos dev actuales:

- No hay colisión real agent/playbook con el mismo nombre; el 409 está cubierto por tests y por
  integración condicional/simulada.
- En los last-5 actuales no hay un punto con `value:null`; la UI de ausencia está cubierta con
  respuesta simulada y pruebas del script de integración.

## 11. Pruebas API automatizadas opcionales

Con la API del paso 3 levantada:

```bash
/root/soarplus-api/.venv/bin/python \
  /root/soarplus-api/scripts/integration/quality_integration_check.py
```

Esperado: todos los checks ejecutables pasan; el 409 puede figurar como INFO/no ejercitado si no
hay colisión real.

Postman (JSONs ya regenerados, no ejecutar el generador):

```text
/root/soarplus-api/scripts/integration/postman/quality.postman_collection.json
/root/soarplus-api/scripts/integration/postman/local.postman_environment.json
```

Importar ambos, seleccionar el environment `soarplus-api local (quality)` y ejecutar primero
`0 · Descubrimiento`, después el resto o el Collection Runner entero.

## 12. Diagnóstico rápido

### La sesión vuelve a null inmediatamente

Comprobar Network. Si las llamadas van a:

```text
https://api1-cas-test.es.deloitte.com
```

el frontend se levantó sin override. Detenerlo, conservar el enlace `.next`, limpiar su destino y
reiniciar con:

```bash
cd /root/soarplus-frontend-app1
NEXT_CACHE=/tmp/soarplus-frontend-next
mkdir -p "$NEXT_CACHE"
test -L .next && test "$(readlink .next)" = "$NEXT_CACHE" || {
  echo "ERROR: enlace .next inesperado" >&2
  exit 1
}
find "$NEXT_CACHE" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
export NODE_PATH="/root/soarplus-frontend-app1/node_modules${NODE_PATH:+:$NODE_PATH}"
NEXT_PUBLIC_ENDPOINT=http://127.0.0.1:8000 npm run dev
```

Si van a local, revisar que `/user/me` y `/user/settings` devuelvan ambos 200; el Header ejecuta
las dos en `Promise.all` y cualquier fallo provoca logout.

### Error CORS

Abrir el frontend como `http://localhost:3000`, no como `127.0.0.1:3000` ni URL pública. Confirmar
que la respuesta API contiene:

```text
access-control-allow-origin: http://localhost:3000
```

### Puerto ocupado

```bash
ss -ltnp | grep -E ':(3000|8000)\b'
```

Detener primero el proceso anterior con Ctrl-C. No levantar simultáneamente `run_local.sh`,
`run_api_local_granted.py` o `run_api_local_quality.py` en el mismo puerto.

## 13. Finalizar y limpiar

1. Detener frontend con Ctrl-C en Terminal B.
2. Detener API con Ctrl-C en Terminal A.
3. Limpiar la sesión del navegador:

```javascript
localStorage.removeItem("session-storage");
location.href = "/login";
```

No se requiere limpieza de DocumentDB: el launcher no escribe en ella.
