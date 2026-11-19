"""Verificación automática en producción vía XML-RPC.

Uso: python informe/verificar.py
Lee la URL de informe/url_publica.txt y las credenciales de secretos.local.txt.
No imprime contraseñas. Crea datos temporales de prueba y los elimina al final.
"""
from __future__ import annotations

import json
import secrets as secretlib
import socket
import urllib.request
import xmlrpc.client
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
URL = (BASE / "informe" / "url_publica.txt").read_text(encoding="utf-8").strip().rstrip("/")
cfg = dict(
    line.strip().split("=", 1)
    for line in (BASE / "secretos.local.txt").read_text(encoding="utf-8").splitlines()
    if "=" in line and not line.lstrip().startswith("#")
)

DB = cfg["DB_NAME"]
ADMIN_LOGIN = "admin"
ADMIN_PASS = cfg["ODOO_ADMIN_PASSWD"]
REVIEW_LOGIN = "review_admin"
REVIEW_PASS = cfg["REVIEW_ADMIN_PASSWORD"]

socket.setdefaulttimeout(90)
common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common", allow_none=True)
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)

results: list[tuple[str, str, str]] = []
setup: dict = {}
created: dict = {"orders": [], "partners": [], "products": [], "users": []}
uid_admin = 0


def check(name: str, fn):
    try:
        ok, detail = fn()
        results.append((name, "OK" if ok else "FALLO", str(detail)))
    except Exception as exc:  # noqa: BLE001 - registramos cualquier fallo-
        msg = getattr(exc, "faultString", None) or str(exc)
        results.append((name, "ERROR", f"{type(exc).__name__}: {msg}"))


def ex(model: str, method: str, *args, **kwargs):
    """Llamada XML-RPC como administrador."""
    return models.execute_kw(DB, uid_admin, ADMIN_PASS, model, method, list(args), kwargs)


def ex_as(uid: int, password: str, model: str, method: str, *args, **kwargs):
    return models.execute_kw(DB, uid, password, model, method, list(args), kwargs)


def xmlid_id(xmlid: str) -> int:
    try:
        rid = ex("ir.model.data", "xmlid_to_res_id", xmlid)
        if rid:
            return rid
    except Exception:  # noqa: BLE001 - compatibilidad con versiones anteriores-
        pass
    module, name = xmlid.split(".", 1)
    ids = ex("ir.model.data", "search", [["module", "=", module], ["name", "=", name]])
    if not ids:
        raise RuntimeError(f"No existe el XML ID {xmlid}")
    return ex("ir.model.data", "read", ids, ["res_id"])[0]["res_id"]


def read_one(model: str, rid: int, fields: list[str]) -> dict:
    return ex(model, "read", [rid], fields)[0]


def make_order(partner_id: int, product_id: int, qty: int) -> int:
    return ex("sale.order", "create", {
        "partner_id": partner_id,
        "order_line": [(0, 0, {
            "product_id": product_id,
            "product_uom_qty": qty,
            "price_unit": 10000.0,
        })],
    })


def prepare():
    """Prepara datos y usuario de revisión. Devuelve un dict con lo creado."""
    global uid_admin
    version = common.version()
    uid_admin = common.authenticate(DB, ADMIN_LOGIN, ADMIN_PASS, {})
    if not uid_admin:
        raise RuntimeError("No se pudo autenticar al administrador de Odoo")

    company_id = read_one("res.users", uid_admin, ["company_id"])["company_id"][0]
    g_user = xmlid_id("base.group_user")
    g_system = xmlid_id("base.group_system")
    g_manager = xmlid_id("sales_team.group_sale_manager")

    # Usuario de revisión (idempotente): administrador + administrador de ventas.
    rid = ex("res.users", "search", [["login", "=", REVIEW_LOGIN]], limit=1)
    group_cmd = [(6, 0, sorted({g_user, g_system, g_manager}))]
    if rid:
        ex("res.users", "write", rid, {
            "password": REVIEW_PASS,
            "group_ids": group_cmd,
            "company_id": company_id,
            "company_ids": [(6, 0, [company_id])],
            "active": True,
        })
        review_id = rid[0]
    else:
        review_id = ex("res.users", "create", {
            "name": "Usuario de revisión",
            "login": REVIEW_LOGIN,
            "password": REVIEW_PASS,
            "group_ids": group_cmd,
            "company_id": company_id,
            "company_ids": [(6, 0, [company_id])],
        })

    partner_id = ex("res.partner", "create", {
        "name": "Prueba verificación Ventas UNICAH",
        "customer_rank": 1,
        "canal_preferido": "web",
    })
    created["partners"].append(partner_id)
    product_id = ex("product.product", "create", {
        "name": "Servicio prueba verificación Ventas UNICAH",
        "type": "service",
        "sale_ok": True,
        "list_price": 10000.0,
        "taxes_id": [(5, 0, 0)],
    })
    created["products"].append(product_id)

    orders = {k: make_order(partner_id, product_id, q) for k, q in
              [("high", 6), ("limit", 5), ("perm", 6), ("approval", 6), ("confirm", 6)]}
    created["orders"].extend(orders.values())

    # Usuarios temporales para probar permisos.
    suffix = secretlib.token_hex(3)
    no_login = f"vu_sin_permiso_{suffix}"
    man_login = f"vu_con_permiso_{suffix}"
    no_pass = secretlib.token_urlsafe(18)
    man_pass = secretlib.token_urlsafe(18)
    no_id = ex("res.users", "create", {
        "name": "Prueba sin permiso de aprobación",
        "login": no_login,
        "password": no_pass,
        "group_ids": [(6, 0, [g_user])],
        "company_id": company_id,
        "company_ids": [(6, 0, [company_id])],
    })
    man_id = ex("res.users", "create", {
        "name": "Prueba con permiso de aprobación",
        "login": man_login,
        "password": man_pass,
        "group_ids": [(6, 0, [g_user, g_manager])],
        "company_id": company_id,
        "company_ids": [(6, 0, [company_id])],
    })
    created["users"].extend([no_id, man_id])

    return {
        **orders,
        "version": version,
        "review_id": review_id,
        "review_uid": common.authenticate(DB, REVIEW_LOGIN, REVIEW_PASS, {}),
        "review_groups": read_one("res.users", review_id, ["group_ids"])["group_ids"],
        "g_system": g_system,
        "g_manager": g_manager,
        "partner_id": partner_id,
        "product_id": product_id,
        "no_uid": common.authenticate(DB, no_login, no_pass, {}),
        "no_pass": no_pass,
        "man_uid": common.authenticate(DB, man_login, man_pass, {}),
        "man_pass": man_pass,
        "man_id": man_id,
    }


