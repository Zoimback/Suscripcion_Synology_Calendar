# Instalación en Synology NAS

## Método 1: Usando Python Package (Recomendado)

### 1. Instalar Python en DSM

1. Abre **Package Center** en DSM
2. Busca **Python 3.10** (o superior)
3. Haz clic en **Instalar**

### 2. Conectarse por SSH

```bash
# Desde tu PC
ssh usuario@nas.ejemplo.com
```

### 3. Crear Directorio del Proyecto

```bash
mkdir -p /volume1/scripts/ics-sync
cd /volume1/scripts/ics-sync
```

### 4. Clonar o Descargar el Proyecto

#### Opción A: Usando Git

```bash
# Instalar Git (si no está instalado)
sudo synopkg install Git

# Clonar repositorio
git clone https://github.com/Zoimback/Suscripcion_Synology_Calendar.git .
```

#### Opción B: Subir Archivos Manualmente

1. Descarga el proyecto como ZIP desde GitHub
2. Usa **File Station** para subir los archivos a `/volume1/scripts/ics-sync`

### 5. Instalar Dependencias

```bash
cd /volume1/scripts/ics-sync

# Localizar Python 3 instalado por Synology
/volume1/@appstore/py3k/usr/local/bin/python3 --version

# Instalar dependencias
/volume1/@appstore/py3k/usr/local/bin/python3 -m pip install -r requirements.txt

# O instalar el paquete completo
/volume1/@appstore/py3k/usr/local/bin/python3 -m pip install -e .
```

### 6. Crear config.json

```bash
cd /volume1/scripts/ics-sync
cp config.json.example config.json
nano config.json
```

Editar:

```json
{
  "caldav": {
    "url": "https://localhost:5001/caldav/tu_usuario/",
    "username": "tu_usuario",
    "password": "tu_contraseña",
    "verify_ssl": false
  },
  "sources": [
    {
      "url": "https://example.com/calendar.ics",
      "calendar_name": "Mi Calendario",
      "delete_removed_events": true
    }
  ],
  "log_file": "/volume1/logs/ics-sync.log"
}
```

**Nota:** Usa `verify_ssl: false` si el certificado es autofirmado.

### 7. Prueba Manual

```bash
cd /volume1/scripts/ics-sync
/volume1/@appstore/py3k/usr/local/bin/python3 -m ics_sync.cli --config config.json --dry-run
```

---

## Método 2: Usando Entorno Virtual

### 1. Crear Entorno Virtual

```bash
cd /volume1/scripts/ics-sync
/volume1/@appstore/py3k/usr/local/bin/python3 -m venv venv
```

### 2. Activar Entorno

```bash
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
# O
pip install -e .
```

### 4. Ejecutar

```bash
ics-sync --config config.json
```

---

## Tarea Programada

### Crear Tarea en Task Scheduler

1. Abre **Control Panel → Task Scheduler**
2. Haz clic en **Create → Scheduled Task → User-defined script**

### Configuración General

- **Task name**: `ICS to CalDAV Sync`
- **User**: Tu usuario (no `root`)
- **Enabled**: ☑

### Schedule

- **Run on the following days**: Daily
- **First run time**: `00:00`
- **Frequency**: Every hour
- **Last run time**: `23:00`

### Task Settings

**User-defined script:**

```bash
#!/bin/bash

cd /volume1/scripts/ics-sync
/volume1/@appstore/py3k/usr/local/bin/python3 -m ics_sync.cli --config config.json >> /volume1/logs/ics-sync.log 2>&1
```

**O con entorno virtual:**

```bash
#!/bin/bash

cd /volume1/scripts/ics-sync
source venv/bin/activate
ics-sync --config config.json >> /volume1/logs/ics-sync.log 2>&1
```

### Guardar y Ejecutar

1. Haz clic en **OK**
2. Selecciónala en la lista
3. Haz clic en **Run** para probar
4. Revisa los logs en `/volume1/logs/ics-sync.log`

---

## Permisos y Seguridad

### Crear Usuario Dedicado (Opcional)

```bash
# Crear usuario solo para ics-sync
sudo synouser --add ics-sync "" "ICS Sync Service" 0 "" ""

# Dar permisos al directorio
sudo chown -R ics-sync:users /volume1/scripts/ics-sync
sudo chmod 700 /volume1/scripts/ics-sync
sudo chmod 600 /volume1/scripts/ics-sync/config.json
```

Luego en Task Scheduler, selecciona el usuario `ics-sync`.

### Proteger config.json

```bash
# Solo el propietario puede leer/escribir
chmod 600 /volume1/scripts/ics-sync/config.json
```

---

## Verificación

### Ver Logs

```bash
# SSH al NAS
ssh usuario@nas.ejemplo.com

# Ver logs en tiempo real
tail -f /volume1/logs/ics-sync.log

# Ver últimas 50 líneas
tail -n 50 /volume1/logs/ics-sync.log
```

### Verificar Calendarios

1. Abre **Synology Calendar** en DSM
2. Verifica que los calendarios aparezcan
3. Abre un evento para confirmar los datos

### Probar desde iOS/Android

1. Configurar cuenta CalDAV:
   - Servidor: `nas.ejemplo.com`
   - Puerto: `5001`
   - Usuario / Contraseña
   - SSL: Activado

2. Los calendarios sincronizados deberían aparecer automáticamente

---

## Troubleshooting en Synology

### Error: "python3: command not found"

```bash
# Verificar instalación de Python
synopkg status py3k

# Si no está instalado
synopkg install py3k

# Localizar ejecutable
find /volume1/@appstore -name python3
```

### Error: "Permission denied"

```bash
# Dar permisos de ejecución
chmod +x /volume1/scripts/ics-sync/*.py
chmod +x /volume1/scripts/ics-sync/ics_sync/*.py
```

### Error: "No module named 'caldav'"

```bash
# Reinstalar dependencias
cd /volume1/scripts/ics-sync
/volume1/@appstore/py3k/usr/local/bin/python3 -m pip install --upgrade -r requirements.txt
```

### Task Scheduler no ejecuta la tarea

1. Verifica los logs en **Task Scheduler → [Tu tarea] → Action → View Result**
2. Asegúrate de usar rutas absolutas en el script
3. Prueba ejecutar el script manualmente por SSH primero

---

## Actualizaciones

### Actualizar Código

```bash
cd /volume1/scripts/ics-sync

# Con Git
git pull origin main

# O descarga y reemplaza archivos manualmente
```

### Actualizar Dependencias

```bash
cd /volume1/scripts/ics-sync
/volume1/@appstore/py3k/usr/local/bin/python3 -m pip install --upgrade -r requirements.txt
```

---

## Siguiente Paso

➡️ [Uso Básico](uso-basico.md)
