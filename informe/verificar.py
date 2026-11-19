"""Verificación automática en producción vía XML-RPC.

Uso: python informe/verificar.py
Lee la URL de informe/url_publica.txt y las credenciales de secretos.local.txt.
No imprime contraseñas.
"""
from pathlib import Path
import json
import urllib.request
import xmlrpc.client

BASE = Path(__file__).resolve().parents[1]
URL = (BASE / "informe" / "url_publica.txt").read_text(encoding="utf-8").strip().rstrip("/")
secrets = dict(
    line.strip().split("=", 1)
    for line in (BASE / "secretos.local.txt").read_text(encoding="utf-8").splitlines()
    if "=" in line and not line.startswith("#")
)

results = []


def check(name, fn):
    try:
        ok, detail = fn()
        results.append((name, "OK" if ok else "FALLO", detail))
    except Exception as exc:
        results.append((name, "ERROR", f"{type(exc).__name__}: {exc}"))


def rpc(path):
    return xmlrpc.client.ServerProxy(f"{URL}{path}", allow_none=True)


common = rpc("/xmlrpc/2/common")
models = rpc("/xmlrpc/2/object")
version = common.version()
DB = secrets.get("DB_NAME", "odoo_prod")
ADMIN_PASS = secrets.get("ODOO_ADMIN_PASSWD", "admin")
uid = common.authenticate(DB, "admin", "admin", {})


def ejecutar(modelo, metodo, *args, **kwargs):
    return models.execute_kw(DB, uid, "admin", modelo, metodo, list(args), kwargs)


check("Login público", lambda: (
    urllib.request.urlopen(URL + "/web/login", timeout=30).status == 200,
    "HTTP 200 en /web/login",
))
check("Módulo instalado", lambda: (
    bool(ejecutar("ir.module.module", "search", [["name", "=", "ventas_unicah"], ["state", "=", "installed"]])),
    "ventas_unicah en estado installed",
))

# Se completará con el resto de pruebas tras el despliegue real.
(BASE / "informe" / "verificacion.md").write_text(
    "# Verificación automática en producción\n\n"
    f"URL: {URL}\n versión: {json.dumps(version)}\n\n"
    "| Prueba | Resultado | Detalle |\n|---|---|---|\n"
    + "".join(f"| {n} | {r} | {d} |\n" for n, r, d in results),
    encoding="utf-8",
)
print("Verificación escrita en informe/verificacion.md")
