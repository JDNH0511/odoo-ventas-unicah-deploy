FROM odoo:20.0

USER root

# Módulo propio (copia; el original en C:\Users\joseh\custom_addons no se modifica)
COPY ventas_unicah/ /mnt/extra-addons/ventas_unicah/

# Configuración de producción y script de arranque
COPY odoo.conf /etc/odoo/odoo.conf
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh && chmod 666 /etc/odoo/odoo.conf && mkdir -p /var/lib/odoo && chown odoo:odoo /var/lib/odoo

USER odoo

# El servicio escucha en 8070 (o en $PORT si la plataforma lo impone)
EXPOSE 8070

ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo", "-c", "/etc/odoo/odoo.conf"]
