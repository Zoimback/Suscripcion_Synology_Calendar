# API Reference

## Módulos Públicos

### `ics_sync.cli`

Punto de entrada para línea de comandos.

#### `main(argv=None)`

Ejecuta el pipeline completo de sincronización.

**Parámetros:**
- `argv` (list[str] | None): Lista de argumentos CLI. Usa `sys.argv` si es `None`.

**Retorna:** `None`

**Ejemplo:**

```python
from ics_sync.cli import main

main(['--config', 'my-config.json', '--dry-run'])
```

---

### `ics_sync.sync`

Lógica central de sincronización.

#### `sync_source(source, principal, *, dry_run, log, verify_ssl=True)`

Sincroniza una fuente ICS a su calendario CalDAV destino.

**Parámetros:**
- `source` (dict): Diccionario de fuente desde `config.json`
  - `url` (str): URL pública del ICS
  - `calendar_name` (str): Nombre del calendario destino
  - `delete_removed_events` (bool, opcional): Eliminar eventos obsoletos
- `principal`: Principal CalDAV autenticado (de `DAVClient`)
- `dry_run` (bool): Si `True`, no hace cambios en CalDAV
- `log` (logging.Logger): Instancia del logger
- `verify_ssl` (bool): Verificar certificados SSL

**Retorna:** `dict[str, int]`

Estadísticas con keys:
- `created`: Eventos nuevos creados
- `updated`: Eventos actualizados
- `deleted`: Eventos eliminados
- `errors`: Errores encontrados
- `skipped`: Eventos sin cambios

**Ejemplo:**

```python
from caldav import DAVClient
from ics_sync.sync import sync_source
import logging

log = logging.getLogger(__name__)
client = DAVClient(url='...', username='...', password='...')
principal = client.principal()

source = {
    'url': 'https://example.com/calendar.ics',
    'calendar_name': 'Mi Calendario',
    'delete_removed_events': True
}

stats = sync_source(source, principal, dry_run=False, log=log)
print(f"Creados: {stats['created']}, Actualizados: {stats['updated']}")
```

---

### `ics_sync.fetcher`

Descarga de fuentes ICS con reintentos.

#### `fetch_ics(url, *, timeout=30, verify_ssl=True, retries=3)`

Descarga y parsea un calendario ICS desde una URL.

**Parámetros:**
- `url` (str): URL HTTP/HTTPS del feed ICS
- `timeout` (int): Timeout por intento en segundos (default: 30)
- `verify_ssl` (bool): Verificar certificados TLS (default: True)
- `retries` (int): Número máximo de intentos (default: 3)

**Retorna:** `icalendar.Calendar`

**Lanza:** La última excepción después de agotar reintentos

**Ejemplo:**

```python
from ics_sync.fetcher import fetch_ics

cal = fetch_ics(
    'https://www.f1calendar.com/download/f1-calendar.ics',
    timeout=60,
    verify_ssl=True,
    retries=5
)

for component in cal.walk():
    if component.name == "VEVENT":
        print(component.get('SUMMARY'))
```

---

### `ics_sync.grouping`

Agrupación de eventos recurrentes.

#### `group_vevents(source_cal)`

Parsea un calendario y retorna eventos agrupados por UID.

**Parámetros:**
- `source_cal` (icalendar.Calendar): Calendario ICS parseado

**Retorna:** `dict[str, list]`

Mapeo `{uid: [master, override…]}`

**Reglas:**
- Eventos standalone usan su UID completo
- Eventos recurrentes (RRULE) + overrides comparten el base UID
- Múltiples RRULE masters: se mantiene el con DTSTART más reciente
- Grupos huérfanos (solo overrides) se descartan

**Ejemplo:**

```python
from icalendar import Calendar
from ics_sync.grouping import group_vevents

with open('calendar.ics', 'rb') as f:
    cal = Calendar.from_ical(f.read())

groups = group_vevents(cal)
for uid, vevents in groups.items():
    print(f"UID: {uid}, Componentes: {len(vevents)}")
```

