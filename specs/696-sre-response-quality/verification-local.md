# Verificación local de /quality tras CR-001 — step by step (usuario)

> Para la prueba completa API + frontend + usuarios sintéticos, usar el runbook consolidado:
> [RUNBOOK-local-quality-ui.md](RUNBOOK-local-quality-ui.md). Este fichero conserva el checklist
> original centrado en API.

Fuente: analysis 696-api-15/16 (worker api) + CR-001. Escrito 2026-10-19 por el admiral.
La API local usa la DocumentDB COMPARTIDA de dev: usar siempre el modo solo-lectura (paso 1).

## 1. Levantar la API (solo-lectura, identidades sintéticas)

```bash
cd /root/soarplus-api
/root/soarplus-api/.venv/bin/python /root/run_api_local_quality.py
```

- Guarda de solo-lectura pymongo activa (`[READONLY-GUARD]`); puerto 127.0.0.1:8000.
- Tokens: `local-viewer` (quality.view), `local-noaccess` (sin capability), `local-admin` (bypass), cualquier otro → 401.
- Health: `curl -s localhost:8000/health` → `{"status":"ok"}` · Swagger: `/docs` · OpenAPI: `/api/v1/openapi.json`.
- Alternativa con Cognito real: `./scripts/run_local.sh` + `.env.local` (`COGNITO_*`); no necesaria para esto.

```bash
B="http://127.0.0.1:8000/api/v1"
```

## 2. Gate (en cualquier ruta, p. ej. R6)

```bash
curl -s -o /dev/null -w "%{http_code}\n" $B/quality/targets/history                                               # 401
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer local-noaccess" $B/quality/targets/history     # 403
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer local-viewer"   $B/quality/targets/history     # 200
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer local-admin"    $B/quality/targets/history     # 200 (bypass)
```

## 3. R1 — catálogo (efecto del predicado nuevo sobre datos reales)

```bash
curl -s -H "Authorization: Bearer local-viewer" "$B/quality/targets" | python3 -m json.tool | head -40
```

Mirar: `evaluations` puede cambiar vs pre-CR — cuentan los puntos con AMBAS métricas puntuadas
(aunque fueran uncommitted/rescore/validation) y desaparecen los unscored. Esperado.

## 4. R2 — historial last-5, URL sin type

```bash
curl -s -H "Authorization: Bearer local-viewer" "$B/quality/targets/<target>/evaluations" | python3 -m json.tool
```

Esperado: ≤5 items, `evaluated_at` descendente, `total` = serie completa (puede ser >5),
primer item == `latest` del catálogo.

```bash
# URL antigua desaparecida:
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer local-viewer" "$B/quality/targets/agent/<target>/evaluations"    # 404
# target inexistente:
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer local-viewer" "$B/quality/targets/no-existe-xyz/evaluations"     # 404
```

409 de colisión: solo saltará si en datos reales un agent y un playbook comparten nombre
(verificación pendiente user/ops). Sin colisión, no ver 409 es lo correcto.

## 5. R6 — todos los targets con last-5

```bash
curl -s -H "Authorization: Bearer local-viewer" "$B/quality/targets/history?limit=5&offset=0" | python3 -m json.tool | head -60
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer local-viewer" "$B/quality/targets/history?limit=501"             # 422 (hard max 500)
```

Esperado: paginación por targets, orden `(target_type, target)`, `history` ≤5 desc por item.
Observar el tiempo de respuesta (riesgo R-6 a volumen real).

## 6. R3/R4/R5 — forma intacta, predicado nuevo

```bash
curl -s -H "Authorization: Bearer local-viewer" "$B/quality/evaluations/<eval_run_id>" | python3 -m json.tool
```

Un `eval_run_id` que antes era 404 (uncommitted/rescored) ahora puede ser 200 si tiene ambas métricas.

## 7. Script de integración y Postman (tras E7/T032)

Cuando E7 esté aceptado, en el repo soarplus-api:

```bash
# script completo R1-R6 (con la API del paso 1 levantada):
/root/soarplus-api/.venv/bin/python /root/soarplus-api/scripts/integration/quality_integration_check.py
# Postman: importar los dos JSON versionados
#   scripts/integration/postman/quality.postman_collection.json
#   scripts/integration/postman/local.postman_environment.json
# y correr la carpeta "0 · Descubrimiento" primero, luego el resto (o Collection Runner entero).
```

Los antiguos /root/quality_integration_check.py y /root/postman/* quedan obsoletos (superficie pre-CR).

## Pendientes user/ops que esta verificación cubre en parte

- Comportamiento de `$type:"number"` (predicado) sobre DocumentDB real → pasos 3-5.
- Colisiones de nombre entre tipos en datos reales → paso 4 (y catálogo).
- Rendimiento de R6 a volumen real → paso 5 (medición informal; la formal sigue pendiente).
- Índices del writer en vivo → fuera de alcance aquí (riesgo R-6 del plan).
