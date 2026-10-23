# Equipo de agentes Pi (pi-link)

Un equipo de agentes [Pi](https://pi.dev) que se coordinan en tiempo real por
[pi-link](https://pi.dev/packages/pi-link), sin Docker: cada rol es una sesión de Pi en una ventana
de tmux, dentro de este mismo pod. Parte de la idea de [ucpdh23/team](https://github.com/ucpdh23/team).

Es independiente de la orquestación de Copilot (`.github/agents/`, `protocols/task-envelope.md`...),
que sigue intacta.

## Roles

| Rol | Qué hace | Directorio de trabajo |
|---|---|---|
| `admiral` | Planifica con el usuario (spec, plan, tasks, gates), gestiona el equipo, reparte el trabajo aprobado y registra el estado | este repo |
| `agentics`, `api`, `frontend` | Un worker por repo, en dos modos: `ANALYZE` (solo lectura) e `IMPLEMENT` | su repo |

Los workers se definen en la tabla "Pi team" de `protocols/worker-registry.md`. Los scripts leen de
ahí el repo de cada uno. Añadir un worker es añadir una fila.

## Ficheros

| Fichero | Para qué |
|---|---|
| `team.sh` | Arranca, para, vigila y cambia de sesión al equipo |
| `launch.sh` | Arranca un rol. No se usa a mano: lo llama `team.sh` |
| `lib.sh` | Funciones comunes |
| `team.md` | Contexto común de todos los agentes (cómo hablar por pi-link, reglas) |
| `roles/admiral.md`, `roles/worker.md` | Contexto propio de cada rol |

`launch.sh` genera `~/.pi-team/<rol>/AGENTS.md` juntando `team.md` y el fichero del rol. Pi lo carga
junto al `AGENTS.md` del repo del rol, sin sustituirlo.

## Puesta en marcha

1. **Login, una sola vez**, en un terminal normal: `pi`, luego `/login`, y sal con `Ctrl+D`. Los
   roles reutilizan ese login. No lo hagas dentro de un rol.
2. `pi/team.sh up` arranca todos los roles, `admiral` primero (queda como hub de pi-link).
3. `pi/team.sh status` comprueba que todo está arriba y conectado.
4. La primera vez, `api` pregunta "Trust project folder" (tiene `.agents/skills`):
   `pi/team.sh attach api`, elige "Trust" y sal con `Ctrl-b d`.

Nada arranca solo. Tras reiniciar el pod hay que repetir `up`.

## Comandos

```bash
pi/team.sh up                  # arranca todo (reinstala tmux si falta)
pi/team.sh down                # para todo
pi/team.sh status              # tabla por rol; sale con 1 si algo falta
pi/team.sh attach <rol>        # abre un rol; cada terminal conserva el suyo
pi/team.sh watch               # todos los roles a la vez, en mosaico y en vivo
pi/team.sh start|stop|restart <rol>
pi/team.sh session list|current|new [etiqueta]|resume <etiqueta> [--force]
```

En VS Code hay tareas equivalentes: `team: up`, `team: attach`, `team: status`, `team: watch`,
`team: down`.

`status` muestra, por rol, la ventana de tmux (`running`, `DEAD`, `missing`) y si está conectado a
pi-link. Un rol `running` pero `NOT connected` está atascado, normalmente esperando una pregunta
(como el Trust de `api`): entra con `attach`.

## tmux en cinco líneas

- `Ctrl-b` es la tecla Ctrl más `b`, soltando ambas, y después la tecla de la acción.
- `Ctrl-b d` sale sin parar los agentes. **No uses `Ctrl+D` dentro de un agente**: cierra Pi.
- `attach <rol>` da a cada terminal de VS Code su propio rol. Sin rol, abre la sesión compartida, y
  todas las terminales cambian de ventana a la vez.
- Historial: la rueda del ratón (activada) o `Ctrl-b [` y luego `PageUp`/`PageDown`; `q` sale.
  Seleccionar texto con el ratón requiere `Shift`.
- En el mosaico de `watch`: clic para cambiar de panel, `Ctrl-b z` para ampliar uno.

Si VS Code se queda con `Ctrl+B` (abre y cierra la barra lateral), usa el ratón o cambia el prefijo
de tmux en `~/.tmux.conf`.

## Sesiones

Cada rol guarda su conversación en una sesión de Pi. El equipo cambia de sesión **a la vez**:

```bash
pi/team.sh session list          # sesiones disponibles; * = en uso
pi/team.sh session new 696       # sesión nueva en todos los roles
pi/team.sh session resume 696    # volver a una anterior en todos los roles
```

Se puede hacer a mano o pidiéndoselo al `admiral` ("empieza una sesión nueva para la US 696",
"recupera la sesión 696"). Solo debe hacerlo cuando se lo pidas.

Cómo funciona:

- Una **sesión de equipo** es una etiqueta. El rol `R` usa la sesión de Pi `<etiqueta>-R`, por
  ejemplo `696-api`. La etiqueta en uso está en `~/.pi-team/team-session`; si no existe, es
  `soarplus`.
- Al arrancar, cada rol abre la sesión de esa etiqueta, que se crea si no existe. Por eso al
  reiniciar un agente o el pod se retoma la sesión más reciente del equipo.
- Cambiar de sesión **reinicia los roles** (workers primero, `admiral` al final). Un Pi en marcha no
  puede cambiar de sesión por sí mismo.
- Si el comando lo ejecuta el `admiral`, su reinicio lo hace tmux unos 3 segundos después.

Reglas:

- Se rechaza el cambio si algún worker no está `idle`, y dice cuál. `--force` lo salta; úsalo solo
  si sabes que no hay trabajo en curso.
- `new` no acepta una etiqueta que ya existe (usa `resume`) ni caracteres fuera de letras, dígitos,
  `.` y `-`.
- Con `new`, las conversaciones empiezan vacías: el estado importante debe estar en Git
  (`specs/<US>-<slug>/`).
- No uses `/new` ni `/resume` dentro de un rol: al reiniciarlo vuelve a la sesión del equipo.

Dónde están: `~/.pi-team/<rol>/sessions/--<ruta del repo>--/<fecha>_<etiqueta>-<rol>.jsonl`. La
conversación completa se puede ver en Pi con `/tree` o `/export`, o fuera con `pi --export <fichero>`.
Los mensajes de pi-link quedan guardados dentro de la sesión.

## Cómo hablan los agentes

- Herramientas de pi-link: `link_send`, `link_list`, `link_compact`. **No hay `link_prompt`** (se
  eliminó en pi-link 0.3.0; Pi 0.87.1 exige 0.5.2). El envío es asíncrono y sin correlación, así que
  cada mensaje lleva una cabecera `[ASK|ANSWER|ASSIGN|ACK|DONE|BLOCKED id=...]`. El detalle está en
  `team.md`.
- Un worker solo acepta `ASSIGN` y `ASK` del `admiral`. El enlace no tiene autenticación: cualquier
  proceso del pod puede enviar mensajes.
- Todos los roles están en el grupo `soarplus` (`<rol>@soarplus`). pi-link solo escucha en
  `127.0.0.1:9900`; el primer agente en arrancar es el hub. Estado: `curl 127.0.0.1:9900/status`.
- Un rol no puede estar dos veces: `launch.sh` se niega si ya está conectado.

## Qué vive dónde

| Ruta | Contenido | Sobrevive a un reinicio del pod |
|---|---|---|
| `~/.pi/agent` | Pi, login (`auth.json`) y el paquete pi-link | Sí |
| `~/.pi-team/<rol>` | `AGENTS.md` generado, `settings.json`, sesiones del rol | Sí |
| `~/.pi-team/team-session` | Etiqueta de la sesión de equipo en uso | Sí |
| `~/.tmux.conf` | Ratón, historial de 50000 líneas, teclas extendidas | Sí |
| `tmux` y los procesos | El binario, las sesiones y los agentes | **No**: `team.sh up` reinstala tmux |

`/root` es un volumen aparte (se llena: vigílalo); el resto del contenedor se recrea.

## Pendiente

- Spec Kit para Pi: el repo solo tiene la integración de Copilot (`specify integration install pi`
  existe, pero `pi` y `copilot` no son compatibles a la vez). Hasta entonces el `admiral` no puede
  ejecutar `/speckit.*`.
- Herramientas de Azure DevOps para los agentes: son de VS Code.
- Aviso al humano cuando el `admiral` espera una decisión (idea de la extensión `notify-human` del
  repo de referencia).
- Aislamiento: todos los roles corren con el mismo usuario y pueden tocar cualquier repo; los límites
  de escritura dependen de las instrucciones, no de la infraestructura.
