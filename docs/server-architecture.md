# Arquitectura del servidor

El servidor conserva las rutas, métodos, cuerpos JSON, códigos HTTP, comandos
remotos y formatos SSE existentes. No se introduce una capa de entidades ni
cambios de funcionalidad. Este refactor se puede fusionar sin el de la UI.

## Recorrido de una petición

`http/handler.py` → `http/routes.py` → `http/controllers.py` →
`application/use_cases/` → contratos → adaptadores de `infrastructure/`.

- **`main.py`** es el punto de composición: crea las dependencias compartidas y
  las inyecta. `run_server(github_client)` sigue siendo la entrada de la CLI.
- **`http/routes.py`** enumera explícitamente los endpoints y sus métodos.
- **`http/handler.py`** lee JSON, escribe respuestas y sirve los archivos de la UI.
  **`http/events.py`** mantiene el framing SSE, heartbeats y limpieza de
  suscripciones; desconectar un navegador no cierra la sesión SSH compartida.
- **`http/controllers.py`** extrae los campos del cuerpo y convierte `Outcome` a
  códigos HTTP. Los casos de uso no importan HTTP ni adaptadores concretos.
- **`application/use_cases/`** agrupa operaciones por SSH, instalación,
  infraestructura, tokens, actualización, versiones y Discord.
- **`application/contracts/ports.py`** documenta las dependencias mediante
  `Protocol`: almacenamiento, comandos remotos, releases, instalación local,
  entorno `.env`, estado de trabajos y envío a Discord. Se pueden sustituir
  por dobles de prueba sin heredar de una implementación.
- **`application/contracts/result.py`** define `Result = (payload, outcome)`.
  `payload` conserva las claves públicas; `outcome` expresa el resultado y el
  controlador selecciona su representación HTTP.
- **`infrastructure/`** contiene JSON, SSH, PyPI, pip, `.env`, Discord HTTP y
  trabajos/lectores de logs. Estos adaptadores conservan los efectos existentes.
- **`components/`** mantiene pequeños exports de compatibilidad para imports
  anteriores. El código nuevo debe usar la nueva estructura.

Los casos de uso se construyen una vez al iniciar el servidor; cada petición
recibe un handler nuevo. El almacenamiento, sesión SSH, estado de instalación y
suscriptores siguen siendo compartidos, como antes.

## Mapa de endpoints

| Método | Endpoint | Caso de uso / transporte |
| --- | --- | --- |
| GET | `/version` | VersionUseCases |
| POST | `/ssh/login`, `/ssh/logout` | SshUseCases |
| POST | `/scorpio/setup` | SetupUseCases |
| GET | `/scorpio/setup/status` | SetupUseCases |
| GET | `/scorpio/setup/events` | SSE de instalación |
| GET | `/scorpio/start`, `/scorpio/stop` | InfrastructureUseCases |
| POST | `/scorpio/reboot` | InfrastructureUseCases |
| GET | `/scorpio/logs/live` | SSE de Docker |
| GET, POST | `/scorpio/setup/token` | TokenUseCases |
| GET, POST | `/scorpio/update` | UpdateUseCases |
| GET | `/discord/settings` | DiscordUseCases |
| POST | `/discord/setup`, `/discord/set-channel` | DiscordUseCases |
| POST | `/discord/set-alert-gap`, `/discord/remove`, `/discord/notify` | DiscordUseCases |

Se conservan incluso las operaciones start/stop por GET. Cambiar verbos,
validación o modelos públicos corresponde a otro cambio funcional.
La actualización pip y el archivo `.env` siguen perteneciendo al host local.

## Cómo extenderlo

1. Añadir la operación al caso de uso correspondiente. Si necesita una nueva
   dependencia externa, documentar su contrato en `application/contracts/`.
2. Implementar el adaptador y conectarlo en `main.py`.
3. Registrar método/ruta y adaptar el cuerpo en el controlador si es necesario.
4. Cubrir respuestas, errores y efectos mediante dobles de las dependencias.

## Verificación

```sh
python -m unittest discover -s tests -p 'test_server*.py' -v
ruff check scorpio/server
ruff format --check scorpio/server
```

Ruff usa `scorpio/server/ruff.toml`: PEP 8, imports ordenados, líneas de 79
caracteres y Python 3.10. Instalar Ruff en el entorno de desarrollo si no está
presente; no se agrega como dependencia de producción.

Las pruebas ejercitan el parser y escritor HTTP reales con sockets en memoria,
las respuestas públicas, persistencia, comandos, fallos y streaming SSE. No
contactan Raspberry Pi, PyPI ni Discord, ni ejecutan una actualización real.

La suite general `python -m unittest discover -s tests` ya presentaba cuatro
fallos en `test_cli.py` en la base `9a9bef7`: la lista de comandos está
incompleta y tres pruebas simulan `subprocess.run` aunque la CLI usa `Popen`.
Se mantienen fuera de este refactor; la suite del servidor pasa por separado.
