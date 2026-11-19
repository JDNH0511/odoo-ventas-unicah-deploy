#!/bin/bash
set -e

CONFIG=/etc/odoo/odoo.conf

# 1) Renderizar odoo.conf desde variables de entorno (sin secretos en el repo)
python3 - "$CONFIG" <<'PY'
import os, re, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    content = f.read()
for key, value in os.environ.items():
    content = content.replace("${" + key + "}", value)
if os.environ.get("PORT"):
    content = re.sub(r"^http_port\s*=.*$", "http_port = " + os.environ["PORT"], content, flags=re.M)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("odoo.conf renderizado; http_port =", re.search(r"^http_port\s*=\s*(\S+)", content, re.M).group(1))
PY

# 2) Esperar a PostgreSQL
python3 - <<'PY'
import os, time, sys
import psycopg2
params = dict(
    host=os.environ.get("DB_HOST", "db"),
    port=int(os.environ.get("DB_PORT", "5432")),
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    dbname=os.environ.get("DB_NAME", "postgres"),
)
for attempt in range(60):
    try:
        conn = psycopg2.connect(connect_timeout=3, **params)
        conn.close()
        print("PostgreSQL listo:", params["host"], params["port"])
        sys.exit(0)
    except Exception as exc:
        print("Esperando PostgreSQL (%s/60): %s" % (attempt + 1, exc.__class__.__name__), flush=True)
        time.sleep(2)
raise SystemExit("PostgreSQL no respondió tras 120 s")
PY

# 3) Inicializar la BD la primera vez con los módulos requeridos
python3 - <<'PY'
import os, subprocess, sys
import psycopg2
params = dict(
    host=os.environ["DB_HOST"], port=int(os.environ.get("DB_PORT", "5432")),
    user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
    dbname=os.environ["DB_NAME"],
)
conn = psycopg2.connect(**params)
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'ir_module_module'")
inicializada = cur.fetchone() is not None
cur.close(); conn.close()
if not inicializada:
    print("Inicializando BD con -i base,sale_management,ventas_unicah ...", flush=True)
    cmd = ["odoo", "-c", "/etc/odoo/odoo.conf", "-d", os.environ["DB_NAME"],
           "-i", "base,sale_management,ventas_unicah", "--stop-after-init", "--without-demo=all"]
    rc = subprocess.call(cmd)
    if rc != 0:
        raise SystemExit("Falló la inicialización (código %s)" % rc)
else:
    print("BD ya inicializada; omitiendo -i", flush=True)
PY

# 3.5) Regenerar assets en cada arranque (el disco de Render Free es efímero)
python3 - <<'PY'
import os
import psycopg2
params = dict(
    host=os.environ["DB_HOST"], port=int(os.environ.get("DB_PORT", "5432")),
    user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
    dbname=os.environ["DB_NAME"],
)
conn = psycopg2.connect(**params)
conn.autocommit = True
cur = conn.cursor()
cur.execute("DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%'")
print("Assets eliminados para regeneracion en este arranque", flush=True)
cur.close()
conn.close()
PY

# 4) Arrancar Odoo
exec odoo -c /etc/odoo/odoo.conf
