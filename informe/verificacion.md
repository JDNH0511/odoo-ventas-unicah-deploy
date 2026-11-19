# Verificación automática en producción

- Fecha: 2026-11-18T20:09:12-06:00
- URL: https://odoo-unicah-yes5.onrender.com
- Base de datos: odoo_prod_66u0
- Versión: {"server_version": "20.0-20261112", "server_version_info": [20, 0, 0, "final", 0, ""], "server_serie": "20.0", "protocol_version": 1}
- Resultado: **16/16 pruebas correctas**

| Prueba | Resultado | Detalle |
|---|---|---|
| Login público | OK | HTTP 200 en /web/login con formulario de acceso |
| Versión de Odoo | OK | Odoo 20.0-20261112 |
| Módulo instalado | OK | ventas_unicah en estado installed |
| Campos del módulo | OK | 6 campos presentes en los modelos |
| Vistas del módulo | OK | vistas de formulario, lista y búsqueda |
| Usuario de revisión | OK | login review_admin con permisos de administrador y ventas |
| Canal preferido → canal_venta | OK | canal_preferido=web se propaga al pedido |
| Total de unidades | OK | 6 unidades calculadas y almacenadas |
| Aprobación requerida (> 50,000) | OK | 60,000 → True; 50,000 → False (umbral estricto) |
| Pendiente de aprobación | OK | pedido > 50,000 en borrador aparece como pendiente |
| Bloqueo de confirmación sin aprobar | OK | El pedido S00022 supera 50,000 y debe ser aprobado por un administrador de ventas antes de confirmarse. |
| Permisos por grupo | OK | sin grupo = rechazado; sales manager = aprobado |
| Aprobación por administrador de ventas | OK | sales_team.group_sale_manager aprueba el pedido |
| Pendiente se limpia al aprobar | OK | pendiente_aprobacion pasa a False tras la aprobación |
| Confirmación tras aprobación | OK | estado tras confirmar: sale |
| copy=False en aprobado_por | OK | original aprobado; copia aprobado_por=False |
