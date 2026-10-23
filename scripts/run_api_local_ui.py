"""API local read-only para probar el frontend /quality con usuarios sintéticos.

Copia canónica auditada. Instalar fuera del repo con:
    install -m 700 /root/soarplus-dev-orchestration/scripts/run_api_local_ui.py /root/run_api_local_ui.py

Ejecutar:
    /root/soarplus-api/.venv/bin/python /root/run_api_local_ui.py
    API_PORT=8001 /root/soarplus-api/.venv/bin/python /root/run_api_local_ui.py

Seguridad:
- escucha forzosamente en 127.0.0.1;
- bloquea métodos de escritura de pymongo antes de importar DatabaseService o la app;
- neutraliza índices, migraciones, seeds y backfills ejecutados por DatabaseService.__init__;
- neutraliza el backfill de usage_metrics del evento startup;
- desactiva completamente el discovery background local (no puede marcar agentes stale);
- los tres usuarios y sus permisos solo existen en memoria;
- cualquier escritura no neutralizada falla cerrada con PermissionError y deja READONLY-GUARD.

Tokens Bearer:
- local-viewer: usuario no-admin con quality.view;
- local-noaccess: usuario no-admin sin capabilities;
- local-admin: admin sin quality.view (prueba el bypass).

Solo para un pod local de desarrollo. Nunca desplegar ni exponer fuera de loopback.
"""

import os
import sys
import types

REPO = "/root/soarplus-api"
API_DIR = os.path.join(REPO, "api")

# Usar siempre un id sintético por defecto. No debe coincidir con un usuario real: otros
# endpoints de usuario podrían consultar sus settings aunque /user/me esté interceptado.
VIEWER_USER_ID = os.environ.get("GRANT_USER_ID", "local-test-viewer")
NOACCESS_USER_ID = "local-test-noaccess"
ADMIN_USER_ID = "local-test-admin"

LOCAL_IDENTITIES = {
    "local-viewer": (VIEWER_USER_ID, {"quality.view"}, False),
    "local-noaccess": (NOACCESS_USER_ID, set(), False),
    "local-admin": (ADMIN_USER_ID, set(), True),
}
BY_USER_ID = {
    user_id: (capabilities, is_admin)
    for user_id, capabilities, is_admin in LOCAL_IDENTITIES.values()
}

# PORT/HOST genéricos pisan DBSettings; eliminarlos antes de importar la app.
API_PORT = int(os.environ.pop("PORT", None) or os.environ.get("API_PORT", 8000))
os.environ.pop("HOST", None)
API_HOST = "127.0.0.1"  # No configurable: los tokens sintéticos saltan autenticación real.

os.environ.setdefault("DOCUMENTDB_USER", os.environ.get("API_DB_USER", ""))
os.environ.setdefault("DOCUMENTDB_PASS", os.environ.get("API_DB_PASS", ""))
os.environ.setdefault("DOCUMENTDB_ENDPOINT", os.environ.get("API_DB_HOST", ""))
os.environ.setdefault("AWS_REGION", os.environ.get("aws_region", "eu-west-1"))
os.environ.setdefault("AGENT_DISCOVERY_DB_FALLBACK", "1")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

missing = [
    name
    for name in ("DOCUMENTDB_USER", "DOCUMENTDB_PASS", "DOCUMENTDB_ENDPOINT")
    if not os.environ.get(name)
]
if missing:
    sys.exit(f"ERROR: faltan variables obligatorias: {', '.join(missing)}")

os.chdir(API_DIR)
sys.path.insert(0, API_DIR)

# 1. Guardia fail-closed ANTES de importar DatabaseService o api.app.
from pymongo.collection import Collection  # noqa: E402

_WRITE_METHODS = (
    "insert_one",
    "insert_many",
    "update_one",
    "update_many",
    "replace_one",
    "delete_one",
    "delete_many",
    "find_one_and_update",
    "find_one_and_replace",
    "find_one_and_delete",
    "bulk_write",
    "create_index",
    "create_indexes",
    "drop_index",
    "drop_indexes",
    "drop",
)


def _blocked(method_name):
    def guard(self, *args, **kwargs):
        print(
            f"[READONLY-GUARD] bloqueado {self.name}.{method_name}",
            flush=True,
        )
        raise PermissionError(
            f"local read-only guard: {self.name}.{method_name} bloqueado"
        )

    return guard


for _method in _WRITE_METHODS:
    setattr(Collection, _method, _blocked(_method))

