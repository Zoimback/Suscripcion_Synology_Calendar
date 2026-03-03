# Synology Calendar ICS Sync

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Utilidad para sincronizar calendarios externos (feeds ICS/iCal) con **Synology Calendar** vía CalDAV. Diseñado específicamente para manejar las peculiaridades de Synology DSM y Google Calendar.

## ✨ Características

- ✅ **Sincronización automática** de múltiples feeds ICS
- ✅ **Creación inteligente de calendarios** usando DSM API (visibles en la interfaz web)
- ✅ **Soporte completo para eventos recurrentes** (RRULE + RECURRENCE-ID)
- ✅ **Manejo de quirks de Google Calendar** (UIDs modificados, masters duplicados)
- ✅ **Reintentos automáticos** con backoff exponencial
- ✅ **Modo dry-run** para pruebas seguras
- ✅ **Logging completo** a archivo y consola

## 🚀 Inicio Rápido

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/Zoimback/Suscripcion_Synology_Calendar.git
cd Suscripcion_Synology_Calendar

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Configuración

Copia el template y edita con tus datos:

```bash
cp skills/synology-calendar-ics-sync/references/config-template.json config.json
```

Ejemplo de `config.json`:

```json
{
  "caldav": {
    "url": "https://tu-nas.example.com:5001/caldav/Usuario/",
    "username": "tu_usuario",
    "password": "tu_contraseña",
    "verify_ssl": false
  },
  "sources": [
    {
      "calendar_name": "Fórmula 1",
      "url": "https://ejemplo.com/f1-calendar.ics",
      "delete_removed_events": true
    }
  ],
  "log_file": "/volume1/scripts/ics-sync/sync.log"
}
```

### Uso

```bash
# Sincronizar todos los calendarios
python sync_ics_to_caldav.py

# Modo dry-run (sin escribir cambios)
python sync_ics_to_caldav.py --dry-run

# Logging detallado
python sync_ics_to_caldav.py --verbose
```

## 📦 Estructura del Proyecto

```
.
├── ics_sync/              # Módulo principal
│   ├── cli.py            # Entry point CLI
│   ├── sync.py           # Motor de sincronización
│   ├── dsm_client.py     # Cliente DSM API
│   ├── caldav_helpers.py # Utilidades CalDAV
│   ├── grouping.py       # Agrupación de eventos recurrentes
│   ├── fetcher.py        # Descarga de feeds ICS
│   └── logging_.py       # Configuración de logging
├── tests/                 # Test suite
│   ├── unit/             # Tests unitarios
│   └── integration/      # Tests de integración
├── skills/                # Documentación de desarrollo
└── sync_ics_to_caldav.py # Script de compatibilidad
```

## 🔧 Características Avanzadas

### Eventos Recurrentes

Maneja correctamente:
- Eventos con `RRULE` (reglas de recurrencia)
- Excepciones (`RECURRENCE-ID`)
- Split series de Google Calendar
- Huérfanos (solo overrides sin master)

### DSM API vs CalDAV

⚠️ **Importante:** Los calendarios creados con `caldav.make_calendar()` son **invisibles** en Synology Calendar UI.

**Solución:** Este proyecto usa la DSM API primero para crear calendarios visibles:

```python
from ics_sync.dsm_client import DSMSession, dsm_ensure_calendars

dsm = DSMSession(base_url, username, password, verify_ssl, log)
dsm_ensure_calendars(dsm, ["Mi Calendario"], log)
```

Ver [wiki](https://github.com/Zoimback/Suscripcion_Synology_Calendar/wiki) para más detalles.

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=ics_sync --cov-report=html

# Tests específicos
pytest tests/unit/test_grouping.py -v
```

## 📋 Requisitos

- Python 3.10+
- Synology DSM 7.0+ con Calendar package
- CalDAV habilitado (Control Panel → Application Privileges)
- Red accesible (puerto 5001 por defecto)

### Dependencias Python

- `caldav>=1.3.9` - Cliente CalDAV
- `icalendar>=5.0.12` - Parser ICS/iCal
- `requests>=2.31.0` - HTTP client

## 🛠️ Herramientas Incluidas

### `delete_calendars.py`

Gestiona calendarios via DSM API:

```bash
# Listar calendarios
python delete_calendars.py --list

# Eliminar calendarios específicos
python delete_calendars.py --delete "Calendario 1" "Calendario 2"

# Dry-run
python delete_calendars.py --delete "Test" --dry-run
```

## 📚 Documentación

Ver [Wiki](https://github.com/Zoimback/Suscripcion_Synology_Calendar/wiki) para:

- Guía de instalación en Synology NAS
- Configuración de tareas programadas
- Troubleshooting de problemas comunes
- Arquitectura interna del proyecto
- Solución a calendarios invisibles

## 🐛 Problemas Conocidos

### Calendarios Invisibles

**Síntoma:** Calendarios aparecen en CalDAV pero no en DSM UI.

**Causa:** Creados con `caldav.make_calendar()` en lugar de DSM API.

**Solución:** Ver [Calendarios Invisibles](https://github.com/Zoimback/Suscripcion_Synology_Calendar/wiki/Calendarios-Invisibles) en la wiki.

### Error 117 al Eliminar

**Síntoma:** DSM API devuelve error 117 al eliminar calendarios.

**Causa:** Calendarios con UUID (no registrados en DSM).

**Solución:** Eliminación directa en PostgreSQL (ver wiki).

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add: AmazingFeature'`)
4. Push a la branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Estilo de Código

Usamos `ruff` para linting y formateo:

```bash
# Verificar estilo
ruff check ics_sync/

# Auto-format
ruff format ics_sync/
```

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- [python-caldav](https://github.com/python-caldav/caldav) - Cliente CalDAV
- [icalendar](https://github.com/collective/icalendar) - Parser RFC 5545
- Comunidad Synology por la documentación de DSM API

## 📞 Soporte

- 🐛 [Issues](https://github.com/Zoimback/Suscripcion_Synology_Calendar/issues)
- 💬 [Discussions](https://github.com/Zoimback/Suscripcion_Synology_Calendar/discussions)
- 📧 Email: rgalexmv@gmail.com

---

**⚠️ Nota de Seguridad:** Nunca subas tu `config.json` con credenciales reales al repositorio. Usa variables de entorno o archivos .gitignore.
