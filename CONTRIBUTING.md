# 🤝 Guía de Contribución

¡Gracias por tu interés en contribuir a Synology Calendar Sync! Este documento te guiará en el proceso.

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [¿Cómo puedo contribuir?](#cómo-puedo-contribuir)
- [Reportar Bugs](#reportar-bugs)
- [Sugerir Mejoras](#sugerir-mejoras)
- [Pull Requests](#pull-requests)
- [Estándares de Código](#estándares-de-código)
- [Configuración del Entorno](#configuración-del-entorno)

## 📜 Código de Conducta

Este proyecto se adhiere a un código de conducta para mantener un ambiente abierto y acogedor. Por favor:

- Usa lenguaje acogedor e inclusivo
- Respeta puntos de vista y experiencias diferentes
- Acepta críticas constructivas con gracia
- Enfócate en lo mejor para la comunidad

## 🚀 ¿Cómo puedo contribuir?

Hay muchas formas de contribuir:

### 🐛 Reportar Bugs

Antes de crear un reporte de bug:
- Verifica que uses la última versión
- Revisa si el bug ya fue reportado en [Issues](https://github.com/Zoimback/Suscripcion_Synology_Calendar/issues)
- Recopila información sobre el problema

**Plantilla de Bug Report:**

```markdown
**Descripción del problema:**
Descripción clara y concisa del bug.

**Pasos para reproducir:**
1. Ir a '...'
2. Ejecutar '...'
3. Ver error

**Comportamiento esperado:**
Qué esperabas que sucediera.

**Comportamiento actual:**
Qué sucedió en realidad.

**Entorno:**
- OS: [e.g. Windows 11, Ubuntu 22.04]
- Python: [e.g. 3.11.5]
- Versión del proyecto: [e.g. commit hash]

**Logs:**
```
Pega aquí los logs relevantes
```

**Capturas de pantalla:**
Si aplica, añade capturas.
```

### 💡 Sugerir Mejoras

Las sugerencias son bienvenidas! Incluye:

- **Descripción clara** de la mejora
- **Caso de uso**: Por qué sería útil
- **Ejemplo**: Si es posible, muestra cómo funcionaría

**Plantilla de Feature Request:**

```markdown
**¿Tu feature está relacionado con un problema?**
Descripción clara del problema. Ej: "Siempre me frustra cuando..."

**Solución propuesta:**
Descripción clara de lo que quieres que suceda.

**Alternativas consideradas:**
Otras soluciones o features que has considerado.

**Contexto adicional:**
Cualquier otro contexto, capturas, etc.
```

## 🔧 Pull Requests

### Proceso

1. **Fork** el repositorio
2. **Crea una rama** desde `main`:
   ```bash
   git checkout -b feature/mi-nueva-feature
   # o
   git checkout -b fix/mi-bug-fix
   ```

3. **Realiza tus cambios** siguiendo los [estándares de código](#estándares-de-código)

4. **Añade tests** si es aplicable

5. **Actualiza documentación** si es necesario

6. **Commit** con mensajes descriptivos:
   ```bash
   git commit -m "feat: añadir soporte para calendarios de Outlook
   
   - Implementar parser para formato Outlook ICS
   - Añadir manejo de zonas horarias UTC
   - Actualizar documentación"
   ```

7. **Push** a tu fork:
   ```bash
   git push origin feature/mi-nueva-feature
   ```

8. **Abre un Pull Request** en GitHub

### Convenciones de commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Cambios en documentación
- `style:` Formato, punto y coma, etc (sin cambio de código)
- `refactor:` Refactorización de código
- `test:` Añadir o modificar tests
- `chore:` Mantenimiento, dependencias, etc

**Ejemplos:**
```
feat: añadir soporte para calendarios de iCloud
fix: corregir conversión de zona horaria en eventos de día completo
docs: actualizar README con nuevos ejemplos
refactor: optimizar consulta de eventos existentes
```

### Checklist de PR

Antes de abrir tu PR, asegúrate de:

- [ ] El código sigue los estándares del proyecto
- [ ] Has testeado los cambios localmente
- [ ] Has actualizado la documentación
- [ ] Los commits tienen mensajes descriptivos
- [ ] No hay conflictos con `main`
- [ ] No incluyes datos sensibles (credenciales, IPs, etc.)

## 📝 Estándares de Código

### Python Style Guide

Seguimos [PEP 8](https://peps.python.org/pep-0008/):

```python
# ✅ Bueno
def sync_calendar(self, calendar_name, ics_url):
    """Sincroniza un calendario desde una URL ICS."""
    print(f"🔄 Sincronizando calendario: {calendar_name}")
    
# ❌ Malo
def sync_calendar(self,calendar_name,ics_url):
    print("Sincronizando calendario: "+calendar_name)
```

### Documentación

- Todas las funciones deben tener docstrings
- Usa type hints cuando sea posible
- Comenta lógica compleja

```python
def convert_to_spain_time(self, dt: datetime) -> datetime:
    """
    Convierte cualquier datetime a la zona horaria de España.
    
    Args:
        dt: Datetime a convertir (puede ser naive o aware)
        
    Returns:
        Datetime convertido a Europe/Madrid
    """
    spain_tz = pytz.timezone('Europe/Madrid')
    # ... código
```

### Manejo de Errores

- Usa try-except específicos
- Loggea errores descriptivos
- No silencies excepciones sin razón

```python
# ✅ Bueno
try:
    calendar.save_event(ical_str)
    added += 1
except Exception as e:
    print(f"⚠️ Error creando {event_data['summary']}: {e}")
    
# ❌ Malo
try:
    calendar.save_event(ical_str)
except:
    pass
```

## 🔨 Configuración del Entorno

### Instalación para desarrollo

1. **Fork y clonar:**
```bash
git clone https://github.com/TU_USUARIO/Suscripcion_Synology_Calendar.git
cd Suscripcion_Synology_Calendar
```

2. **Crear entorno virtual:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
pip install black flake8 mypy  # Herramientas de desarrollo
```

4. **Configurar pre-commit (opcional):**
```bash
pip install pre-commit
pre-commit install
```

### Testing Local

Antes de hacer commit:

```bash
# Formatear código
black main.py

# Verificar estilo
flake8 main.py --max-line-length=100

# Type checking
mypy main.py

# Probar script
python main.py
```

## 🏷️ Áreas de Contribución

Buscamos ayuda especialmente en:

### 🔥 Prioridad Alta
- [ ] Soporte para más servidores CalDAV (NextCloud, iCloud, etc.)
- [ ] Tests unitarios y de integración
- [ ] Dockerización completa
- [ ] Configuración vía variables de entorno

### 📚 Documentación
- [ ] Traducciones (inglés, catalán, etc.)
- [ ] Más ejemplos de uso
- [ ] Video tutoriales
- [ ] Wiki extendida

### ✨ Features
- [ ] Interfaz web de configuración
- [ ] Notificaciones (Discord, Telegram, email)
- [ ] Sincronización bidireccional
- [ ] Filtros avanzados de eventos
- [ ] Dashboard de estadísticas

### 🐛 Bugs Conocidos
- Ver [Issues](https://github.com/Zoimback/Suscripcion_Synology_Calendar/issues?q=is%3Aissue+is%3Aopen+label%3Abug)

## 📞 Preguntas

¿Tienes preguntas? 

- Abre un [Issue](https://github.com/Zoimback/Suscripcion_Synology_Calendar/issues) con la etiqueta `question`
- Revisa Issues cerrados para ver si ya fue respondida

## 🎉 Reconocimientos

Todos los contribuidores son reconocidos en:
- README.md
- Releases del proyecto
- Commits de GitHub

---

¡Gracias por contribuir! 🙌