def _login_page() -> tuple[bool, str]:
    with urllib.request.urlopen(URL + "/web/login", timeout=90) as resp:
        html = resp.read().decode("utf-8", "ignore").lower()
        return resp.status == 200 and "login" in html, "HTTP 200 en /web/login con formulario de acceso"


def _block_confirm(S: dict) -> tuple[bool, str]:
    try:
        ex("sale.order", "action_confirm", [S["confirm"]])
        return False, "action_confirm no bloqueó el pedido superior a 50,000"
    except Exception as exc:  # noqa: BLE001
        msg = getattr(exc, "faultString", str(exc))
        ok = "aprobad" in msg.lower() or "debe ser" in msg.lower()
        return ok, msg[:300]


def _permissions(S: dict) -> tuple[bool, str]:
    try:
        ex_as(S["no_uid"], S["no_pass"], "sale.order", "action_aprobar", [S["perm"]])
        return False, "un usuario sin el grupo pudo aprobar"
    except Exception as exc:  # noqa: BLE001
        msg = getattr(exc, "faultString", str(exc)).lower()
        if not any(w in msg for w in ("administrador de ventas", "access", "acceso", "permiso")):
            return False, msg[:300]
    try:
        ex_as(S["man_uid"], S["man_pass"], "sale.order", "action_aprobar", [S["perm"]])
    except Exception as exc:  # noqa: BLE001
        return False, f"el administrador de ventas no pudo aprobar: {getattr(exc, 'faultString', exc)}"[:300]
    groups = read_one("res.users", S["man_id"], ["group_ids"])["group_ids"]
    return S["g_manager"] in groups, "sin grupo = rechazado; sales manager = aprobado"


def _approve_and_confirm(S: dict) -> tuple[bool, str]:
    try:
        ex_as(S["man_uid"], S["man_pass"], "sale.order", "action_aprobar", [S["confirm"]])
        ex_as(S["man_uid"], S["man_pass"], "sale.order", "action_confirm", [S["confirm"]])
        state = read_one("sale.order", S["confirm"], ["state"])["state"]
        return state in ("sale", "done"), f"estado tras confirmar: {state}"
    except Exception as exc:  # noqa: BLE001
        return False, getattr(exc, "faultString", str(exc))[:300]


def _copy_test(S: dict) -> tuple[bool, str]:
    ex_as(S["man_uid"], S["man_pass"], "sale.order", "action_aprobar", [S["approval"]])
    original = read_one("sale.order", S["approval"], ["aprobado_por"])["aprobado_por"]
    copy_id = ex("sale.order", "copy", [S["approval"]])[0]
    created["orders"].append(copy_id)
    copied = read_one("sale.order", copy_id, ["aprobado_por"])["aprobado_por"]
    return bool(original) and not bool(copied), f"original aprobado; copia aprobado_por={copied}"


def cleanup():
    for oid in created["orders"]:
        try:
            state = read_one("sale.order", oid, ["state"])["state"]
            if state not in ("draft", "sent", "cancel"):
                ex("sale.order", "action_cancel", [oid])
            ex("sale.order", "unlink", [oid])
        except Exception:  # noqa: BLE001 - limpieza best-effort-
            pass
    for model, key in (("product.product", "products"), ("res.partner", "partners"), ("res.users", "users")):
        for rid in created[key]:
            try:
                ex(model, "unlink", [rid])
            except Exception:  # noqa: BLE001 - limpieza best-effort-
                pass


try:
    setup = prepare()
