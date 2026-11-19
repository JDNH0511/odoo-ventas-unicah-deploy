# odoo_deploy — despliegue gratuito de Odoo 20 + `ventas_unicah`

Copia de despliegue. **No modifica** `C:\Users\joseh\odoo` ni `C:\Users\joseh\custom_addons`.

## Contenido

- `Dockerfile`: imagen oficial `odoo:20.0`, copia `ventas_unicah/` a `/mnt/extra-addons`, `EXPOSE 8070`.
- `odoo.conf`: `http_port = 8070`, `list_db = False`, `proxy_mode = True`, `workers = 0` y todos los valores sensibles como `${VARIABLE}`.
- `entrypoint.sh`: renderiza la configuración, espera a PostgreSQL, inicializa con `-i base,sale_management,ventas_unicah` y arranca Odoo.
- `informe/`: comparativa, verificaciones, problemas, capturas y PDF final.

## Variables de entorno (nunca en el repo)

| Variable | Descripción |
|---|---|
| `DB_HOST` | Host de PostgreSQL |
| `DB_PORT` | Puerto de PostgreSQL (5432) |
| `DB_NAME` | Nombre de la BD (`odoo_prod`) |
| `DB_USER` | Usuario de PostgreSQL |
| `DB_PASSWORD` | Contraseña de PostgreSQL |
| `ODOO_ADMIN_PASSWD` | Contraseña maestra de Odoo |
| `PORT` | Opcional: si la plataforma impone un puerto, Odoo escucha ahí (se documenta el mapeo a 8070) |

Las contraseñas se generan localmente y se guardan solo en `secretos.local.txt` (ignorado por git).

## Prueba local

```powershell
docker build -t odoo-unicah:20 .
docker run --rm -p 8070:8070 ^
  -e DB_HOST=host.docker.internal -e DB_PORT=5432 ^
  -e DB_NAME=odoo_deploy_test -e DB_USER=odoo -e DB_PASSWORD=... ^
  -e ODOO_ADMIN_PASSWD=... odoo-unicah:20
```

Abrir `http://localhost:8070`.
