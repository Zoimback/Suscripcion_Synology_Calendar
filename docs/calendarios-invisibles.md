# Calendarios Invisibles en Synology Calendar

## ¿Qué son los Calendarios Invisibles?

Los **calendarios invisibles** son calendarios que existen en el servidor CalDAV de Synology pero no aparecen en la interfaz web de Synology Calendar. Estos calendarios:

- ✅ Son accesibles vía protocolo CalDAV
- ✅ Pueden sincronizarse con clientes externos (Outlook, Thunderbird, etc.)
- ❌ **NO** aparecen en la interfaz web de DSM
- ❌ **NO** se pueden gestionar desde la aplicación Calendar de Synology

## Causa del Problema

Este problema ocurre cuando se crean calendarios usando el método `caldav.make_calendar()` de la biblioteca CalDAV en lugar de usar la API oficial de Synology DSM (`SYNO.Cal.Cal`).

### Diferencias clave:

| Método de Creación | Slug/ID | Visible en DSM | Ejemplo |
|-------------------|---------|----------------|---------||
| **DSM API** (`SYNO.Cal.Cal`) | ID corto aleatorio | ✅ Visible | `iqzwmbc`, `hfhnpin`, `dbwzvs` |
| **CalDAV** (`caldav.make_calendar()`) | UUID largo | ❌ Invisible | `58c1664f-...`, `23a64972-...` |

### Arquitectura Interna

Synology Calendar almacena los calendarios en una base de datos **PostgreSQL** (no en el sistema de archivos):

- Base de datos: `calendar`
- Tablas principales:
  - `collection` - Metadatos de calendarios
  - `caldav_data` - Datos de eventos CalDAV
  - `syno_cal_obj` - Objetos de calendario (eventos, tareas, etc.)

Los calendarios creados vía CalDAV se registran en la tabla `collection` pero el sistema DSM no los reconoce porque no fueron creados a través de su API interna.

---

## Diagnóstico: Detectar Calendarios Invisibles

### Método 1: Script Python con CalDAV

```python
import caldav
import json
from collections import Counter

# Cargar configuración
with open('config.json') as f:
    cfg = json.load(f)

c = cfg['caldav']
client = caldav.DAVClient(
    url=c['url'], 
    username=c['username'], 
    password=c['password'], 
    ssl_verify_cert=False
)

# Obtener todos los calendarios
cals = client.principal().calendars()

# Detectar duplicados (señal de calendarios invisibles)
counts = Counter(cal.name for cal in cals)
duplicates = [name for name, cnt in counts.items() if cnt > 1]

print(f'Total calendarios en CalDAV: {len(cals)}')
print(f'Duplicados encontrados: {duplicates}')

# Mostrar detalles
for cal in sorted(cals, key=lambda x: x.name or ''):
    url = cal.url.rstrip('/').split('/')[-1]
    is_uuid = len(url) > 20 and '-' in url
    tipo = '🚫 INVISIBLE (UUID)' if is_uuid else '✅ Visible (ID corto)'
    print(f'{cal.name:<30} {url:<40} {tipo}')
```

### Método 2: Consulta Directa a PostgreSQL

```sql
-- Conectarse por SSH
ssh usuario@nas.ejemplo.com
sudo -u postgres psql -d calendar

-- Ver todos los calendarios
SELECT collection_id, url, displayname 
FROM collection 
ORDER BY displayname;

-- Los calendarios invisibles tienen URLs con UUIDs largos:
--   /Alex/A7579712-9DC0-4C61-BE2E-ED3663DF00CA/  ← INVISIBLE
--   /Alex/iqzwmbc/                               ← VISIBLE
```

---

## Solución: Eliminar Calendarios Invisibles

### ⚠️ ADVERTENCIA

**Haz un backup completo antes de proceder** con estos comandos. La eliminación es irreversible.

```bash
# Backup de la base de datos
ssh usuario@nas.ejemplo.com
sudo -u postgres pg_dump calendar > /volume1/backup/calendar_backup_$(date +%Y%m%d).sql
```

### Pasos de Eliminación

#### 1. Identificar los Collection IDs a eliminar