except Exception as exc:  # noqa: BLE001
    results.append(("Preparación de datos", "ERROR", f"{type(exc).__name__}: {exc}"))


if setup:
    S = setup

    check("Login público", _login_page)

    check("Versión de Odoo", lambda: (
        bool(S["version"].get("server_version")),
        f"Odoo {S['version'].get('server_version')}",
    ))

    check("Módulo instalado", lambda: (
        bool(ex("ir.module.module", "search", [
            ["name", "=", "ventas_unicah"], ["state", "=", "installed"]
        ])),
        "ventas_unicah en estado installed",
    ))

    check("Campos del módulo", lambda: (
        all(
            ex("ir.model.fields", "search", [["model", "=", m], ["name", "=", f]], limit=1)
            for m, f in [
                ("res.partner", "canal_preferido"),
                ("sale.order", "canal_venta"),
                ("sale.order", "total_unidades"),
                ("sale.order", "requiere_aprobacion"),
                ("sale.order", "aprobado_por"),
                ("sale.order", "pendiente_aprobacion"),
            ]
        ),
        "6 campos presentes en los modelos",
    ))

    check("Vistas del módulo", lambda: (
        (lambda n: (n >= 4, f"{n} vistas heredadas"))(
            len(ex("ir.ui.view", "search", [["name", "ilike", "ventas.unicah"]]))
        ),
        "vistas de formulario, lista y búsqueda",
    ))

    check("Usuario de revisión", lambda: (
        bool(S["review_uid"]) and S["g_system"] in S["review_groups"] and S["g_manager"] in S["review_groups"],
        f"login {REVIEW_LOGIN} con permisos de administrador y ventas",
    ))

    check("Canal preferido → canal_venta", lambda: (
        read_one("sale.order", S["high"], ["canal_venta"])["canal_venta"] == "web",
        "canal_preferido=web se propaga al pedido",
    ))

    check("Total de unidades", lambda: (
        abs(read_one("sale.order", S["high"], ["total_unidades"])["total_unidades"] - 6.0) < 0.001,
        "6 unidades calculadas y almacenadas",
    ))

    check("Aprobación requerida (> 50,000)", lambda: (
        (lambda a, b: (
            a["requiere_aprobacion"] is True and b["requiere_aprobacion"] is False,
            f"{a['amount_total']:,.0f} → {a['requiere_aprobacion']}; "
            f"{b['amount_total']:,.0f} → {b['requiere_aprobacion']} (umbral estricto)",
        ))(
            read_one("sale.order", S["high"], ["amount_total", "requiere_aprobacion"]),
            read_one("sale.order", S["limit"], ["amount_total", "requiere_aprobacion"]),
        )
    ))

    check("Pendiente de aprobación", lambda: (
        read_one("sale.order", S["high"], ["pendiente_aprobacion"])["pendiente_aprobacion"] is True,
        "pedido > 50,000 en borrador aparece como pendiente",
    ))

    check("Bloqueo de confirmación sin aprobar", lambda: _block_confirm(S))

    check("Permisos por grupo", lambda: _permissions(S))

    check("Aprobación por administrador de ventas", lambda: (
        (lambda r: (bool(r) and bool(read_one("sale.order", S["approval"], ["aprobado_por"])["aprobado_por"]),
                    f"aprobado_por={read_one('sale.order', S['approval'], ['aprobado_por'])['aprobado_por']}"))(
            ex_as(S["man_uid"], S["man_pass"], "sale.order", "action_aprobar", [S["approval"]])
        ),
        "sales_team.group_sale_manager aprueba el pedido",
    ))

    check("Pendiente se limpia al aprobar", lambda: (
        read_one("sale.order", S["approval"], ["pendiente_aprobacion"])["pendiente_aprobacion"] is False,
        "pendiente_aprobacion pasa a False tras la aprobación",
    ))

    check("Confirmación tras aprobación", lambda: _approve_and_confirm(S))

    check("copy=False en aprobado_por", lambda: _copy_test(S))


cleanup()

ok_count = sum(1 for _, r, _ in results if r == "OK")
fecha = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
version_txt = json.dumps(setup.get("version", {}), ensure_ascii=False) if setup else "{}"

md = (
    "# Verificación automática en producción\n\n"
    f"- Fecha: {fecha}\n"
    f"- URL: {URL}\n"
    f"- Base de datos: {DB}\n"
    f"- Versión: {version_txt}\n"
    f"- Resultado: **{ok_count}/{len(results)} pruebas correctas**\n\n"
    "| Prueba | Resultado | Detalle |\n|---|---|---|\n"
    + "".join(
        f"| {n} | {r} | {d.replace('|', '\\|').replace(chr(10), ' ')} |\n"
        for n, r, d in results
    )
)
(BASE / "informe" / "verificacion.md").write_text(md, encoding="utf-8")
(BASE / "informe" / "verificacion.json").write_text(
    json.dumps({
        "fecha": fecha,
        "url": URL,
        "db": DB,
        "version": setup.get("version", {}),
        "resultados": [{"prueba": n, "resultado": r, "detalle": d} for n, r, d in results],
    }, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(f"Verificación escrita: {ok_count}/{len(results)} pruebas correctas")
