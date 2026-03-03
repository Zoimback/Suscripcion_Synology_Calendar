# Configuración

## Archivo config.json

Crea un archivo `config.json` en la raíz del proyecto:

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

## Configuración CalDAV

### URL de CalDAV

Formato: `https://[NAS_IP_O_DOMINIO]:[PUERTO]/caldav/[USUARIO]/`

**Ejemplos:**
```
https://192.168.1.100:5001/caldav/alex/
https://midrive.myds.me:5001/caldav/alex/
```

### Autenticación

#### Sin 2FA

Usa tu contraseña normal de DSM:

```json
{
  "username": "alex",
  "password": "mi_contraseña_dsm"
}
```

#### Con 2FA Habilitado

1. Ve a **DSM → Cuenta → Seguridad → Contraseñas de aplicaciones**
2. Haz clic en **Crear**
3. Nombre: `ICS Sync`
4. Permisos: Selecciona **Calendar**
5. Copia la contraseña generada
6. Úsala en `config.json`:

```json
{
  "username": "alex",
  "password": "xxxx-xxxx-xxxx-xxxx"
}
```

### Certificado SSL

```json
"verify_ssl": true   // Verificar certificado (recomendado)
"verify_ssl": false  // Ignorar certificado (solo para autofirmados)
```

## Configuración de Fuentes ICS

### Fuente Básica

```json
{
  "url": "https://example.com/calendar.ics",
  "calendar_name": "Mi Calendario",
  "delete_removed_events": false
}
```

### Múltiples Fuentes

```json
"sources": [
  {
    "url": "https://calendar.google.com/calendar/ical/.../basic.ics",
    "calendar_name": "Google Calendar",
    "delete_removed_events": true
  },
  {
    "url": "https://www.f1calendar.com/download/f1-calendar_p1_p2_p3_q_gp.ics",
    "calendar_name": "Fórmula 1",
    "delete_removed_events": false
  },
  {
    "url": "https://universidad.ejemplo.com/horarios.ics",
    "calendar_name": "Universidad",
    "delete_removed_events": true
  }
]
```

### Opciones por Fuente

| Opción | Tipo | Descripción |
|--------|------|-------------|
| `url` | string | **Requerido**. URL pública del archivo ICS |
| `calendar_name` | string | **Requerido**. Nombre del calendario en Synology |
| `delete_removed_events` | boolean | Eliminar eventos que ya no están en el ICS (default: `false`) |

### Ejemplos de Fuentes ICS

#### Google Calendar

1. Abre Google Calendar en web
2. Configuración → Configuración del calendario → [Tu Calendario]
3. Copia la **URL secreta en formato iCal**

```json
{
  "url": "https://calendar.google.com/calendar/ical/xxxxx%40gmail.com/private-xxxxx/basic.ics",
  "calendar_name": "Mi Google Calendar"
}
```

#### Fórmula 1

```json
{
  "url": "https://www.f1calendar.com/download/f1-calendar_p1_p2_p3_q_gp.ics",
  "calendar_name": "Fórmula 1"
}
```

#### Webcal (webcal://)

Convierte `webcal://` a `https://`:

```
webcal://example.com/calendar.ics
   ↓
https://example.com/calendar.ics
```

## Configuración de Logs

```json
"log_file": "sync.log"           // Archivo en directorio actual
"log_file": "/var/log/ics-sync.log"  // Ruta absoluta
"log_file": null                 // Solo salida por consola
```

---

## Siguiente Paso

➡️ [Uso Básico](uso-basico.md)