```sql
ssh usuario@nas.ejemplo.com
sudo -u postgres psql -d calendar

-- Listar calendarios con URL larga (UUID)
SELECT collection_id, url, displayname 
FROM collection 
WHERE LENGTH(url) > 50 
ORDER BY displayname;

-- Ejemplo de salida:
-- collection_id |                        url                         | displayname
-- --------------+----------------------------------------------------+------------------
--          1054 | /Alex/A7579712-9DC0-4C61-BE2E-ED3663DF00CA/       | Better F1 Calendar
--          1053 | /Alex/041C201C-1AF8-4F41-96D2-EEDB09AB6C5C/       | Universidad Carlemany
--          1055 | /Alex/014A524E-C04E-4901-B7EA-6F1929431B52/       | Trabajo BBVA
```

#### 2. Eliminar de la base de datos

```sql
-- Eliminar calendarios invisibles (ajustar los IDs según tu caso)
DELETE FROM collection 
WHERE collection_id IN (1054, 1053, 1055);

-- Salir de PostgreSQL
\q
```

**Nota:** Las claves foráneas tienen `ON DELETE CASCADE`, por lo que al eliminar de `collection`, automáticamente se limpian:
- `caldav_data` (eventos CalDAV)
- `syno_cal_obj` (objetos de calendario)
- Otras tablas relacionadas

#### 3. Verificar la limpieza

```python
# Ejecutar script de verificación nuevamente
import caldav, json
with open('config.json') as f: cfg = json.load(f)
c = cfg['caldav']
client = caldav.DAVClient(url=c['url'], username=c['username'], password=c['password'], ssl_verify_cert=False)
cals = client.principal().calendars()
print(f'✓ Total calendarios después de limpieza: {len(cals)}')
```

---

## Prevención: Evitar Calendarios Invisibles en el Futuro

### ✅ Método Correcto: Usar DSM API Primero

Este proyecto (`ics-sync`) **ya implementa la prevención automáticamente**:

```python
# El módulo ics_sync.dsm_client crea calendarios vía DSM API
from ics_sync.dsm_client import DSMSession, dsm_ensure_calendars

# Esto crea calendarios VISIBLES con ID corto
dsm = DSMSession(dsm_url, username, password, verify_ssl, log)
dsm_ensure_calendars(dsm, calendar_names, log)
```

Cuando ejecutas `ics-sync`, automáticamente:

1. 🔑 Conecta a DSM API primero
2. ✅ Crea calendarios faltantes con IDs cortos (visibles)
3. 📦 Luego usa CalDAV solo para sincronizar eventos

### ❌ Método Incorrecto: Crear con CalDAV Directamente

```python
# ¡NO HACER ESTO!
import caldav
client = caldav.DAVClient(url=..., username=..., password=...)
principal = client.principal()

# Esto crea un calendario INVISIBLE con UUID
calendar = principal.make_calendar(name="Mi Calendario")  # ← EVITAR
```

### Regla de Oro

> **Siempre crea calendarios usando la DSM API (`SYNO.Cal.Cal`) primero.**  
> Luego usa CalDAV solo para gestionar eventos dentro de esos calendarios.

---

## Troubleshooting

### Error 117 al intentar eliminar calendarios

**Síntoma:** Al usar `SYNO.Cal.Cal` para eliminar, aparece error 117.

**Causa:** Los calendarios UUID no están registrados en la API de DSM.

**Solución:** Usar eliminación directa en PostgreSQL (ver sección de Solución).

### CalDAV DELETE devuelve 405 Method Not Allowed

**Síntoma:** `cal.delete()` falla con error 405.

**Causa:** Synology no permite eliminar colecciones de calendario vía CalDAV.

**Solución:** Usar PostgreSQL o DSM API (solo funciona para calendarios visibles).

### Calendario reaparece después de eliminar

**Síntoma:** El calendario eliminado vuelve a aparecer después de un tiempo.

**Causa:** Puede haber un proceso de sincronización automática recreándolo.

**Solución:** 
1. Verificar `config.json` y eliminar la fuente ICS
2. Verificar tareas programadas en DSM
3. Reiniciar el servicio Calendar: `sudo synoservice --restart pkgctl-Calendar`

---

## Resumen

| Aspecto | Detalle |
|---------|---------||
| **Problema** | Calendarios visibles en CalDAV pero invisibles en DSM Calendar |
| **Causa** | Creación vía `caldav.make_calendar()` en lugar de DSM API |
| **Detección** | Script Python con CalDAV o consulta PostgreSQL |
| **Solución** | `DELETE FROM collection WHERE collection_id IN (...)` |
| **Prevención** | `ics-sync` previene automáticamente usando DSM API |

---

**Última actualización:** 3 de marzo de 2026  
**Mantenedor:** [@Zoimback](https://github.com/Zoimback)
