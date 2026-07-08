# 🔍 Guía de Debugging con Logging

Este proyecto ahora tiene un sistema de logging centralizado para que **puedas debugguear fácilmente** y ver todos los logs en consola y archivo.

## 📝 Cómo Usar

### Opción 1: Usar Logger en tus scripts

```python
from scripts.logging_config import get_logger

logger = get_logger(__name__)

# Diferentes niveles de log
logger.debug("Mensaje de debug")
logger.info("Información importante")
logger.warning("Advertencia")
logger.error("Error encontrado")
logger.critical("Problema crítico")
```

### Opción 2: Usar print() normal (se redirige a logs automáticamente)

El proyecto está configurado para capturar `print()` automáticamente y enviarlos a los logs.

```python
print("Este print aparecerá en los logs")
```

## 📍 Dónde se guardan los logs

- **Consola**: Verás los logs en tiempo real mientras corre la app
- **Archivo**: `./logs/resq2fhir.log` - historial completo

## 🎚️ Niveles de Log

| Nivel | Uso |
|-------|-----|
| **DEBUG** | Información detallada para debugging |
| **INFO** | Información general importante |
| **WARNING** | Advertencias (problemas potenciales) |
| **ERROR** | Errores que ocurrieron |
| **CRITICAL** | Problemas críticos |

## 🔧 Configurar el Nivel de Log

### Por variable de entorno:
```bash
# Mostrar solo INFO y superiores
RESQ_LOG_LEVEL=INFO python -m uvicorn scripts.main:app --reload

# Para DEBUG completo (más verbose)
RESQ_LOG_LEVEL=DEBUG python -m uvicorn scripts.main:app --reload
```

### Por defecto:
Si no configuras nada, usa **DEBUG** (máximo detalle).

## 💡 Ejemplos Prácticos

### En FastAPI routes:
```python
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    logger.info(f"Uploading file: {file.filename}")
    logger.debug(f"File size: {len(file.file.read())} bytes")
    # ... tu código
```

### En funciones de transformación:
```python
def transform_data(data):
    logger.debug(f"Input data shape: {data.shape}")
    try:
        result = process(data)
        logger.info("Transformation completed successfully")
        return result
    except Exception as e:
        logger.error(f"Transformation failed: {e}", exc_info=True)
        raise
```

## 🚀 Rápido Start

1. Ya está todo configurado en `main.py`
2. Solo necesitas importar y usar:

```python
from scripts.logging_config import get_logger
logger = get_logger(__name__)
logger.info("¡Listo para debugguear!")
```

## 📂 Estructura de Archivos

```
scripts/
├── logging_config.py     ← ✨ Nuevo: configuración centralizada
├── main.py               ← Actualizado con logging
├── utils.py
└── ...
logs/
└── resq2fhir.log         ← Se crea automáticamente
```

---

**¿Preguntas?** Revisa los ejemplos en `logging_config.py` o `main.py`.
