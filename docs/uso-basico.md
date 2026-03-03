# Uso Básico

## Sintaxis del Comando

```bash
ics-sync [OPTIONS]
```

## Opciones Disponibles

| Opción | Descripción | Default |
|--------|-------------|--------|
| `--config PATH` | Ruta al archivo de configuración | `config.json` |
| `--dry-run` | Simular sin hacer cambios | `false` |
| `--verbose` | Logs detallados (nivel DEBUG) | `false` |
| `--help` | Mostrar ayuda | |

---

## Ejemplos de Uso

### 1. Sincronización Normal

```bash
ics-sync --config config.json
```

Salida:
```
2026-03-03 10:30:00 [INFO] Connecting to CalDAV at https://midrive.myds.me:5001/caldav/Alex/ as 'Alex'
2026-03-03 10:30:01 [INFO] CalDAV connection OK
2026-03-03 10:30:01 [INFO] [Fórmula 1] Fetching ICS from https://www.f1calendar.com/...
2026-03-03 10:30:02 [INFO] [Fórmula 1] Found 24 event(s) to sync
2026-03-03 10:30:02 [INFO] [Fórmula 1] 20 event(s) already in CalDAV
2026-03-03 10:30:05 [INFO] [Fórmula 1] Done — created=4, updated=0, skipped=20, deleted=0, errors=0
2026-03-03 10:30:05 [INFO] Sync complete — total: created=4, updated=0, skipped=20, deleted=0, errors=0
```

### 2. Modo Dry-Run (Simulación)

Útil para probar sin modificar nada:

```bash
ics-sync --config config.json --dry-run
```

Salida:
```
2026-03-03 10:35:00 [INFO] [Fórmula 1] Fetching ICS from https://www.f1calendar.com/...
2026-03-03 10:35:01 [INFO] [Fórmula 1] Found 24 event(s) to sync
2026-03-03 10:35:01 [INFO] [Fórmula 1] DRY RUN — no changes will be made
```

### 3. Modo Verbose (Debug)

Para ver logs detallados:

```bash
ics-sync --config config.json --verbose
```

Salida:
```
2026-03-03 10:40:00 [DEBUG] Found calendar: 'Fórmula 1'
2026-03-03 10:40:01 [DEBUG] [Fórmula 1] Created UID=event-123 + 2 override(s)
2026-03-03 10:40:02 [DEBUG] [Fórmula 1] Updated UID=event-456 (3 component(s))
2026-03-03 10:40:03 [DEBUG] [Fórmula 1] Skipped incompatible override RECURRENCE-ID=...
```

### 4. Archivo de Configuración Personalizado

```bash
ics-sync --config /ruta/personalizada/mi-config.json
```

---

## Ejecución Manual vs. Programada

### Ejecución Manual

Para probar o sincronizar bajo demanda:

```bash
cd /ruta/al/proyecto
ics-sync --config config.json
```

### Ejecución Programada (Cron)

Para sincronización automática:

```bash
# Editar crontab
crontab -e

# Sincronizar cada hora
0 * * * * cd /ruta/al/proyecto && /usr/bin/python3 -m ics_sync.cli --config config.json >> /var/log/ics-sync.log 2>&1

# Sincronizar cada 30 minutos
*/30 * * * * cd /ruta/al/proyecto && /usr/bin/python3 -m ics_sync.cli --config config.json >> /var/log/ics-sync.log 2>&1

# Sincronizar diariamente a las 6:00 AM
0 6 * * * cd /ruta/al/proyecto && /usr/bin/python3 -m ics_sync.cli --config config.json >> /var/log/ics-sync.log 2>&1
```

---

## Interpretación de Resultados

### Estadísticas de Sincronización

```
created=4, updated=2, skipped=18, deleted=1, errors=0
```

| Estadística | Significado |
|-------------|-------------|
| `created` | Eventos nuevos creados en CalDAV |
| `updated` | Eventos existentes actualizados |
| `skipped` | Eventos sin cambios (LAST-MODIFIED igual) |
| `deleted` | Eventos eliminados (solo si `delete_removed_events: true`) |
| `errors` | Errores durante la sincronización |

### Códigos de Salida

| Código | Significado |
|--------|-------------|
| `0` | Sincronización exitosa |
| `1` | Uno o más errores durante la sincronización |

---

## Casos de Uso Comunes

### Sincronización de Google Calendar

```bash
# 1. Exportar URL ICS desde Google Calendar
# 2. Añadir a config.json
# 3. Ejecutar sync
ics-sync --config config.json
```

### Sincronización de Fórmula 1

```bash
# URL pública de F1Calendar.com
ics-sync --config config.json
```

### Sincronización de Calendario Universitario

```bash
# URL ICS proporcionada por la universidad
ics-sync --config config.json
```

---

## Solución Rápida de Problemas

### Error: "CalDAV connection failed"

```bash
# Verificar conectividad
ping tu-nas.ejemplo.com

# Verificar puerto
nc -zv tu-nas.ejemplo.com 5001

# Verificar credenciales en config.json
```

### Error: "Failed to fetch ICS"

```bash
# Verificar URL ICS en navegador
curl -I "https://example.com/calendar.ics"

# Probar con --verbose para más detalles
ics-sync --config config.json --verbose
```

### Warning: "Calendar not found — creating via CalDAV fallback"

Esto indica que el calendario no existe. El script intentará crearlo automáticamente.

**Nota:** Los calendarios creados vía CalDAV pueden ser invisibles en DSM. Ver [Calendarios Invisibles](calendarios-invisibles.md).

---

## Siguiente Paso

➡️ [Sincronización Automática](sincronizacion-automatica.md)
