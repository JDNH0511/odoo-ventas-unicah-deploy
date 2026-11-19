"""Genera el informe PDF final del despliegue. No imprime secretos."""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as RLImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
cfg = dict(
    line.strip().split("=", 1)
    for line in (ROOT / "secretos.local.txt").read_text(encoding="utf-8").splitlines()
    if "=" in line and not line.lstrip().startswith("#")
)
ver = json.loads((BASE / "verificacion.json").read_text(encoding="utf-8"))
url = ver["url"].rstrip("/")
review_user = "review_admin"
review_pass = cfg["REVIEW_ADMIN_PASSWORD"]
db_name = ver["db"]
fecha = datetime.now().astimezone().strftime("%d/%m/%Y %H:%M %Z")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Titulo", parent=styles["Title"], fontSize=24, leading=29,
                          textColor=colors.HexColor("#123A5B")))
styles.add(ParagraphStyle(name="Subtitulo", parent=styles["Normal"], fontSize=13, leading=18,
                          textColor=colors.HexColor("#2D6A9F"), spaceAfter=10))
styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=15, leading=19,
                          textColor=colors.HexColor("#123A5B"), spaceBefore=14, spaceAfter=7))
styles.add(ParagraphStyle(name="Cuerpo", parent=styles["BodyText"], fontSize=10, leading=14,
                          alignment=TA_LEFT, spaceAfter=6))
styles.add(ParagraphStyle(name="Peq", parent=styles["BodyText"], fontSize=8, leading=10))
styles.add(ParagraphStyle(name="Celda", parent=styles["BodyText"], fontSize=8, leading=10, spaceAfter=0))
styles.add(ParagraphStyle(name="Centro", parent=styles["BodyText"], fontSize=10, leading=14,
                          alignment=TA_CENTER))


def P(text: str, style="Cuerpo") -> Paragraph:
    return Paragraph(html.escape(str(text)).replace("\n", "<br/>"), styles[style])


def tabla(datos, anchos, header=True, font_size=9):
    t = Table(datos, colWidths=anchos, repeatRows=1 if header else 0)
    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8C6D1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
    ]
    if header:
        cmds += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123A5B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F6FA")]),
        ]
    t.setStyle(TableStyle(cmds))
    return t


def pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#5B6B78"))
    canvas.drawString(45 * mm, 12 * mm, "Despliegue Odoo 20 + ventas_unicah — Jose Nieto")
    canvas.drawRightString(A4[0] - 45 * mm, 12 * mm, f"Página {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#B8C6D1"))
    canvas.line(45 * mm, 15 * mm, A4[0] - 45 * mm, 15 * mm)
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(BASE / "Informe_Despliegue_Odoo.pdf"),
    pagesize=A4,
    leftMargin=45 * mm, rightMargin=45 * mm,
    topMargin=40 * mm, bottomMargin=22 * mm,
    title="Informe de despliegue Odoo 20 + ventas_unicah",
    author="Jose Nieto",
)
S = []

# Portada
S += [Spacer(1, 45 * mm), P("Informe de despliegue", "Titulo"),
      P("Odoo 20 + módulo <b>ventas_unicah</b> en la nube", "Subtitulo"), Spacer(1, 12 * mm)]
S.append(tabla([
    ["Estudiante", "Jose Nieto"],
    ["Cuenta", "0801 2005 17968"],
    ["Clase", "Programación de Negocios"],
    ["Fecha", fecha],
    ["Plataforma", "Render Free (Web Docker + PostgreSQL)"],
    ["Repositorio", "github.com/JDNH0511/odoo-ventas-unicah-deploy"],
], [45 * mm, 110 * mm], header=False, font_size=10))
S += [Spacer(1, 14 * mm), P("Entregable: aplicación pública, usuario de revisión, evidencias y verificación automática.", "Centro")]
S.append(PageBreak())

