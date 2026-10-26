# Operativa para levantar y adaptar el entorno Pi Team

## Objetivo

Este documento explica cómo reconstruir el entorno de agentes Pi del equipo, qué componentes
son reproducibles desde este repositorio, qué dependencias deben provisionarse fuera de Git y qué
archivos hay que adaptar al mover el equipo a otro stack o infraestructura.

Pi no aprende permanentemente de las conversaciones. El comportamiento reproducible procede de los
ficheros del repositorio y de la configuración/runtime de cada rol. Las sesiones Pi son memoria
episódica adicional, no la fuente de verdad del código ni del workflow.

## Arquitectura

```text
pi/team.sh
  -> pi/launch.sh <rol>
      -> genera ~/.pi-team/<rol>/AGENTS.md y settings.json
      -> selecciona ~/.pi-team/team-session
      -> arranca Pi con --session-id <sesion>-<rol>
      -> conecta el rol a pi-link

admiral + workers
  -> tmux (una ventana por rol)
  -> pi-link (hub en admiral)
  -> repositorios y artefactos versionados
```

Roles actuales:

```text
admiral
agentics
api
frontend
```

El registro único de workers está en:

```text
protocols/worker-registry.md
```

## Fuentes de verdad

| Área | Fuente |
|---|---|
| Arranque tmux y roles | `pi/team.sh` |
| Generación del runtime Pi | `pi/launch.sh` |
| Variables y utilidades | `pi/lib.sh` |
| Instrucciones comunes | `pi/team.md` |
| Instrucciones por rol | `pi/roles/` |
| Workers y repositorios | `protocols/worker-registry.md` |
| Protocolos de trabajo | `protocols/*.md` |
| Definiciones de agentes | `.github/agents/` |
| Prompts auxiliares | `.pi/prompts/` |
| Skill ADO | `.agents/skills/ado-work-items/` |
| Estado de una feature | `specs/<US>-<slug>/` |
| Configuración portable de roles | `pi/team-config/` |

`pi/team-config/` contiene templates/documentación. Pi no los carga directamente: el launcher
genera la configuración efectiva a partir de `pi/team.md`, `pi/roles/` y el repositorio del rol.

## Prerrequisitos del host

### Obligatorios

- Linux o entorno compatible con Bash.
- Git.
- Node.js/npm y el ejecutable `pi` instalado.
- Una autenticación Pi válida, normalmente en:

  ```text
  ~/.pi/agent/auth.json
  ```

- El paquete `pi-link`, instalado donde lo espera el launcher:

  ```bash
  pi install npm:pi-link@0.5.2
  ```

- Los repositorios de los workers en las rutas registradas.

### Instalados automáticamente o por operación

- `tmux`: `pi/team.sh up` intenta instalarlo si no existe.
- Directorios runtime bajo `~/.pi-team/`.
- `AGENTS.md` y `settings.json` específicos de cada rol.

### Opcionales

- Azure CLI y extensión `azure-devops`, si se va a usar la skill ADO.
- Herramientas de búsqueda `rg` y `fd`.
- VS Code/Remote Containers.

## Preparación de un host nuevo

### 1. Clonar el orquestador

```bash
git clone https://github.com/yuscoru/orquestador.git /root/soarplus-dev-orchestration
cd /root/soarplus-dev-orchestration
git checkout <branch-o-tag>
```

### 2. Clonar los repositorios de workers

Las rutas deben coincidir con `protocols/worker-registry.md`, o se debe editar ese registro:

```bash
git clone <agentics-repository> /root/soarplus-agentics
git clone <api-repository> /root/soarplus-api
git clone <frontend-repository> /root/soarplus-frontend-app1
```

Para adaptar el stack a otros nombres/rutas, cambiar el registro y verificar también:

- `.github/agents/`.
- `pi/roles/`.
- Las reglas de ownership de los protocolos.
- Cualquier skill que use rutas absolutas.

### 3. Instalar y autenticar Pi

Ejecutar Pi en un terminal normal, no dentro de un worker:

```bash
pi
/login
```

Salir con `Ctrl+D` solo después de completar el login. No usar `Ctrl+D` dentro de un agente:
esto cierra Pi.

### 4. Instalar pi-link

```bash
pi install npm:pi-link@0.5.2
```

El launcher comprueba la existencia de:

```text
~/.pi/agent/npm/node_modules/pi-link
```

### 5. Provisionar secretos fuera de Git

Por ejemplo, para ADO, usar almacenamiento root-only:

```text
/root/.pi-team/env.sh
```

Permisos esperados:

```bash
chmod 600 /root/.pi-team/env.sh
```

No versionar:

- PATs.
- API keys.
- `auth.json`.
- `.env`.
- `models-store.json`.
- URLs con credenciales.

### 6. Instalar ADO si se necesita

La skill no instala Azure CLI. Si se necesita consultar o actualizar work items:

```bash
apt-get install azure-cli
az extension add --name azure-devops
```

Usar un `AZURE_CONFIG_DIR` persistente y no guardar secretos en el repositorio.

## Arranque normal

Desde el repositorio del orquestador:

```bash
cd /root/soarplus-dev-orchestration
pi/team.sh up
pi/team.sh status
```

