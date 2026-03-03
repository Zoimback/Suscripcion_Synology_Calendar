# Arquitectura

## Visión General

```
┌─────────────────┐
│  Fuentes ICS   │
│ (Google, F1,  │
│ Universidad)  │
└────────┬────────┘
         │ HTTP GET
         │ (fetch_ics)
         ↓
┌────────┴────────┐
│  ics_sync.py   │
│                │
│  ┌───────────┐ │
│  │ grouping  │ │  Agrupar eventos recurrentes
│  └────┬──────┘ │  Normalizar UIDs de Google
│       │          │
│  ┌────┴──────┐ │
│  │   sync    │ │  Upsert/Delete lógica
│  └────┬──────┘ │  Comparación LAST-MODIFIED
└────────┴────────┘
         │
         ├──── DSM API (SYNO.Cal.Cal)
         │      │ Crear calendarios (visibles)
         │      ↓
         │    ┌────────────────┐
         │    │ Synology DSM  │
         │    │ (ID cortos)   │
         │    └───────┬────────┘
         │           │
         └─ CalDAV  │
           (eventos) │
                     ↓
          ┌─────────────────┐
          │ PostgreSQL DB  │
          │ (collection,   │
          │  syno_cal_obj) │
          └───────┬─────────┘
                 │
                 ↓
      ┌───────────────────┐
      │ Clientes CalDAV  │
      │ (iOS, Android,  │
      │  Outlook, etc.)  │
      └───────────────────┘
```

---

## Estructura del Proyecto

```
.
├── ics_sync/                 # Paquete principal
│   ├── __init__.py          # API pública
│   ├── cli.py               # Punto de entrada CLI
│   ├── config.py            # Carga config.json
│   ├── logging_.py          # Setup de logging
│   ├── fetcher.py           # Descarga ICS con reintentos
│   ├── grouping.py          # Agrupación de eventos recurrentes
│   ├── sync.py              # Motor de sincronización
│   ├── caldav_helpers.py    # Utilidades CalDAV
│   └── dsm_client.py        # Cliente DSM HTTP API
│
├── tests/                   # Tests unitarios
│   ├── unit/
│   │   ├── test_grouping.py
│   │   └── test_sync_helpers.py
│   └── integration/
│       └── test_integration.py
│
├── docs/                    # Documentación
│   ├── instalacion.md
│   ├── configuracion.md
│   ├── uso-basico.md
│   └── ...
│
├── config.json.example      # Plantilla de configuración
├── requirements.txt         # Dependencias Python
├── pyproject.toml           # Configuración del proyecto
├── README.md
└── LICENSE
```

---

## Flujo de Ejecución
### 1. Inicialización
```python
# cli.py: main()
└─ Parsear argumentos CLI (argparse)
└─ Cargar config.json (config.load_config)
└─ Setup logging (logging_.setup_logging)
```

### 2. Conexión CalDAV

```python
# cli.py
└─ Conectar CalDAV (caldav.DAVClient)
└─ Obtener principal (client.principal())
```

### 3. Pre-flight DSM

```python
# cli.py
└─ DSMSession(base_url, username, password)
└─ dsm_ensure_calendars(dsm, calendar_names)
    ├─ Listar calendarios existentes
    └─ Crear faltantes vía SYNO.Cal.Cal
```

**Propósito:** Prevenir calendarios invisibles (UUID) creando con DSM API primero.

### 4. Sincronización por Fuente

```python
# cli.py: for source in config['sources']
└─ sync_source(source, principal, dry_run, log)
```

#### 4.1. Fetch ICS

```python
# sync.py: sync_source()
└─ fetch_ics(url, verify_ssl)
    ├─ HTTP GET con User-Agent
    ├─ Reintentos: 3 con backoff exponencial (2s, 4s)
    └─ icalendar.Calendar.from_ical(raw)
```

#### 4.2. Agrupar Eventos

```python
# sync.py
└─ group_vevents(source_cal)
    ├─ Iterar VEVENT components
    ├─ Normalizar Google UIDs (_R20260303T120000Z)
    ├─ Agrupar por base_uid:
    │   {uid: [master, override1, override2, ...]}
    ├─ Resolver múltiples masters (mantener último DTSTART)
    └─ Descartar grupos huérfanos (solo overrides)
```