#### `base_uid(uid)`

Elimina el sufijo de recurrencia estilo Google.

**Parámetros:**
- `uid` (str): UID original

**Retorna:** `str` - UID base sin sufijo

**Ejemplo:**

```python
from ics_sync.grouping import base_uid

uid = "event123_R20260303T120000Z@google.com"
base = base_uid(uid)
print(base)  # "event123@google.com"
```

#### `build_ics_for_group(source_cal, vevents)`

Crea un VCALENDAR con uno o más VEVENTs, preservando VTIMEZONEs.

**Parámetros:**
- `source_cal` (icalendar.Calendar): Calendario fuente original
- `vevents` (list): Lista de componentes VEVENT

**Retorna:** `bytes` - ICS serializado

**Ejemplo:**

```python
from ics_sync.grouping import build_ics_for_group

ics_bytes = build_ics_for_group(source_cal, [master, override1, override2])
with open('output.ics', 'wb') as f:
    f.write(ics_bytes)
```

---

### `ics_sync.caldav_helpers`

Utilidades para CalDAV.

#### `get_or_create_calendar(principal, calendar_name, log)`

Retorna el calendario CalDAV por nombre, prefiriendo el de ID corto (visible).

**Parámetros:**
- `principal`: Principal CalDAV
- `calendar_name` (str): Nombre del calendario
- `log` (logging.Logger): Logger

**Retorna:** Objeto calendario CalDAV

**Comportamiento:**
- Si no existe: crea vía CalDAV (puede ser invisible)
- Si hay duplicados: prefiere ID corto (visible) sobre UUID

**Ejemplo:**

```python
from caldav import DAVClient
from ics_sync.caldav_helpers import get_or_create_calendar
import logging

log = logging.getLogger(__name__)
client = DAVClient(url='...', username='...', password='...')
principal = client.principal()

cal = get_or_create_calendar(principal, 'Fórmula 1', log)
print(cal.url)
```

#### `get_existing_uids(caldav_calendar)`

Retorna mapeo de UIDs a eventos CalDAV.

**Parámetros:**
- `caldav_calendar`: Calendario CalDAV

**Retorna:** `dict[str, object]` - Mapeo `{UID: caldav_event}`

**Ejemplo:**

```python
from ics_sync.caldav_helpers import get_existing_uids

existing = get_existing_uids(cal)
print(f"Eventos existentes: {len(existing)}")
for uid in existing:
    print(f"  - {uid}")
```

---

### `ics_sync.dsm_client`

Cliente HTTP para DSM API.

#### `class DSMSession`

Sesión wrapper para Synology DSM HTTP API.

**Constructor:**

```python
DSMSession(base_url, username, password, verify_ssl, log)
```

**Parámetros:**
- `base_url` (str): URL base de DSM (ej: `https://nas.ejemplo.com:5001`)
- `username` (str): Usuario DSM
- `password` (str): Contraseña (o app password si 2FA habilitado)
- `verify_ssl` (bool): Verificar certificado SSL
- `log` (logging.Logger): Logger

**Métodos:**

##### `list_calendars() -> list[dict]`

Retorna lista cruda de diccionarios de calendarios desde DSM API.

##### `existing_calendar_names() -> set[str]`

Retorna set de nombres de calendarios existentes.

##### `create_calendar(name, color='#0099cc') -> bool`

Crea un calendario vía DSM API.

**Parámetros:**
- `name` (str): Nombre del calendario
- `color` (str): Color hex (default: azul)

**Retorna:** `bool` - True si tuvo éxito

##### `logout() -> None`

Cierra la sesión DSM.

**Ejemplo:**

