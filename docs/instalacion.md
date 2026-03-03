# Instalación

## Requisitos

- **Python**: 3.10 o superior
- **Synology NAS**: DSM 7.x con Calendar package instalado
- **CalDAV**: Debe estar habilitado en DSM

## Instalación Local (Windows/Mac/Linux)

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Zoimback/Suscripcion_Synology_Calendar.git
cd Suscripcion_Synology_Calendar
```

### 2. Crear Entorno Virtual (Recomendado)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependencias

```bash
# Opción A: Instalación editable (desarrollo)
pip install -e .

# Opción B: Solo dependencias
pip install -r requirements.txt
```

### 4. Verificar Instalación

```bash
ics-sync --help
```

Deberías ver el mensaje de ayuda del comando.

---

## Instalación en Synology NAS

Ver [Instalación en Synology](instalacion-synology.md) para instrucciones completas.

---

## Siguiente Paso

➡️ [Configuración](configuracion.md)