#### 4.3. Obtener Calendario CalDAV

```python
# sync.py
└─ get_or_create_calendar(principal, calendar_name)
    ├─ Buscar por nombre (normalizado Unicode)
    ├─ Si hay duplicados: preferir ID corto (no UUID)
    └─ Si no existe: crear vía CalDAV (fallback)
```

#### 4.4. Obtener Eventos Existentes

```python
# sync.py
└─ get_existing_uids(caldav_cal)
    ├─ Iterar caldav_cal.events()
    └─ Retornar {UID: caldav_event}
```

#### 4.5. Upsert Eventos

```python
# sync.py: for uid, vevents in source_events.items()
└─ _upsert_group(uid, vevents, ...)
    ├─ build_ics_for_group(source_cal, vevents)
    │   ├─ Crear VCALENDAR nuevo
    │   ├─ Copiar VTIMEZONEs referenciados
    │   └─ Añadir VEVENTs
    │
    ├─ if UID existe en CalDAV:
    │   ├─ Comparar LAST-MODIFIED / DTSTART
    │   ├─ Si sin cambios: skip
    │   └─ _save_with_retry(event, ics_data)
    │       ├─ Intentar 3 veces
    │       └─ Si falla grupo: fallback incremental
    │
    └─ else (nuevo):
        ├─ obj_id = md5(uid)  # URL determinista
        └─ _put_with_retry(caldav_cal, ics_data, obj_id)
            ├─ Intentar 3 veces
            └─ Si falla grupo: fallback incremental
```

**Fallback incremental:**
1. Intentar guardar grupo completo
2. Si falla: guardar solo master
3. Añadir overrides uno por uno
4. Omitir overrides incompatibles

#### 4.6. Eliminar Eventos Obsoletos

```python
# sync.py: if delete_removed
└─ removed_uids = existing - source
└─ for uid in removed_uids:
    └─ existing_uids[uid].delete()  # con reintentos
```

### 5. Finalización
```python
# cli.py
└─ Agregar stats de todas las fuentes
└─ Log resumen final
└─ sys.exit(1 if errors else 0)
```

---

## Patrones de Diseño

### Reintentos con Backoff Exponencial

Todas las operaciones de red usan reintentos:

```python
for attempt in range(1, retries + 1):
    try:
        # operación
        return success
    except Exception as e:
        if attempt < retries:
            time.sleep(2 ** attempt)  # 2s, 4s, 8s
        else:
            raise e
```

### Comparación de Timestamps

Optimización: skip eventos sin cambios

```python
src_lastmod = master.get('LAST-MODIFIED') or master.get('DTSTAMP')
dst_lastmod = existing_master.get('LAST-MODIFIED') or ...

if src_lastmod <= dst_lastmod:
    return 'skipped'
```

**Excepción:** Google Calendar cambia DTSTART sin actualizar LAST-MODIFIED:

```python
if dtstart_changed:
    force_update = True
```

### Normalización Unicode

Comparación de nombres tolerante a locales:

```python
def _norm(s: str) -> str:
    return unicodedata.normalize("NFC", s or "").casefold()

if _norm(cal.name) == _norm(calendar_name):
    match = cal
```

---

## Manejo de Eventos Recurrentes

### Convenciones iCalendar

**Evento standalone:**
```ical
BEGIN:VEVENT
UID:event123
DTSTART:20260305
SUMMARY:Reunión
END:VEVENT
```

**Evento recurrente:**
```ical
BEGIN:VEVENT
UID:event456
RRULE:FREQ=WEEKLY;COUNT=10
DTSTART:20260301
SUMMARY:Clase Semanal
END:VEVENT
```

**Excepción de recurrencia:**
```ical
BEGIN:VEVENT
UID:event456
RECURRENCE-ID:20260308
DTSTART:20260309  ← Movido un día
SUMMARY:Clase Semanal (Reprogramada)
END:VEVENT
```

### Quirk de Google Calendar

Google exporta overrides con UID modificado:

```
UID original:   event456@google.com
UID override:   event456_R20260308T100000Z@google.com
                         ↑───────────────────────↑
                         sufijo _R<fecha>T<hora>
```

