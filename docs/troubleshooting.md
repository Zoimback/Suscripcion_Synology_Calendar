# Troubleshooting

## Problemas de Conexión

### Error: "CalDAV connection failed"

**Síntoma:**
```
[ERROR] CalDAV connection failed: [Errno 111] Connection refused
```

**Causas y Soluciones:**

1. **NAS apagado o inaccesible**
   ```bash
   # Verificar conectividad
   ping nas.ejemplo.com
   ```

2. **Puerto incorrecto**
   ```bash
   # Verificar puerto (default: 5001 para HTTPS)
   nc -zv nas.ejemplo.com 5001
   ```

3. **CalDAV no habilitado**
   - DSM → Control Panel → Application Portal → **Habilitar CalDAV**

4. **Firewall bloqueando**
   - DSM → Control Panel → Security → Firewall → Permitir puerto 5001

### Error: "SSL: CERTIFICATE_VERIFY_FAILED"

**Síntoma:**
```
[ERROR] SSL: CERTIFICATE_VERIFY_FAILED
```

**Solución:**

En `config.json`, desactiva verificación SSL:

```json
{
  "caldav": {
    "verify_ssl": false
  }
}
```

**Nota:** Solo usa `verify_ssl: false` con certificados autofirmados de confianza.

---

## Problemas de Autenticación

### Error: "401 Unauthorized"

**Síntoma:**
```
[ERROR] CalDAV connection failed: 401 Unauthorized
```

**Causas y Soluciones:**

1. **Credenciales incorrectas**
   - Verifica `username` y `password` en `config.json`
   - Prueba login manual en DSM

2. **2FA habilitado**
   - Crea una **Contraseña de Aplicación**:
     - DSM → Cuenta → Seguridad → Contraseñas de aplicaciones
     - Usa esa contraseña en `config.json`

3. **Usuario sin permisos de Calendar**
   - DSM → Control Panel → User → Permisos → Habilitar Calendar

### Error: "DSM 2FA is enabled. Use an app-specific password"

**Solución:**

1. DSM → Cuenta → Seguridad → **Contraseñas de aplicaciones**
2. Crear → Nombre: `ICS Sync` → Permisos: Calendar
3. Copiar la contraseña generada
4. Usar en `config.json`:

```json
{
  "password": "xxxx-xxxx-xxxx-xxxx"
}
```

---

## Problemas con Fuentes ICS

### Error: "Failed to fetch ICS"

**Síntoma:**
```
[ERROR] [Mi Calendario] Failed to fetch ICS: HTTPSConnectionPool...
```

**Causas y Soluciones:**

1. **URL incorrecta o expirada**
   ```bash
   # Probar URL en navegador o curl
   curl -I "https://example.com/calendar.ics"
   ```

2. **Fuente ICS caída temporalmente**
   - Esperar y reintentar
   - El script reintenta automáticamente 3 veces

3. **Timeout de red**
   - Aumentar timeout en el código (ver [API Reference](api-reference.md))

### Error: "ValueError: cal: not a valid icalendar file"

**Síntoma:**
```
[ERROR] ValueError: cal: not a valid icalendar file
```

**Causa:** El archivo ICS descargado está corrupto o no es válido.

**Solución:**

1. Verifica la URL manualmente:
   ```bash
   curl "https://example.com/calendar.ics" -o test.ics
   cat test.ics
   ```