`up` arranca `admiral` primero, que actúa como hub de pi-link, y después los workers.

Para abrir un rol concreto:

```bash
pi/team.sh attach api
pi/team.sh attach agentics
pi/team.sh attach frontend
```

Para ver todo el equipo:

```bash
pi/team.sh watch
```

Para desconectar la terminal sin parar los agentes:

```text
Ctrl-b d
```

No usar `Ctrl+D` dentro de Pi.

## Sesiones Pi

La etiqueta de sesión está en:

```text
~/.pi-team/team-session
```

Cada rol usa una sesión independiente:

```text
<label>-admiral
<label>-agentics
<label>-api
<label>-frontend
```

Comandos:

```bash
pi/team.sh session list
pi/team.sh session current
pi/team.sh session new <nueva-etiqueta>
pi/team.sh session resume <etiqueta>
```

Cambiar o crear una sesión reinicia los roles coordinadamente. Los workers deben estar idle.

Una sesión nueva empieza con conversación vacía; por eso el estado importante debe estar en Git,
especialmente en `specs/<US>-<slug>/`. Las sesiones históricas pueden ayudar a recuperar contexto,
pero deben contrastarse con Git, ADO y el runtime actual.

## Adaptación a otro stack

### Cambiar repositorios o rutas

Editar:

```text
protocols/worker-registry.md
```

Actualizar la tabla de workers y sus rutas. Después comprobar:

```bash
pi/team.sh status
```

Cada worker solo debe escribir en su repositorio asignado.

### Cambiar roles

Actualizar conjuntamente:

```text
protocols/worker-registry.md
.github/agents/<rol>.agent.md
pi/roles/worker.md
```

Los nombres deben seguir la regla del registry. No inventar aliases distintos para un mismo worker.

### Cambiar skills o paquetes

Revisar:

```text
pi/launch.sh
pi/team-config/<rol>/settings.example.json
```

`launch.sh` genera las settings reales. Las rutas absolutas de `/root` deben convertirse en
variables o rutas válidas para el nuevo host; no copiar literalmente settings de otro pod sin
revisarlas.

### Cambiar la persistencia de memoria

El mínimo reproducible es versionar:

```text
specs/<US>-<slug>/
protocols/
CLOSURE-STATUS.md
```

Para memoria adicional se pueden respaldar las sesiones bajo `~/.pi-team/<rol>/sessions/`, pero
sin incluir credenciales ni ficheros temporales. Una memoria recuperada siempre debe verificarse
contra commit, fecha, rama y estado actual.

## Arranque después de recrear el pod

Los siguientes elementos suelen desaparecer:

- tmux y sus procesos.
- `~/.pi-team/` runtime.
- Entornos bajo `/tmp`.
- Builds `.next` enlazados a `/tmp`.
- Instalaciones hechas manualmente en el sistema.

Procedimiento:

```bash
cd /root/soarplus-dev-orchestration
pi/team.sh up
pi/team.sh status
```

Después reconstruir los runtimes de producto siguiendo sus runbooks, no relanzar evaluaciones
automáticamente y verificar primero AgentCard, salud, credenciales y conexión de cada servicio.

## Verificación mínima

```bash
pi/team.sh status
pi/team.sh session current
```

Comprobar además:

- Cada ventana tiene el rol esperado.
- Todos los roles aparecen conectados a pi-link.
- El repositorio de cada worker existe y está en la branch esperada.
- No hay un worker implementando antes de cambiar sesión.
- Las skills necesarias están disponibles.
- Los secretos existen solo fuera de Git.
- El estado de la feature está en `specs/`.

## Backup y recuperación

### Versionar en Git

- `pi/`.
- `protocols/`.
- `.github/agents/`.
- `.pi/prompts/`.
- `.agents/skills/`.
- `specs/` y runbooks.
- `pi/team-config/` como templates no secretos.

### Respaldar por separado

- Sesiones Pi históricas.
- `~/.pi/agent/auth.json` mediante mecanismo seguro.
- Secretos/PATs en un secret manager.
- Repositorios de workers.
- Datos de DocumentDB y resultados de evaluación.

Nunca poner estos elementos sensibles en el repositorio.

## Troubleshooting

### Worker `running` pero `NOT connected`

```bash
pi/team.sh attach <rol>
```

Suele indicar una pregunta de confianza del proyecto o un fallo de arranque.

### Falta tmux

```bash
pi/team.sh up
```

El script intenta instalarlo.

### Falta pi-link

```bash
pi install npm:pi-link@0.5.2
pi/team.sh up
```

### Falta un repositorio

Comprobar la ruta del registry y la existencia del `.git` del repositorio.

### Se perdió una sesión

Usar `pi/team.sh session list`. Si no está disponible, reconstruir el contexto desde Git y
`specs/<US>-<slug>/`; no asumir que el historial de conversación es la fuente de verdad.

## Límites de este documento

Este documento levanta el equipo de agentes Pi. No despliega automáticamente:

- SystemDevAgent.
- Quality API.
- Frontend.
- DocumentDB.
- CronJobs.
- ADO.

Esos componentes tienen sus propios runbooks y permisos. La operación segura exige autorización
explícita para evaluaciones, reinicios, escrituras, push, PR, merge y deploy.