**Solución:** `base_uid()` elimina el sufijo:

```python
_GOOGLE_RECUR_RE = re.compile(r"_R\d{8}T\d{6}Z?(?=@|$)")

def base_uid(uid: str) -> str:
    return _GOOGLE_RECUR_RE.sub("", uid)
```

### Almacenamiento en CalDAV

**RFC 5545:** Master + overrides deben almacenarse como **un solo objeto CalDAV**.

```ical
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//SynologyICSSync//EN

BEGIN:VEVENT
UID:event456
RRULE:FREQ=WEEKLY;COUNT=10
DTSTART:20260301
SUMMARY:Clase Semanal
END:VEVENT

BEGIN:VEVENT
UID:event456
RECURRENCE-ID:20260308
DTSTART:20260309
SUMMARY:Clase Semanal (Reprogramada)
END:VEVENT

END:VCALENDAR
```

**Synology rechaza** overrides como objetos separados (error 500).

---

## Base de Datos Synology

### Esquema PostgreSQL

```sql
-- Tabla principal de calendarios
CREATE TABLE collection (
    collection_id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    displayname TEXT,
    color TEXT,
    owner_id INTEGER,
    ...
);

-- Eventos CalDAV
CREATE TABLE caldav_data (
    caldav_id SERIAL PRIMARY KEY,
    collection_id INTEGER REFERENCES collection(collection_id) ON DELETE CASCADE,
    url TEXT,
    data BYTEA,  -- ICS serializado
    ...
);

-- Objetos de calendario (eventos parseados)
CREATE TABLE syno_cal_obj (
    obj_id SERIAL PRIMARY KEY,
    collection_id INTEGER REFERENCES collection(collection_id) ON DELETE CASCADE,
    uid TEXT,
    summary TEXT,
    dtstart TIMESTAMP,
    dtend TIMESTAMP,
    rrule TEXT,
    ...
);
```

### Calendarios Visibles vs. Invisibles

| Creado vía | URL ejemplo | `collection.url` | Visible en DSM |
|------------|-------------|------------------|----------------|
| DSM API | `https://.../caldav/Alex/iqzwmbc/` | `/Alex/iqzwmbc/` | ✅ Sí |
| CalDAV | `https://.../caldav/Alex/58c1664f-.../` | `/Alex/58c1664f-.../` | ❌ No |

Ver [Calendarios Invisibles](calendarios-invisibles.md) para detalles.

---

## Dependencias

### Producción
| Paquete | Versión | Propósito |
|---------|---------|----------|
| `caldav` | ≥1.3.9 | Cliente CalDAV |
| `icalendar` | ≥5.0.12 | Parseo/generación ICS |
| `requests` | ≥2.31.0 | HTTP para DSM API e ICS fetch |

### Desarrollo

| Paquete | Propósito |
|---------|----------|
| `pytest` | Tests unitarios |
| `pytest-cov` | Cobertura de tests |
| `ruff` | Linter + formatter |
| `recurring-ical-events` | Tests de recurrencia |

---

## Rendimiento

### Optimizaciones Implementadas

1. **Skip eventos sin cambios**
   - Comparación `LAST-MODIFIED` antes de actualizar
   - Ahorra ~80% de writes en syncs sucesivos

2. **URL determinista para eventos**
   ```python
   obj_id = hashlib.md5(uid.encode()).hexdigest()
   ```
   - Evita duplicados en re-runs
   - Permite operaciones idempotentes

3. **Reintentos inteligentes**
   - Solo reintenta operaciones fallidas
   - Backoff exponencial reduce carga en servidor

4. **Fallback incremental para grupos**
   - Si grupo completo falla, intenta master + overrides uno por uno
   - Maximiza eventos guardados sin fallar todo

### Métricas Típicas

| Fuente | Eventos | Primera Sync | Syncs Subsecuentes |
|--------|---------|--------------|--------------------|
| Google Calendar (100 eventos) | 100 | ~20s | ~5s (skipped) |
| Fórmula 1 (24 eventos) | 24 | ~8s | ~3s |
| Universidad (50 eventos) | 50 | ~12s | ~4s |

---

## Siguiente Paso

➡️ Volver al [Índice de Documentación](README.md)