2. Valida el ICS en [icalendar.org/validator](https://icalendar.org/validator.html)

3. Contacta al proveedor del ICS

---

## Problemas con Eventos

### Warning: "Skipped incompatible override"

**Síntoma:**
```
[DEBUG] [Mi Calendario] Skipped incompatible override RECURRENCE-ID=...
```

**Causa:** Synology rechaza ciertas combinaciones de eventos recurrentes.

**Solución:** Esto es normal. El script:
- Guarda el evento maestro (RRULE)
- Intenta agregar excepciones una por una
- Omite las incompatibles sin fallar

### Eventos no se actualizan

**Síntoma:** Los eventos no cambian después de sincronizar.

**Causas y Soluciones:**

1. **LAST-MODIFIED no cambió en el ICS**
   - Verificar que la fuente ICS actualiza `LAST-MODIFIED`
   - El script compara timestamps para evitar writes innecesarios

2. **Error silencioso**
   - Ejecutar con `--verbose` para ver detalles:
     ```bash
     ics-sync --config config.json --verbose
     ```

### Eventos eliminados no desaparecen

**Síntoma:** Eventos eliminados del ICS siguen en Synology.

**Causa:** `delete_removed_events` está en `false`.

**Solución:**

En `config.json`:

```json
{
  "sources": [
    {
      "delete_removed_events": true  // ← Cambiar a true
    }
  ]
}
```

**⚠️ Advertencia:** Esto eliminará eventos que ya no existen en el ICS.

---

## Problemas con Calendarios

### Warning: "Calendar not found — creating via CalDAV fallback"

**Síntoma:**
```
[WARNING] Calendar 'Mi Calendario' not found — creating via CalDAV fallback (may be invisible in UI)
```

**Causa:** El calendario no existe en DSM y la DSM API falló.

**Solución:**

1. Crear el calendario manualmente en DSM:
   - Synology Calendar → **New Calendar** → Nombre: `Mi Calendario`

2. O aceptar el warning (el calendario funcionará pero puede ser invisible, ver [Calendarios Invisibles](calendarios-invisibles.md))

### Calendarios duplicados

**Síntoma:** Aparecen 2 calendarios con el mismo nombre.

**Causa:** Un calendario creado vía CalDAV (UUID invisible) + uno creado vía DSM (visible).

**Solución:** Ver [Calendarios Invisibles](calendarios-invisibles.md#solucion-eliminar-calendarios-invisibles)

---

## Problemas de Rendimiento

### Sincronización muy lenta

**Síntoma:** El script tarda varios minutos.

**Causas y Soluciones:**

1. **Muchos eventos**
   - Normal: ~100 eventos = 10-30 segundos
   - Optimización: El script ya usa:
     - Comparación de `LAST-MODIFIED` (skip si igual)
     - Reintentos con backoff exponencial

2. **Red lenta**
   - Verificar latencia al NAS:
     ```bash
     ping -c 10 nas.ejemplo.com
     ```

3. **NAS sobrecargado**
   - Verificar CPU/RAM en DSM Resource Monitor

### Errores de timeout

**Síntoma:**
```
[ERROR] requests.exceptions.ReadTimeout: HTTPSConnectionPool
```

**Solución:**

Modificar timeout en `ics_sync/fetcher.py`:

```python
def fetch_ics(
    url: str,
    *,
    timeout: int = 60,  # ← Aumentar de 30 a 60
    ...
):
```

---

## Problemas en Synology NAS

### Error: "python3: command not found"

**Solución:**

```bash
# Instalar Python 3 desde Package Center
# O usar ruta completa
/volume1/@appstore/py3k/usr/local/bin/python3 -m ics_sync.cli
```

### Error: "No module named 'caldav'"

**Solución:**

```bash
cd /volume1/scripts/ics-sync
/volume1/@appstore/py3k/usr/local/bin/python3 -m pip install -r requirements.txt
```

### Task Scheduler no ejecuta

**Verificación:**

1. DSM → Task Scheduler → [Tu tarea] → **Action → View Result**
2. Revisar logs:
   ```bash
   tail -f /volume1/logs/ics-sync.log
   ```

**Solución común:**

Usar rutas absolutas en el script:

```bash
#!/bin/bash
cd /volume1/scripts/ics-sync
/volume1/@appstore/py3k/usr/local/bin/python3 -m ics_sync.cli --config /volume1/scripts/ics-sync/config.json >> /volume1/logs/ics-sync.log 2>&1
```

---

## Problemas con Logs

### Logs no se generan

**Verificación:**

```bash
# Verificar permisos
ls -la /var/log/ics-sync.log

# Verificar directorio existe
mkdir -p /var/log
```

**Solución:**

En `config.json`, usa ruta con permisos de escritura:

```json
{
  "log_file": "./sync.log"  // Ruta relativa al proyecto
}
```

### Logs demasiado grandes

**Solución: Rotar logs**

```bash
# Linux: Crear /etc/logrotate.d/ics-sync
/var/log/ics-sync.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
```

---

## Depuración Avanzada

### Modo Verbose

```bash
ics-sync --config config.json --verbose
```

### Modo Dry-Run

```bash
ics-sync --config config.json --dry-run --verbose
```

### Ejecutar Python Interactivo

```python
import json
from caldav import DAVClient

with open('config.json') as f:
    cfg = json.load(f)

c = cfg['caldav']
client = DAVClient(url=c['url'], username=c['username'], password=c['password'])
principal = client.principal()
cals = principal.calendars()
print(f'Calendarios encontrados: {len(cals)}')
for cal in cals:
    print(f'  - {cal.name} ({cal.url})')
```

---

## Obtener Ayuda

### Reportar un Error

Abre un [Issue en GitHub](https://github.com/Zoimback/Suscripcion_Synology_Calendar/issues) con:

1. **Versión de Python**: `python --version`
2. **Versión de DSM**: DSM → Control Panel → Info Center
3. **Logs con `--verbose`**:
   ```bash
   ics-sync --config config.json --verbose > debug.log 2>&1
   ```
4. **Configuración anonimizada**:
   ```json
   {
     "caldav": {
       "url": "https://NAS_REDACTED:5001/caldav/USER_REDACTED/",
       "username": "REDACTED",
       "password": "REDACTED"
     },
     "sources": [
       {
         "url": "https://REDACTED/calendar.ics",
         "calendar_name": "Example Calendar"
       }
     ]
   }
   ```

### Recursos Adicionales

- [Documentación CalDAV](https://github.com/python-caldav/caldav)
- [RFC 5545 (iCalendar)](https://tools.ietf.org/html/rfc5545)
- [Synology Calendar API](https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/Calendar/All/enu/Synology_Calendar_API_Guide_enu.pdf)

---

## Siguiente Paso

➡️ [Calendarios Invisibles](calendarios-invisibles.md)
