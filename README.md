# 📅 Synology Calendar Sync

Sistema automático de sincronización de calendarios desde URLs ICS a Synology CalDAV.

## 📋 Descripción

Este proyecto sincroniza automáticamente eventos desde múltiples fuentes de calendarios ICS (Google Calendar, calendarios deportivos, eventos universitarios, etc.) hacia tu servidor Synology CalDAV. Ideal para centralizar todos tus calendarios en un único lugar con actualizaciones automáticas cada 15 minutos.

## ✨ Características

- 🔄 **Sincronización automática** desde múltiples URLs ICS
- 📱 **Multi-calendario**: Soporta ilimitados calendarios de origen
- 🇪🇸 **Zona horaria**: Conversión automática a Europe/Madrid
- ⏰ **Alarmas inteligentes**: 15 y 5 minutos antes de cada evento
- 🚀 **Solo eventos futuros**: Ignora automáticamente eventos pasados
- 🔍 **Detección de duplicados**: Usa UID para evitar eventos duplicados
- 🔄 **Actualización inteligente**: Solo modifica eventos que cambien
- 📊 **Logging detallado**: Información clara del proceso de sincronización
- 🔒 **Seguro**: Credenciales protegidas en archivo local no versionado

## 🛠️ Requisitos

- Python 3.8+
- Servidor Synology con CalDAV habilitado
- Acceso a internet para descargar calendarios ICS

## 📦 Instalación

1. **Clonar el repositorio:**
```bash
git clone https://github.com/Zoimback/Suscripcion_Synology_Calendar.git
cd Suscripcion_Synology_Calendar
```

2. **Crear entorno virtual (recomendado):**
```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

## ⚙️ Configuración

1. **Crear archivo de configuración:**
```bash
cp events.json.example events.json
```

2. **Editar `events.json` con tus datos:**
```json
{
  "caldav": {
    "url": "https://tu-synology.com:5001/caldav/",
    "username": "tu_usuario",
    "password": "tu_contraseña"
  },
  "calendarios": [
    {
      "nombre": "Mi Calendario",
      "url_ics": "https://ejemplo.com/calendario.ics"
    }
  ]
}
```

### 📝 Notas de configuración:

- **URL CalDAV**: Típicamente `https://tu-nas:5001/caldav/` o `http://tu-nas:5000/caldav/`
- **URLs ICS**: Reemplaza `webcal://` por `https://` si es necesario
- **Múltiples calendarios**: Añade más objetos al array `calendarios`

## 🚀 Uso

### Ejecución manual:
```bash
python main.py
```

### Ejecución automática (cada 15 minutos):

**Windows - Programador de Tareas:**
1. Abrir "Programador de tareas"
2. Crear tarea básica
3. Desencadenador: Cada 15 minutos
4. Acción: `python` con argumento `C:\ruta\completa\main.py`

**Linux/Mac - Cron:**
```bash
crontab -e
# Añadir línea:
*/15 * * * * cd /ruta/al/proyecto && /ruta/al/venv/bin/python main.py
```

**Docker (opcional):**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main.py .
CMD ["python", "-u", "main.py"]
```

## 📊 Salida esperada

```
============================================================
🚀 Iniciando sincronización - 2026-02-25 11:49:12
============================================================

🔄 Sincronizando calendario: Universidad
📋 Usando calendario existente: Universidad
📊 Eventos existentes: 4
⏭️  Eventos pasados omitidos: 2
📥 Eventos futuros a sincronizar: 8
✅ Completado: 3 añadidos, 5 actualizados

============================================================
✨ Sincronización completada
============================================================
```

## 🔧 Solución de problemas

### Error: 405 Method Not Allowed
- Verifica que el calendario destino exista en Synology
- Comprueba permisos de escritura del usuario CalDAV
- Revisa la URL CalDAV (debe incluir `/caldav/`)

### Error: No module named 'caldav'
```bash
pip install -r requirements.txt
```

### Eventos no se actualizan
- Verifica que las URLs ICS sean accesibles
- Comprueba credenciales en `events.json`
- Revisa logs para errores específicos

### Zona horaria incorrecta
- El script convierte automáticamente a Europe/Madrid
- Puedes modificar `pytz.timezone('Europe/Madrid')` en el código

## 🗂️ Estructura del proyecto

```
Suscripcion_Synology_Calendar/
├── main.py              # Script principal
├── events.json          # Configuración (no versionado)
├── events.json.example  # Plantilla de configuración
├── requirements.txt     # Dependencias
├── .gitignore          # Archivos ignorados
├── README.md           # Este archivo
└── CONTRIBUTING.md     # Guía de contribución
```

## 📚 Fuentes de calendarios ICS

Ejemplos de calendarios públicos ICS:

- **Google Calendar**: Configuración → Integrar calendario → Dirección secreta en formato iCal
- **Fórmula 1**: `https://files-f1.motorsportcalendars.com/es/f1-calendar_qualifying_sprint_gp.ics`
- **Deportes**: [MotorsportCalendars](https://www.motorsportcalendars.com/)
- **Festivos**: Busca "calendario festivos ICS [país]"

## 🤝 Contribuir

Lee [CONTRIBUTING.md](CONTRIBUTING.md) para conocer cómo contribuir al proyecto.

## 📝 Licencia

Este proyecto es de código abierto. Consulta el archivo LICENSE para más detalles.

## 🙏 Agradecimientos

- [caldav](https://github.com/python-caldav/caldav) - Librería CalDAV
- [icalendar](https://github.com/collective/icalendar) - Parser de iCalendar
- [pytz](https://pypi.org/project/pytz/) - Zonas horarias

## 📧 Contacto

- **GitHub**: [@Zoimback](https://github.com/Zoimback)
- **Issues**: [Reportar problema](https://github.com/Zoimback/Suscripcion_Synology_Calendar/issues)

---

⭐ Si este proyecto te resulta útil, ¡dale una estrella en GitHub!
