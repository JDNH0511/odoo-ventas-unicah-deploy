# odoo_deploy — despliegue gratuito de Odoo 20 + `ventas_unicah`

Copia de despliegue. **No modifica** `C:\Users\joseh\odoo` ni `C:\Users\joseh\custom_addons`.

## Producción

- **URL pública:** <https://odoo-unicah-yes5.onrender.com>
- **Plataforma:** Render Free (web Docker + PostgreSQL), región Oregon.
- **Repositorio:** <https://github.com/JDNH0511/odoo-ventas-unicah-deploy>
- **Usuario de revisión:** `review_admin` (contraseña solo en `secretos.local.txt`).
- **Verificación:** `informe/verificacion.md` (16/16 pruebas correctas).

## Contenido

- `Dockerfile`: imagen oficial `odoo:20.0`, copia `ventas_unicah/` a `/mnt/extra-addons`, `EXPOSE 8070`.
- `odoo.conf`: `http_port = 8070`, `http_interface = 0.0.0.0`, `list_db = False`, `proxy_mode = True`, `workers = 0` y valores sensibles como `${VARIABLE}`.
- `entrypoint.sh`: renderiza la configuración, espera a PostgreSQL, inicializa con `-i base,sale_management,ventas_unicah` y arranca Odoo.
- `informe/`: comparativa, problemas, capturas, verificación PDF final.

## Mapeo de puertos

En local Odoo usa `8070`. Render inyecta `PORT=10000`; el entrypoint reescribe `http_port` a ese valor y Odoo escucha en `0.0.0.0`. El tráfico público entra por HTTPS en el puerto 443 y Render lo reenvía al contenedor en 10000.

## Variables de entorno (nunca en el repo)

| Variable | Descripción |
|---|---|
| `DB_HOST` | Host interno de PostgreSQL en Render |
| `DB_PORT` | Puerto de PostgreSQL (5432) |
| `DB_NAME` | Nombre real de la BD (`odoo_prod_66u0`) |
| `DB_USER` | Usuario de PostgreSQL |
| `DB_PASSWORD` | Contraseña de PostgreSQL |
| `ODOO_ADMIN_PASSWD` | Contraseña maestra de Odoo y del usuario `admin` |
| `REVIEW_ADMIN_PASSWORD` | Contraseña del usuario de revisión (solo local) |
| `PORT` | impuesto por Render (10000); documentado arriba |

Las contraseñas se guardan solo en `secretos.local.txt` (ignorado por git).

## Verificación en producción

```powershell
& 'C:\Users\joseh\odoo\venv\Scripts\python.exe' informe\verificar.py
```

El script crea datos temporales, comprueba 16 comportamientos del módulo y elimina los datos al terminar. Escribe `informe/verificacion.md` y `informe/verificacion.json`.

## Prueba local (opcional)

Requiere Docker con WSL2; en este equipo no estaba disponible y se validó el build remotamente en Render.

```powershell
docker build -t odoo-unicah:20 .
docker run --rm -p 8070:8070 ^
  -e DB_HOST=host.docker.internal -e DB_PORT=5432 ^
  -e DB_NAME=odoo_deploy_test -e DB_USER=odoo -e DB_PASSWORD=... ^
  -e ODOO_ADMIN_PASSWD=... odoo-unicah:20
```

Abrir `http://localhost:8070`.