from AWS.documentdb import DatabaseService  # noqa: E402

# 2. Neutralizar los pasos conocidos de __init__ para que ni siquiera reintenten escrituras.
def _no_write_step(self, *args, **kwargs):
    return None


for _step in (
    "_ensure_indexes",
    "_fix_groups_as_string",
    "_safe_create_index",
    "ensure_manage_capability_ids_migrated",
    "ensure_predefined_roles_seeded",
    "ensure_baseline_roles_backfilled",
    "ensure_llm_config_override_agent_pin_capability_backfilled",
    "ensure_new_playbooks_domains_datasource_capabilities_backfilled",
    "ensure_quality_view_capability_backfilled",
):
    setattr(DatabaseService, _step, _no_write_step)

# 3. Neutralizar la migración automática del evento FastAPI startup.
_backfill_stub = types.ModuleType("backfill_usage_metrics")
_backfill_stub.run_migration = lambda *args, **kwargs: print(
    "[READONLY-GUARD] backfill_usage_metrics omitido", flush=True
)
sys.modules["backfill_usage_metrics"] = _backfill_stub

# 4. Usuarios, capabilities y atributos exclusivamente en memoria.
_original_capabilities = DatabaseService.get_effective_capabilities
_original_attribute = DatabaseService.get_user_attribute
_original_user_info = DatabaseService.get_userinfo_by_attribute
_original_user_settings = DatabaseService.get_user_settings


def _capabilities(self, user_id):
    if user_id in BY_USER_ID:
        return sorted(BY_USER_ID[user_id][0])
    return _original_capabilities(self, user_id)


def _attribute(self, user_id, key):
    if user_id in BY_USER_ID and key == "is_admin":
        return BY_USER_ID[user_id][1]
    return _original_attribute(self, user_id, key)


def _user_info(self, attribute, value):
    if attribute == "user_id" and value in BY_USER_ID:
        capabilities, is_admin = BY_USER_ID[value]
        label = (
            "local-admin"
            if is_admin
            else "local-viewer"
            if capabilities
            else "local-noaccess"
        )
        return {
            "user_id": value,
            "username": label,
            "email": f"{label}@local.invalid",
            "name": label.replace("-", " ").title(),
            "is_admin": is_admin,
            "tags": [],
            "bucket_name": None,
            "s3_access_key": None,
            "s3_secret_key": None,
            "llm_api_key": None,
        }
    return _original_user_info(self, attribute, value)


def _user_settings(self, user_id):
    if user_id in BY_USER_ID:
        # El Header llama a /user/settings junto a /user/me. Nunca leer settings reales para
        # identidades sintéticas, aunque GRANT_USER_ID se configure por error con un id real.
        return {"llm_api_key": None, "ia_language": None}
    return _original_user_settings(self, user_id)


DatabaseService.get_effective_capabilities = _capabilities
DatabaseService.get_user_attribute = _attribute
DatabaseService.get_userinfo_by_attribute = _user_info
DatabaseService.get_user_settings = _user_settings

from controllers.controller import AuthController  # noqa: E402

_original_validate = AuthController.validate_token


def _validate(self, token):
    if token in LOCAL_IDENTITIES:
        user_id = LOCAL_IDENTITIES[token][0]
        return {
            "sub": user_id,
            "username": user_id,
            "token_use": "access",
            "scope": "local-ui-test",
        }
    return _original_validate(self, token)


AuthController.validate_token = _validate

# 5. Para la vista quality no se necesita discovery. Desactivarlo elimina tanto el hilo como
# cualquier posibilidad de alterar agent_registry/stale aunque cambie el fallback en el futuro.
from lib.agent_discovery import BackgroundDiscoveryService  # noqa: E402


def _discovery_disabled(self, *args, **kwargs):
    print("[READONLY-GUARD] agent discovery background omitido", flush=True)


BackgroundDiscoveryService.start = _discovery_disabled
BackgroundDiscoveryService.stop = lambda self, *args, **kwargs: None

import uvicorn  # noqa: E402
from api import app  # noqa: E402

print(
    f"[LOCAL-UI] http://{API_HOST}:{API_PORT} read-only; "
    f"tokens: {', '.join(LOCAL_IDENTITIES)}",
    flush=True,
)
uvicorn.run(
    app,
    host=API_HOST,
    port=API_PORT,
    proxy_headers=True,
    log_level="info",
)