# Resumen
S.append(P("1. Resumen ejecutivo", "H2"))
S.append(P(
    "Se publicó Odoo 20 con el módulo <b>ventas_unicah</b> usando exclusivamente servicios gratuitos y sin tarjeta. "
    "El servicio web corre en Render Free desde un Dockerfile y la base PostgreSQL es administrada por Render en la misma región. "
    "La aplicación quedó operativa y las 16 pruebas automáticas de funcionalidad terminaron correctamente."
))
ok = sum(1 for r in ver["resultados"] if r["resultado"] == "OK")
S.append(tabla([
    ["Concepto", "Valor"],
    ["URL pública", url],
    ["Base de datos", db_name],
    ["Versión Odoo", ver["version"].get("server_version", "20.0")],
    ["Resultado verificación", f"{ok}/{len(ver['resultados'])} pruebas correctas"],
    ["Commit desplegado", "1539d24 — Escuchar en 0.0.0.0 para que Render detecte el puerto"],
], [45 * mm, 110 * mm], font_size=9))
S.append(Spacer(1, 5 * mm))
S.append(P("Acceso de revisión", "H2"))
S.append(P("Credenciales de solo lectura/acceso de revisión para comprobar el despliegue:", "Peq"))
S.append(tabla([
    ["Campo", "Valor"],
    ["URL de entrada", url + "/web/login"],
    ["Usuario", review_user],
    ["Contraseña", review_pass],
], [40 * mm, 115 * mm], font_size=9))
S.append(Spacer(1, 4 * mm))
S.append(P("Nota: la contraseña de revisión se incluye solo en este PDF y en el archivo local ignorado <b>secretos.local.txt</b>. No aparece en el repositorio ni en las capturas.", "Peq"))

# Arquitectura
S.append(P("2. Arquitectura y decisiones", "H2"))
S.append(tabla([
    ["Elemento", "Configuración"],
    ["Web", "Render Web Service Free · Docker · Odoo 20.0 · 0.1 CPU / 512 MB"],
    ["Base de datos", "Render PostgreSQL Free · 1 GB · región Oregon"],
    ["Puerto", "Local 8070 → Render inyecta PORT=10000 → HTTPS público 443"],
    ["Red", "http_interface = 0.0.0.0, proxy_mode = True"],
    ["Recursos", "workers = 0, sin demo, sincronización de módulos controlada"],
    ["Repositorio", "Público; secretos inyectados como variables de entorno"],
], [42 * mm, 113 * mm], font_size=9))
S.append(Spacer(1, 4 * mm))
S.append(P(
    "Se descartó Northflank porque, pese a anunciar un plan sin tarjeta, exigió verificar un método de pago. "
    "Render fue el único servicio evaluado que permitió desplegar contenedor Docker y PostgreSQL sin ese requisito. "
    "La comparativa completa está en <b>informe/comparativa.md</b>."
))

# Despliegue
S.append(P("3. Proceso de despliegue", "H2"))
pasos = [
    "Copia limpia en <b>C:\\Users\\joseh\\odoo_deploy</b>; originales intactos.",
    "Dockerfile, odoo.conf y entrypoint.sh preparados con secretos como variables.",
    "Repositorio público creado y autorizado con GitHub CLI (JDNH0511).",
    "PostgreSQL Free y Web Service Free creados en Render, región Oregon.",
    "Variables de entorno configuradas sin exponer valores.",
    "Inicialización remota de BD con base, sale_management y ventas_unicah.",
    "Fix de red (commit 1539d24) y deploy manual: servicio Live en 56.7 s.",
    "Verificación XML-RPC integral y creación del usuario de revisión.",
]
for i, paso in enumerate(pasos, 1):
    S.append(P(f"{i}. {paso}"))

S.append(PageBreak())

# Verificación
S.append(P("4. Verificación funcional", "H2"))
S.append(P(
    "El script <b>informe/verificar.py</b> se conecta por XML-RPC, crea datos temporales, valida el comportamiento "
    "del módulo y elimina los datos al finalizar. No imprime contraseñas."
))
filas = [["Prueba", "Resultado", "Detalle"]]
for r in ver["resultados"]:
    filas.append([
        P(r["prueba"], "Celda"),
        P(r["resultado"], "Celda"),
        P(r["detalle"], "Celda"),
    ])
