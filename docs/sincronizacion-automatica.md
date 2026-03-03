# Sincronización Automática

## Cron (Linux/Mac)

### Configurar Cron

```bash
# Editar crontab del usuario
crontab -e
```

### Ejemplos de Tareas Cron

```bash
# Sincronizar cada hora
0 * * * * cd /ruta/al/proyecto && /usr/bin/python3 -m ics_sync.cli --config config.json >> /var/log/ics-sync.log 2>&1

# Sincronizar cada 30 minutos
*/30 * * * * cd /ruta/al/proyecto && /usr/bin/python3 -m ics_sync.cli --config config.json >> /var/log/ics-sync.log 2>&1

# Sincronizar cada 15 minutos
*/15 * * * * cd /ruta/al/proyecto && /usr/bin/python3 -m ics_sync.cli --config config.json >> /var/log/ics-sync.log 2>&1

# Sincronizar diariamente a las 6:00 AM
0 6 * * * cd /ruta/al/proyecto && /usr/bin/python3 -m ics_sync.cli --config config.json >> /var/log/ics-sync.log 2>&1

# Sincronizar de lunes a viernes a las 8:00 AM
0 8 * * 1-5 cd /ruta/al/proyecto && /usr/bin/python3 -m ics_sync.cli --config config.json >> /var/log/ics-sync.log 2>&1
```

### Sintaxis Cron

```
* * * * * comando
│ │ │ │ │
│ │ │ │ └─── Día de la semana (0-7, 0=Domingo)
│ │ │ └───── Mes (1-12)
│ │ └─────── Día del mes (1-31)
│ └───────── Hora (0-23)
└─────────── Minuto (0-59)
```

### Verificar Tareas Cron

```bash
# Listar tareas del usuario actual
crontab -l

# Ver logs del sistema (Debian/Ubuntu)
sudo tail -f /var/log/syslog | grep CRON

# Ver logs de ics-sync
tail -f /var/log/ics-sync.log
```

---

## Task Scheduler (Windows)

### Crear Tarea Programada

1. Abrir **Programador de tareas** (Task Scheduler)
2. **Acción → Crear tarea básica**
3. Configurar:

**General:**
- Nombre: `ICS Sync to Synology`
- Descripción: `Sincroniza calendarios ICS a Synology Calendar`
- Ejecutar con los privilegios más altos: ☐

**Desencadenadores:**
- Nuevo → **Repetir cada**: `1 hora`
- Duración: `Indefinidamente`

**Acciones:**
- Programa/script: `C:\Python310\python.exe`
- Argumentos: `-m ics_sync.cli --config C:\ruta\config.json`
- Iniciar en: `C:\ruta\al\proyecto`

### Script Batch (Alternativa)

Crear `sync.bat`:

```batch
@echo off
cd /d C:\ruta\al\proyecto
C:\Python310\python.exe -m ics_sync.cli --config config.json >> sync.log 2>&1
```

Luego programar `sync.bat` en Task Scheduler.

---

## Tarea Programada en Synology NAS

Ver [Instalación en Synology](instalacion-synology.md#tarea-programada) para instrucciones completas.

### Resumen

1. **Control Panel → Task Scheduler**
2. **Create → Scheduled Task → User-defined script**
3. Configurar ejecución cada hora
4. Script:

```bash
cd /volume1/scripts/ics-sync
/volume1/@appstore/py3k/usr/local/bin/python3 -m ics_sync.cli --config config.json >> /volume1/logs/ics-sync.log 2>&1
```

---

## Systemd Service (Linux)

### Crear Service Unit

Crear `/etc/systemd/system/ics-sync.service`:

```ini
[Unit]
Description=ICS to Synology CalDAV Sync
After=network.target

[Service]
Type=oneshot
User=tu_usuario
WorkingDirectory=/ruta/al/proyecto
ExecStart=/usr/bin/python3 -m ics_sync.cli --config config.json
StandardOutput=append:/var/log/ics-sync.log
StandardError=append:/var/log/ics-sync.log

[Install]
WantedBy=multi-user.target
```

### Crear Timer

Crear `/etc/systemd/system/ics-sync.timer`:

```ini
[Unit]
Description=Run ICS Sync every hour

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Persistent=true

[Install]
WantedBy=timers.target
```

### Habilitar y Arrancar

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar timer
sudo systemctl enable ics-sync.timer

# Iniciar timer
sudo systemctl start ics-sync.timer

# Verificar estado
sudo systemctl status ics-sync.timer

# Ver logs
sudo journalctl -u ics-sync.service -f
```

---

## Docker + Cron

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install -e .

# Instalar cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Añadir tarea cron
RUN echo "0 * * * * cd /app && python3 -m ics_sync.cli --config config.json >> /var/log/ics-sync.log 2>&1" | crontab -

CMD ["cron", "-f"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  ics-sync:
    build: .
    volumes:
      - ./config.json:/app/config.json:ro
      - ./logs:/var/log
    restart: unless-stopped
```

---

## Monitorización

### Ver Logs en Tiempo Real

```bash
# Linux/Mac
tail -f /var/log/ics-sync.log

# Windows (PowerShell)
Get-Content sync.log -Wait -Tail 20

# Synology
ssh usuario@nas.ejemplo.com
tail -f /volume1/logs/ics-sync.log
```

### Alertas por Email (Linux)

Configurar `mailx` o `sendmail` y modificar cron:

```bash
0 * * * * cd /ruta && python3 -m ics_sync.cli --config config.json 2>&1 | grep -i error && echo "Sync failed!" | mail -s "ICS Sync Error" tu@email.com
```

### Healthchecks.io (Opcional)

Monitorizar ejecuciones:

```bash
# Añadir a cron
0 * * * * cd /ruta && python3 -m ics_sync.cli --config config.json && curl -fsS -m 10 --retry 5 https://hc-ping.com/tu-uuid
```

---

## Recomendaciones

| Frecuencia | Caso de Uso |
|-----------|-------------|
| Cada 15 min | Calendarios dinámicos (eventos deportivos en vivo) |
| Cada 1 hora | Calendarios regulares (Google, universidad, trabajo) |
| Cada 6 horas | Calendarios estáticos (temporadas deportivas) |
| Diaria | Calendarios de bajo cambio (vacaciones, recordatorios) |

---

## Siguiente Paso

➡️ [Troubleshooting](troubleshooting.md)
