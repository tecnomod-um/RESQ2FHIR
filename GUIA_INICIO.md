# RESQ2FHIR - Guía de Instalación y Uso (Español)

## Descripción General

RESQ2FHIR es un sistema completo para transformar datos de registros de ictus (stroke) en formato CSV preprocesados a recursos FHIR (HL7 FHIR R4) estándares de salud interoperables.

## Características Principales

✓ **Converter**: Transforma filas CSV a FHIR Bundles completos  
✓ **API REST**: FastAPI para procesamiento de lotes  
✓ **Validación**: Integración con validator-api para validar bundles  
✓ **Persistencia**: Opcional - guardar en servidor HAPI FHIR  
✓ **Docker**: Stack completo preparado para containerización  
✓ **Documentación**: Guías, ejemplos y mapeos de campos  

## INSTALACIÓN RÁPIDA

### Paso 1: Instalar Dependencias
```bash
pip install -r requirements.txt
```

### Paso 2: Configuración Mínima
```bash
# Crear archivo de configuración
cp .env.example .env

# Editar .env y asegurar que CONVERTER_CMD está configurado
# La línea debe ser:
# CONVERTER_CMD=python scripts/transform.py --input {in} --outdir {out}
```

### Paso 3: Verificar Instalación
```bash
python setup_demo.py
```

## USO - OPCIÓN 1: Converter CLI (Más Simple)

Ejecutar el converter directamente sin necesidad de API:

```bash
python scripts/transform.py \
  --input data/data-extended.csv \
  --outdir ./bundles \
  --verbose
```

**Resultado:**
- Archivos JSON en `./bundles/`
- Un archivo JSON por paciente
- Cada archivo es un FHIR Bundle completo

## USO - OPCIÓN 2: API REST (Recomendado)

Iniciar el servidor FastAPI y enviar CSVs vía HTTP:

```bash
# Terminal 1: Iniciar servidor
uvicorn scripts.main:app --reload

# Terminal 2: Enviar CSV
curl -X POST http://localhost:8000/jobs/csv \
  -F "file=@data/data-extended.csv"
```

**Respuesta:**
```json
{
  "jobId": "20240101-120000-a1b2c3d4",
  "totals": {
    "bundles": 150,
    "errors": 0,
    "warnings": 5
  },
  "bySeverity": {
    "fatal": 0,
    "error": 0,
    "warning": 5,
    "information": 120
  }
}
```

## USO - OPCIÓN 3: Docker (Producción)

Desplegar stack completo con validador y HAPI:

```bash
docker-compose up
```

**Servicios disponibles:**
- API: http://localhost:8000
- Validador: http://localhost:8085
- HAPI FHIR: http://localhost:8080

## ESTRUCTURA DE DATOS

### CSV de Entrada
El archivo CSV debe contener:
- `case_id`: Identificador único del paciente
- `hospital_name`: Nombre del hospital
- `sex`: Género (male/female/other)
- `age`: Edad en años
- `stroke_type`: Tipo de ictus (ischemic/hemorrhagic/tia)
- `systolic_pressure`, `diastolic_pressure`: Presión arterial
- Y muchos otros campos clínicos...

Ver `DATA_TRANSFORMATION.md` para mapeo completo de campos.

### FHIR Bundle de Salida
Cada bundle contiene:
- **Organization**: Hospital/Centro
- **Patient**: Datos demográficos del paciente
- **Encounter**: Información de ingreso/alta
- **Condition**: Diagnósticos e historia médica
- **Observation**: Mediciones, puntuaciones (NIHSS, mRS, etc.)
- **Procedure**: Procedimientos realizados (trombectomía, etc.)
- **MedicationStatement/MedicationRequest**: Medicamentos

## SOLUCIÓN DE PROBLEMAS

### Error: "CONVERTER_CMD is not set"
**Solución:** Asegurar que en `.env` está:
```
CONVERTER_CMD=python scripts/transform.py --input {in} --outdir {out}
```

### Error: "No module named 'scripts'"
**Solución:** Ejecutar desde la raíz del proyecto:
```bash
cd RESQ2FHIR
export PYTHONPATH="$PYTHONPATH:$(pwd)"
python scripts/transform.py --input data/data-extended.csv --outdir ./bundles
```

### Error: Campos CSV faltantes
**Solución:** Verificar que el CSV tenga todas las columnas requeridas:
```bash
# Ver primeras líneas del CSV
head -1 data/data-extended.csv

# Contar columnas
head -1 data/data-extended.csv | tr ',' '\n' | wc -l
```

### Error de codificación UTF-8
**Solución:** Convertir CSV a UTF-8:
```bash
iconv -f ISO-8859-1 -t UTF-8 input.csv > output_utf8.csv
```

