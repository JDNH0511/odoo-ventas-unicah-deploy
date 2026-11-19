# Problemas encontrados y resoluciones

## 1. Docker Desktop no arranca en local (WSL2 ausente y sesión sin privilegios de administrador)

- **Síntoma:** `docker build` / `docker run` locales fallan con
  `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`.
- **Diagnóstico:** el CLI de Docker 29.9.2 está instalado, pero `wsl --status` informa
  «El Subsistema de Windows para Linux no está instalado» y la sesión actual **no es administrador**,
  por lo que no se puede instalar WSL2 ni habilitar Hyper-V de forma automatizada.
- **Resolución:** no se modifica el equipo del usuario (instalar WSL/reiniciar requiere elevación y reinicio).
  La imagen se valida en el despliegue remoto de Northflank, que construye el `Dockerfile` en su propio
  entorno Linux. Aquí se dejaron `Dockerfile`, `odoo.conf` y `entrypoint.sh` listos para esa construcción.
- **Estado:** solucionado por migración de la prueba al entorno de integración continua de la plataforma.

## 2. GitHub CLI no estaba instalado

- **Síntoma:** `gh: El término 'gh' no se reconoce...`.
- **Resolución:** instalación silenciosa con
  `winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements --disable-interactivity`.
  Quedó en `C:\Program Files\GitHub CLI\gh.exe` (versión 2.105.0).
- **Estado:** resuelto. Queda pendiente solo la autorización interactiva del usuario (`gh auth login`).

## 3. Adaptaciones de Odoo 20 confirmadas desde el código del módulo

- `res.users` usa `group_ids` en Odoo 20 (el módulo usa `has_group`, que es estable).
- La vista de lista `sale.sale_order_tree` es `<list>`; los xpath usados son compatibles.
- Se mantiene `copy=False` en `aprobado_por` para que la copia no quede aprobada.
- **Estado:** verificado por lectura directa de los 7 archivos del módulo en `C:\Users\joseh\odoo_deploy\ventas_unicah`.