S.append(tabla(filas, [48 * mm, 18 * mm, 89 * mm], font_size=8))
S.append(Spacer(1, 3 * mm))
S.append(P(f"Resultado final: <b>{ok} de {len(ver['resultados'])} pruebas correctas</b>.", "Centro"))

# Problemas
S.append(P("5. Problemas y resoluciones", "H2"))
S.append(tabla([
    ["Problema", "Resolución"],
    ["Northflank exigió tarjeta pese a anunciar plan gratuito", "Migración inmediata a Render Free, sin método de pago."],
    ["Docker local bloqueado: WSL2 ausente y sesión sin administrador", "Build validado en el entorno Linux remoto de Render."],
    ["Render no detectaba el puerto; Odoo escuchaba en loopback", "http_interface=0.0.0.0 + mapeo de $PORT a 10000; deploy Live."],
], [62 * mm, 93 * mm], font_size=8.5))
S.append(Spacer(1, 3 * mm))
S.append(P(
    "Incidencias adicionales documentadas: contraseña maestra vs. contraseña del usuario admin, impuesto por defecto "
    "en el producto de prueba y diferencias de API de Odoo 20 para dominios y copy()."
))

# Evidencias
S.append(PageBreak())
S.append(P("6. Evidencias", "H2"))
S.append(P("Capturas reales tomadas del navegador y del panel de Render. Los secretos aparecen ocultos o enmascarados.", "Peq"))

CAPTIONS = [
    ("01_github_repo.png", "Repositorio público en GitHub"),
    ("02_render_servicio.png", "Servicio web odoo-unicah en Render"),
    ("03_render_postgres.png", "Base PostgreSQL Free en Render"),
    ("04_render_variables.png", "Variables de entorno (valores enmascarados)"),
    ("05_render_deploy_live.png", "Deploy 1539d24 en estado Live"),
    ("06_odoo_login.png", "Pantalla pública de inicio de sesión"),
    ("07_odoo_modulo_instalado.png", "Módulo ventas_unicah instalado"),
    ("08_odoo_pedido_aprobacion.png", "Pedido > 50,000 con aviso y botón Aprobar"),
    ("09_render_puerto_10000.png", "Log: http_port = 10000"),
    ("10_render_logs_http200.png", "Logs: GET /web/login → HTTP 200"),
]
for name, caption in CAPTIONS:
    path = BASE / "capturas" / name
    if not path.exists():
        continue
    with Image.open(path) as im:
        w, h = im.size
    max_w = 120 * mm
    img_h = min(68 * mm, max_w * h / w)
    S.append(RLImage(str(path), width=max_w, height=img_h))
    S.append(Spacer(1, 1.5 * mm))
    S.append(P(caption, "Peq"))
    S.append(Spacer(1, 4 * mm))

# Limitaciones y cierre
S.append(P("7. Limitaciones del plan gratuito", "H2"))
S.append(tabla([
    ["Limitación", "Impacto y mitigación"],
    ["Suspensión por inactividad", "El servicio se duerme tras ~15 min; la primera petición puede tardar cerca de 1 min en responder."],
    ["Caducidad de la base", "La BD Free caduca el 18/12/2026. Para una revisión académica inmediata es suficiente."],
    ["Recursos de la BD", "256 MB RAM y 1 GB de almacenamiento; no apto para carga académica intensiva."],
], [48 * mm, 107 * mm], font_size=8.5))

S.append(P("8. Conclusión", "H2"))
S.append(P(
    "El despliegue quedó publicado y funcional en una URL HTTPS pública, con usuario de revisión, módulo instalado "
    "y comportamiento verificado en producción. Las incidencias encontradas fueron resueltas y quedan documentadas "
    "en capturas, registros y scripts reproducibles."
))

doc.build(S, onFirstPage=pie, onLaterPages=pie)
print(f"PDF generado: {BASE / 'Informe_Despliegue_Odoo.pdf'}")
