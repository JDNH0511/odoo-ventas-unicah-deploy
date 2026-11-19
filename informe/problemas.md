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

## 2. Northflank exige tarjeta pese a anunciar plan «sin tarjeta»

- **Síntoma:** al dar de alta la cuenta Sandbox aparece un paso de pago para un cobro de $0; al introducir la tarjeta, «no se puede verificar el método de pago».
- **Decisión:** no se reintentó con otra tarjeta. La restricción del proyecto prohíbe cualquier servicio que exija tarjeta, así que se descarta Northflank.
- **Resolución:** migración a **Render Free** (web Docker + Postgres), que permite alta y despliegue sin método de pago. La comparativa y la justificación se actualizaron en `informe/comparativa.md`.
- **Estado:** resuelto por cambio de plataforma.

## 3. GitHub CLI no estaba instalado

- **Síntoma:** `gh: El término 'gh' no se reconoce...`.
- **Resolución:** instalación silenciosa con
  `winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements --disable-interactivity`.
  Quedó en `C:\Program Files\GitHub CLI\gh.exe` (versión 2.105.0).
- **Estado:** resuelto. El usuario autorizó GitHub CLI y `gh auth status` confirmó la cuenta `JDNH0511`; el repositorio quedó público y sin secretos.

## 4. Adaptaciones de Odoo 20 confirmadas desde el código del módulo

- `res.users` usa `group_ids` en Odoo 20 (el módulo usa `has_group`, que es estable).
- La vista de lista `sale.sale_order_tree` es `<list>`; los xpath usados son compatibles.
- Se mantiene `copy=False` en `aprobado_por` para que la copia no quede aprobada.
- **Estado:** verificado por lectura directa de los 7 archivos del módulo en `C:\Users\joseh\odoo_deploy\ventas_unicah` y confirmado en producción por `informe/verificar.py`.

## 5. Render no detectaba el puerto expuesto

- **Síntoma:** el primer deploy terminaba tras ~15 min con `==> No open ports detected on 0.0.0.0, continuing to scan...` y la URL pública agotaba el tiempo de espera.
- **Diagnóstico:** Odoo escuchaba solo en `127.0.0.1`; Render exige que el contenedor escuche en `0.0.0.0` en el puerto inyectado como `$PORT` (10000 en Render).
- **Resolución:** se añadió `http_interface = 0.0.0.0` a `odoo.conf` y `entrypoint.sh` reescribe `http_port` a `$PORT`. Commit `1539d24`, deploy manual y servicio `Live` en 56.7 s.
- **Estado:** resuelto; `GET /web/login` devuelve HTTP 200.

## 6. `admin_passwd` no equivale a la contraseña del usuario `admin`

- **Síntoma:** la verificación XML-RPC no podía autenticar con `ODOO_ADMIN_PASSWD` aunque el valor estaba configurado como contraseña maestra en `odoo.conf`.
- **Diagnóstico:** Odoo inicializa la BD con el usuario `admin` y contraseña `admin`; la clave maestra solo autoriza operaciones de base de datos.
- **Resolución:** se autenticó una vez con `admin/admin` y se actualizó la contraseña del usuario `admin` por XML-RPC al valor de `ODOO_ADMIN_PASSWD`, sin mostrarlo en consola ni en capturas.
- **Estado:** resuelto; la verificación completa quedó en 16/16.

## 7. Impuesto por defecto y API de `copy` en Odoo 20

- **Síntoma:** la primera prueba de umbral marcó 50,000 como aprobable porque el producto de prueba arrastraba un impuesto (total 57,500), y la copia falló por diferencias de firma de `copy()`/`read()`.
- **Resolución:** el script crea el producto con `taxes_id` vacío, usa dominios planos de Odoo 20 y toma el ID devuelto por `copy()` desde una lista.
- **Estado:** resuelto; umbral y `copy=False` verificados correctamente.
