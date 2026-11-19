# Comparativa de servicios gratuitos para desplegar Odoo 20 + PostgreSQL

**Fecha de la investigación:** 18 de noviembre de 2026  
**Investigador:** agente DevOps (para Jose Nieto, Programación de Negocios)  
**Restricción aplicada:** 100 % gratuito, sin tarjeta, sin upgrade, sin trials que se cobren.

## Criterios

Odoo 20 con `sale_management` necesita aproximadamente **1 GB de RAM** para arrancar de forma estable; con 512 MB suele fallar al instalarse. Por eso se descartan planes gratuitos de 512 MB para el servicio web.

| Servicio | Plan gratuito actual | RAM web | PostgreSQL gratuito | ¿Tarjeta? | Inactividad / caducidad | Docker + puerto propio | Veredicto |
|---|---|---|---|---|---|---|---|
| **Northflank Sandbox (ELEGIDO)** | Sandbox: 2 servicios, 2 jobs, 1 base de datos, **hasta $20/mes de recursos**, siempre encendido | Hasta `nf-compute-50` = 0.5 vCPU / 1 GB (≈$12.16/mes) y `nf-compute-100-1` = 1 vCPU / 1 GB (≈$18.25/mes) | 1 addon PostgreSQL incluido (≈$7/mes con 0.2 vCPU + 512 MB + 1 GB disco) | **No** | Sin suspensión por inactividad, sin caducidad del plan | Sí (Dockerfile, imagen pública, puerto configurable) | **Mejor opción:** sin tarjeta, siempre activo, permite Odoo + BD dentro del tope de $20/mes |
| Render | Web service Free + Postgres Free | 512 MB, 0.1 CPU | 256 MB, 1 GB, **caduca a los 30 días** | No | Web duerme tras 15 min; BD se borra tras 30 días + 14 de gracia | Sí | Descartado: 512 MB insuficiente y la BD desaparece al mes |
| Railway | Free: $1/mes de uso, 3 servicios | 512 MB por servicio | 0.5 GB volumen | No | Duerme a los 5–10 min; $1 se agota rápido; el Trial de $5 dura 30 días | Sí | Descartado: RAM insuficiente y crédito insuficiente para Odoo + BD |
| Koyeb | 1 servicio free + Postgres free | 512 MB, 0.1 vCPU | 1 GB, **5 horas activas/mes** | **Sí** (preautorización de $29) | Duerme al cabo de una hora | Sí | Descartado: exige tarjeta y la BD solo 5 h/mes |
| Oracle Cloud Always Free | VM ARM 4 OCPU / 24 GB + Autonomous DB | 24 GB | Autonomous DB 2 CPU / 2 GB (never expire) | Normalmente **sí** para verificarse | Sin caducidad mientras haya actividad | Sí | Descartado: requiere tarjeta y registro humano; más complejo de automatizar |
| Neon (solo como BD alternativa) | Free permanente, 100 proyectos | n/a | 1 GB/projecto, 100 CU-h, scale-to-zero a los 5 min; **no pausa projects por inactividad** | No | Datos conservados; compute suspendido cuando ocioso | n/a | Buena alternativa de BD si el addon de Northflank no alcanzara |

## Decisión inicial y cambio (18/11/2026)

Inicialmente se eligió **Northflank Sandbox**. Sin embargo, al crear la cuenta la consola **exigió introducir y verificar un método de pago even para un cobro de $0**, y la verificación fue rechazada. Esto incumple la restricción obligatoria «100 % gratuito, sin tarjeta», por lo que **Northflank queda descartado** y no se insistió con otra tarjeta.

### Decisión final: **Render (plan Free)**

| Servicio | Plan elegido | Coste | Tarjeta | Detalle |
|---|---|---|---|---|
| Web Odoo | `free` (0.1 CPU / 512 MB RAM) | $0 | **No** | Docker desde repositorio; el contenedor debe escuchar en el puerto que Render inyecta como `$PORT`. Mapeo documentado: Odoo escucha `$PORT` (8070 por defecto en local) y el puerto público del servicio es 443/HTTPS. |
| PostgreSQL | Render Postgres `free` (256 MB RAM, 1 GB disco) | $0 | **No** | Misma cuenta, misma región; se conecta por red privada. Caduca a los 30 días (con 14 días de gracia). Para una revisión académica en los próximos días es suficiente; se documenta la limitación. |

**Justificación del cambio:** Render es el único servicio evaluado que, sin pedir tarjeta, permite desplegar un contenedor Docker y una base PostgreSQL administrada. Sus contrapartidas (512 MB de RAM, suspensión tras 15 min de inactividad y BD de 30 días) se mitigan así:

- RAM: `workers = 0`, `max_cron_threads = 0`, `db_maxconn = 5`, sin demo y un solo proceso para reducir la huella de Odoo.
- Suspensión: Render muestra una página de arranque y levanta el servicio en ~1 min al abrir la URL; se documenta en el PDF.
- Caducidad de la BD: se registra la fecha de creación y se avisa de que hay que recrearla antes de 30 días si se necesita más adelante.

Fuentes añadidas: https://render.com/docs/free y https://render.com/pricing (consultados de nuevo el 18/11/2026).

## Fuentes consultadas (18/11/2026)

- Northflank pricing: https://northflank.com/pricing
- Northflank compute plans and quotas: https://northflank.com/docs/v1/application/billing/resource-plans-and-quotas
- Northflank sandboxes on cloud: https://northflank.com/docs/v1/application/sandboxes/sandboxes-on-northflank-cloud
- Northflank API (planes públicos): https://api.northflank.com/v1/plans
- Render free docs: https://render.com/docs/free
- Render pricing: https://render.com/pricing
- Railway free plan: https://docs.railway.com/pricing/free-plan
- Railway plans: https://docs.railway.com/pricing/plans
- Koyeb pricing FAQ: https://www.koyeb.com/docs/faqs/pricing
- Koyeb databases: https://www.koyeb.com/docs/databases
- Neon pricing: https://neon.com/pricing
- Supabase pricing: https://supabase.com/pricing
- Oracle Cloud Free Tier: https://www.oracle.com/cloud/free/
