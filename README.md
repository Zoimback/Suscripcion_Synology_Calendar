# Synology Calendar ICS Sync

Sincroniza calendarios ICS externos (Google Calendar, F1, deportes, universidad, etc.) a **Synology Calendar** vía CalDAV.

## 🚀 Características

- ✅ Sincronización automática de múltiples fuentes ICS
- ✅ Soporte completo para eventos recurrentes (RRULE)
- ✅ Manejo de excepciones de recurrencia (RECURRENCE-ID)
- ✅ Eliminación automática de eventos obsoletos
- ✅ Reintentos automáticos con backoff exponencial
- ✅ Calendarios visibles en Synology Calendar UI y iOS/Android
- ✅ Compatible con cualquier servidor CalDAV

## 📋 Requisitos

- Python 3.10 o superior
- Synology NAS con Calendar package instalado
- CalDAV habilitado en DSM

## 🔧 Instalación

```bash
git clone https://github.com/Zoimback/Suscripcion_Synology_Calendar.git
cd Suscripcion_Synology_Calendar
pip install -e .
```

## ⚙️ Configuración

Crea un archivo `config.json`:

```json
{
  "caldav": {
    "url": "https://tu-nas.ejemplo.com:5001/caldav/usuario/",
    "username": "tu_usuario",
    "password": "tu_contraseña",
    "verify_ssl": true
  },
  "sources": [
    {
      "url": "https://example.com/calendar.ics",
      "calendar_name": "Mi Calendario",
      "delete_removed_events": true
    }
  ],
  "log_file": "sync.log"
}
```

### Autenticación 2FA

Si tienes 2FA habilitado en DSM:

1. Ve a **DSM → Cuenta → Seguridad → Contraseñas de aplicaciones**
2. Crea una contraseña específica para la aplicación
3. Usa esa contraseña en `config.json`

## 🚀 Uso

### Sincronización Manual

```bash
# Sincronización normal
ics-sync --config config.json

# Modo dry-run (sin modificar nada)
ics-sync --config config.json --dry-run

# Modo verbose (más logs)
ics-sync --config config.json --verbose
```

### Sincronización Automática (Cron)

Ejemplo para ejecutar cada hora:

```bash
# Editar crontab
crontab -e

# Añadir línea:
0 * * * * cd /ruta/al/proyecto && /usr/bin/python3 -m ics_sync.cli --config config.json
```

### Tarea Programada en Synology

Ver [Wiki: Instalación en Synology](https://github.com/Zoimback/Suscripcion_Synology_Calendar/wiki/Instalacion-Synology)

## 📖 Documentación

Visita la [Wiki](https://github.com/Zoimback/Suscripcion_Synology_Calendar/wiki) para documentación completa:

- [Instalación y Configuración](https://github.com/Zoimback/Suscripcion_Synology_Calendar/wiki/Instalacion)
- [Calendarios Invisibles](https://github.com/Zoimback/Suscripcion_Synology_Calendar/wiki/Calendarios-Invisibles)
- [Guía de Troubleshooting](https://github.com/Zoimback/Suscripcion_Synology_Calendar/wiki/Troubleshooting)
- [API Reference](https://github.com/Zoimback/Suscripcion_Synology_Calendar/wiki/API-Reference)

## 🛠️ Desarrollo

```bash
# Instalar con dependencias de desarrollo
pip install -e ".[dev]"

# Ejecutar tests
pytest

# Linting
ruff check .
ruff format .
```

## 📝 Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add: AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## ⚠️ Problemas Conocidos

- **Calendarios Invisibles**: Los calendarios creados vía `caldav.make_calendar()` no aparecen en DSM. Ver [Wiki: Calendarios Invisibles](https://github.com/Zoimback/Suscripcion_Synology_Calendar/wiki/Calendarios-Invisibles)
- **Error 117**: DSM API retorna error 117 al intentar eliminar calendarios UUID. Solución: PostgreSQL directo.

## 📧 Soporte

¿Problemas? Abre un [Issue](https://github.com/Zoimback/Suscripcion_Synology_Calendar/issues)