```python
from ics_sync.dsm_client import DSMSession
import logging

log = logging.getLogger(__name__)
dsm = DSMSession(
    base_url='https://nas.ejemplo.com:5001',
    username='alex',
    password='mi_password',
    verify_ssl=False,
    log=log
)

dsm.create_calendar('Nuevo Calendario', color='#e5604f')
print(dsm.existing_calendar_names())
dsm.logout()
```

#### `dsm_ensure_calendars(dsm, calendar_names, log)`

Crea calendarios faltantes vía DSM API.

**Parámetros:**
- `dsm` (DSMSession): Sesión DSM autenticada
- `calendar_names` (list[str]): Lista de nombres de calendarios
- `log` (logging.Logger): Logger

**Retorna:** `None`

**Ejemplo:**

```python
from ics_sync.dsm_client import DSMSession, dsm_ensure_calendars

dsm = DSMSession(...)
dsm_ensure_calendars(dsm, ['Fórmula 1', 'Universidad', 'Trabajo'], log)
```

---

### `ics_sync.config`

Carga de configuración.

#### `load_config(path='config.json')`

Carga y retorna el diccionario JSON de configuración.

**Parámetros:**
- `path` (str | Path): Ruta al archivo config.json

**Retorna:** `dict`

**Ejemplo:**

```python
from ics_sync.config import load_config

cfg = load_config('mi-config.json')
print(cfg['caldav']['url'])
```

---

### `ics_sync.logging_`

Configuración de logging.

#### `setup_logging(verbose, log_file=None)`

Configura logging root y retorna logger `ics-sync`.

**Parámetros:**
- `verbose` (bool): Habilitar nivel DEBUG
- `log_file` (str | None): Ruta opcional a archivo de log

**Retorna:** `logging.Logger`

**Ejemplo:**

```python
from ics_sync.logging_ import setup_logging

log = setup_logging(verbose=True, log_file='/var/log/ics-sync.log')
log.info('Iniciando sincronización')
```

---

## Uso Programatic

### Ejemplo Completo

```python
import logging
from caldav import DAVClient
from ics_sync.config import load_config
from ics_sync.sync import sync_source
from ics_sync.dsm_client import DSMSession, dsm_ensure_calendars
from ics_sync.logging_ import setup_logging

# 1. Configurar logging
log = setup_logging(verbose=True, log_file='sync.log')

# 2. Cargar configuración
cfg = load_config('config.json')

# 3. Conectar CalDAV
caldav_cfg = cfg['caldav']
client = DAVClient(
    url=caldav_cfg['url'],
    username=caldav_cfg['username'],
    password=caldav_cfg['password'],
    ssl_verify_cert=caldav_cfg.get('verify_ssl', True)
)
principal = client.principal()

# 4. Pre-crear calendarios vía DSM (previene calendarios invisibles)
try:
    dsm = DSMSession(
        base_url='https://nas.ejemplo.com:5001',
        username=caldav_cfg['username'],
        password=caldav_cfg['password'],
        verify_ssl=caldav_cfg.get('verify_ssl', True),
        log=log
    )
    calendar_names = [s['calendar_name'] for s in cfg['sources']]
    dsm_ensure_calendars(dsm, calendar_names, log)
except Exception as e:
    log.warning(f"DSM pre-flight error: {e}")

# 5. Sincronizar cada fuente
for source in cfg['sources']:
    stats = sync_source(
        source,
        principal,
        dry_run=False,
        log=log,
        verify_ssl=caldav_cfg.get('verify_ssl', True)
    )
    print(f"{source['calendar_name']}: {stats}")
```

---

## Constantes

### `ics_sync.sync`

- `_MAX_ATTEMPTS` = 3: Reintentos máximos por operación
- `_RETRY_DELAY` = 5: Segundos entre reintentos

### `ics_sync.dsm_client`

- `DSMSession.DSM_COLORS`: Lista de 10 colores hex para calendarios

---

## Siguiente Paso

➡️ [Arquitectura](arquitectura.md)
