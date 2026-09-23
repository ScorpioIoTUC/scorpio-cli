# Arquitectura de la UI

La UI mantiene las mismas páginas, apariencia, textos, rutas, peticiones y
comportamiento. Este refactor es independiente del servidor: ambos PR parten
de `main` y se pueden fusionar en cualquier orden.

## Separación de responsabilidades

```text
src/
  api/
    endpoints.ts        Catálogo de rutas del backend
    contracts.ts        Respuestas y contratos compartidos
    http.ts             Único transporte fetch y normalización de errores
    events.ts           Único transporte EventSource y cierre de suscripciones
    ssh/                Login/logout y contratos de sesión
    setup/              Instalación, estado y eventos de progreso
    infrastructure/     Start, stop y reboot
    logs/               Suscripción a logs de Docker
    token/              Lectura y guardado de la configuración API
    version/            Consulta de versiones
    update/             Consulta y ejecución de actualización local de la CLI
    discord/            Ajustes y contratos de Discord
  pages/
    landing/
      components/       Tarjetas, paneles y filas de logs
      hooks/            Estado, acciones, filtros y suscripciones del dashboard
      logs/             Filtrado puro y asignación de colores
      styles/           Reglas CSS separadas conservando la cascada
    login/hooks/        Login y estado de la petición
    settings/hooks/     Carga, formularios y mensajes de configuración
    updates/hooks/      Carga de versiones y estado de actualización
  components/           Elementos visuales compartidos
  helpers/              Persistencia de la sesión del navegador
```

Las páginas componen la interfaz. Los hooks coordinan estado, efectos y
acciones. Los módulos `api/*Api.ts` contienen las operaciones del backend y
usan contratos documentados `*Types.ts`; no importan React. Los componentes
no construyen URLs ni llaman directamente a `fetch` o `EventSource`.

`Dashboard.tsx` reemplaza el archivo general de 349 líneas. La instalación,
infraestructura, panel de servicios, tabla, filas y detalle de logs tienen
componentes pequeños. Los hooks se mantienen montados en el dashboard para
conservar filtros y estado al cambiar la instalación.

La lógica de ajustes y actualizaciones también está separada de sus páginas.
La sección visual de Discord continúa oculta, como antes; se conservan su
consulta inicial y operaciones disponibles sin habilitar funciones nuevas.

## Contratos y conexión al backend

- `api/endpoints.ts` concentra las rutas. El método y cuerpo de cada operación
  están en su módulo API.
- `http.ts` usa `VITE_API_URL` (o el mismo origen si no está definido), conserva
  los headers JSON y expone `ApiError` con mensaje y código de respuesta.
- `events.ts` conserva las URLs relativas de SSE y su reconexión nativa. Igual
  que antes, `VITE_API_URL` solo afecta JSON; desarrollo y preview usan el proxy
  de Vite. Unificar ambos orígenes sería un cambio funcional separado.
- Cada suscripción devuelve `Unsubscribe`: el hook debe invocarlo al limpiar
  el efecto. Cerrar un stream no ejecuta logout.
- Los tipos conservan los nombres del backend, incluso `snake_case` y
  `camelCase` mezclados. `infrastructure.services` es opcional porque el
  endpoint de estado actualmente solo devuelve `status`; la versión local
  de la CLI puede ser `null` si no está instalada.
- Los endpoints de inicio/parada siguen usando GET. La actualización sigue
  ejecutándose en el host local y conserva el aviso de reinicio.

## Límite de tamaño

Todos los archivos `.ts`, `.tsx` y `.css` de `src/` tienen como máximo 200
líneas físicas, contando comentarios y blancos internos. La comprobación
falla si aparece un archivo mayor, transporte fuera de los dos módulos
permitidos o dependencias de React dentro de `api/`.

Prettier mantiene un formato consistente (`npm run format` para aplicarlo).

Los estilos largos se dividen por secciones mediante `@import`, sin cambiar
reglas ni orden. El CSS de producción resultó idéntico al de `main`.

## Verificación y desarrollo

Desde `scorpio/ui`, con Node 20 o superior:

```sh
npm ci
npm run check:architecture
npm run format:check
npm run typecheck
npm test
npm run build
```

Las pruebas usan el runner nativo de Node, Vite para compilar TypeScript y
`react-test-renderer` para montar/desmontar hooks. Se simulan las fronteras de
red y navegador: no se contacta al backend ni a servicios externos.

Se cubren métodos, rutas, cuerpos, errores, SSE y su limpieza, filtros de logs,
login/logout, redirección al perder la sesión SSH, actualización de versiones,
validación y guardado de tokens, y eliminación de temporizadores.

Durante el refactor también se compararon los árboles renderizados de login,
landing, ajustes y actualizaciones contra `main` (`9a9bef7`), con instalación
idle/completed y logs simulados: la estructura visual coincide. Esta comparación
puntual no sustituye pruebas con una Raspberry Pi real.

Para extender una función, definir primero el contrato/ruta en `api/`, añadir
la operación y consumirla desde un hook de la página. Extraer componentes por
responsabilidad y ejecutar las comprobaciones antes de enviar cambios.
