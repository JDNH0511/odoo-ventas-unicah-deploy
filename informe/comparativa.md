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

## Decisión

Se elige **Northflank Sandbox** porque es el único servicio evaluado que cumple simultáneamente:

1. **Sin tarjeta de crédito.**
2. **Siempre encendido** (a diferencia de Render, Railway y Koyeb).
3. **Base de datos PostgreSQL incluida** y permanente.
4. Permite **construir desde Dockerfile** y exponer el **puerto 8070**.
5. Con `nf-compute-50` (0.5 vCPU / 1 GB) para Odoo y un addon PostgreSQL pequeño, el consumo total ronda los **$19–20/mes**, dentro del límite gratuito de $20.

> Nota operativa: si la consola rechaza la combinación por el límite de $20, se usa `nf-compute-50` para Odoo y un addon PostgreSQL de 0.1 vCPU/256 MB; si aun así no cabe, se migraría la BD a Neon Free (sin tarjeta, permanente) manteniendo Northflank solo para el contenedor.

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