## CONFIGURACIÓN AVANZADA

### Variables de Entorno Principales

```bash
# Requerido
CONVERTER_CMD=python scripts/transform.py --input {in} --outdir {out}

# Validador FHIR (opcional)
VALIDATOR_BASE_URL=http://localhost:8085
VALIDATOR_PATH=/api/validate/bundle

# Servidor HAPI FHIR (opcional, para persistencia)
HAPI_BASE_URL=http://localhost:8080/fhir
HAPI_BEARER=

# Directorio de trabajo
WORKDIR=/tmp/resq2fhir/workdir
```

Ver `.env.local` para todas las opciones disponibles.

## EJEMPLOS DE USO

### Ejemplo 1: Convertir un pequeño lote
```bash
python scripts/transform.py \
  --input data/data-extended.csv \
  --outdir ./demo_bundles \
  --verbose
```

### Ejemplo 2: Procesar vía API con validación
```bash
curl -X POST http://localhost:8000/jobs/csv \
  -F "file=@data/data-extended.csv" \
  -F "parallelism=6" \
  -F "persistToHapi=false"
```

### Ejemplo 3: Guardar en servidor HAPI
```bash
# Asegurar que HAPI está corriendo
docker-compose up hapi

# Enviar CSV con persistencia
curl -X POST http://localhost:8000/jobs/csv \
  -F "file=@data/data-extended.csv" \
  -F "persistToHapi=true"
```

## MONITOREO

### Ver resultados de un job
```bash
# Listar jobs
ls workdir/jobs/

# Ver resumen del job
cat workdir/jobs/{job_id}/job.json | python -m json.tool

# Ver logs del converter
tail workdir/jobs/{job_id}/_converter.stdout.log
tail workdir/jobs/{job_id}/_converter.stderr.log

# Ver resultados de validación
ls workdir/jobs/{job_id}/outcomes/
cat workdir/jobs/{job_id}/outcomes/*.oo.json
```

## TESTING

### Ejecutar tests de integración
```bash
python test_converter.py --verbose
```

### Verificar estructura del proyecto
```bash
python verify_structure.py
```

### Probar con datos de ejemplo
```bash
python setup_demo.py
```

## DOCUMENTACIÓN

- **README.md** - Documentación técnica completa
- **SETUP.md** - Guía de instalación en inglés
- **DATA_TRANSFORMATION.md** - Mapeo detallado de campos CSV a FHIR
- **CONTRIBUTING.md** - Cómo extender el sistema
- **QUICKSTART.sh** - Ejemplos de línea de comandos (Linux/Mac)
- **QUICKSTART.ps1** - Ejemplos PowerShell (Windows)

## ARQUITECTURA

```
CSV Input
    ↓
[scripts/transform.py]
    ├─ Lee CSV con pandas
    ├─ Valida campos
    └─ Transforma a FHIR
    ↓
JSON Bundles
    ↓
[FastAPI - main.py]
    ├─ Validación con validator-api
    └─ Persistencia a HAPI FHIR (opcional)
    ↓
Output: Job Report + FHIR Resources
```

## REQUISITOS

- Python 3.9+
- pip (gestor de paquetes)
- (Opcional) Docker para despliegue containerizado
- (Opcional) Servicio validador FHIR
- (Opcional) Servidor HAPI FHIR

## INSTALACIÓN DE DEPENDENCIAS

```bash
# Con pip directo
pip install -r requirements.txt

# Con virtual environment (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## DESPLIEGUE EN PRODUCCIÓN

### Con Docker Compose
```bash
docker-compose up -d
```

### En Kubernetes (ejemplo)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resq2fhir-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: resq2fhir
  template:
    metadata:
      labels:
        app: resq2fhir
    spec:
      containers:
      - name: api
        image: resq2fhir:latest
        ports:
        - containerPort: 8000
        env:
        - name: CONVERTER_CMD
          value: "python scripts/transform.py --input {in} --outdir {out}"
```

## NOTAS IMPORTANTES

1. **Configuración obligatoria**: `CONVERTER_CMD` debe estar establecido
2. **Encoding**: CSV debe usar UTF-8
3. **Campos requeridos**: Verificar `DATA_TRANSFORMATION.md`
4. **Seguridad**: Nunca commitear `.env` con credenciales reales
5. **Performance**: Para >100k registros, considerar Spark

## SOPORTE Y CONTACTO

- Revisar documentación incluida
- Ver logs en `workdir/jobs/{job_id}/`
- Revisar outcomes de validación

## VERSIÓN

- RESQ2FHIR: 1.0.0
- FHIR: R4 (4.0.1)
- Python: 3.9+
- Fecha: 2024

---

¡Listo para comenzar! Ejecuta `python setup_demo.py` para verificar la instalación.
