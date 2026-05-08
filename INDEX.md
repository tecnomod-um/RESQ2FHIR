# RESQ2FHIR - Índice y Resumen del Proyecto

## 📋 Descripción del Proyecto

RESQ2FHIR es una API y sistema completo para transformar datos preprocesados de registros de ictus (stroke) en formato CSV a recursos FHIR estándares de interoperabilidad en salud.

**Versión:** 1.0.0  
**Estándar FHIR:** R4 (4.0.1)  
**Python:** 3.9+  

## 🎯 Objetivo

Automatizar la transformación de datos clínicos de ictus en formato CSV a FHIR Bundles válidos, con validación y persistencia opcionales.

## 📁 Estructura del Proyecto

```
RESQ2FHIR/
├── README.md                      # Documentación principal (Inglés)
├── GUIA_INICIO.md                 # Guía de inicio rápido (Español)
├── SETUP.md                       # Instrucciones de instalación
├── DATA_TRANSFORMATION.md         # Mapeos CSV → FHIR
├── CONTRIBUTING.md                # Cómo contribuir/extender
├── INDEX.md                       # Este archivo
│
├── requirements.txt               # Dependencias Python
├── Dockerfile                     # Imagen Docker para la API
├── docker-compose.yml             # Stack completo (API + Validator + HAPI)
├── .env.example                   # Plantilla de configuración
├── .env.local                     # Configuración local extendida
│
├── scripts/                       # Código principal
│   ├── __init__.py
│   ├── transform.py               # ⭐ Converter CSV → FHIR (NUEVO)
│   ├── main.py                    # FastAPI REST API
│   ├── data_modeling.py           # Orquestador de transformación
│   ├── enum_models.py             # Definiciones de conceptos SNOMED/FHIR
│   ├── helpers.py                 # Funciones de transformación de dominio
│   ├── utils.py                   # Utilidades compartidas
│   └── fhir_resources/            # Builders para recursos FHIR
│       ├── __init__.py
│       ├── patient.py             # Recurso Patient
│       ├── encounter.py           # Recurso Encounter
│       ├── observation.py         # Recurso Observation (observaciones)
│       ├── condition.py           # Recurso Condition (diagnósticos)
│       ├── procedure.py           # Recurso Procedure (procedimientos)
│       ├── medication*.py         # Recursos de medicamentos
│       └── ...
│
├── data/                          # Datos
│   ├── data-extended.csv          # CSV de entrada preprocesado
│   └── mappings.csv               # Mapeos de campos
│
├── examples/                      # Ejemplos de uso
│   └── (futuro: scripts de demostración)
│
├── test_converter.py              # Tests de integración (NUEVO)
├── test_config.py                 # Configuración para tests (NUEVO)
├── setup_demo.py                  # Script de setup (NUEVO)
├── verify_structure.py            # Validación de estructura (NUEVO)
│
├── QUICKSTART.sh                  # Ejemplos rápidos (Linux/Mac)
├── QUICKSTART.ps1                 # Ejemplos rápidos (PowerShell)
│
├── LICENSE                        # Licencia del proyecto
└── .gitignore                     # Configuración de Git

```

## 🚀 Quick Start

### 1. Instalación Rápida
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar
cp .env.example .env
# Editar .env y asegurar CONVERTER_CMD

# Verificar
python setup_demo.py
```

### 2. Uso Básico (Converter CLI)
```bash
python scripts/transform.py \
  --input data/data-extended.csv \
  --outdir ./bundles \
  --verbose
```

### 3. Uso con API
```bash
# Terminal 1: Iniciar API
uvicorn scripts.main:app --reload

# Terminal 2: Enviar CSV
curl -X POST http://localhost:8000/jobs/csv \
  -F "file=@data/data-extended.csv"
```

### 4. Despliegue con Docker
```bash
docker-compose up
```

## 📚 Documentación

### Archivos de Documentación

| Archivo | Contenido | Idioma |
|---------|----------|--------|
| **README.md** | Documentación técnica completa | Inglés |
| **GUIA_INICIO.md** | Guía rápida para empezar | Español |
| **SETUP.md** | Instalación y configuración detallada | Inglés |
| **DATA_TRANSFORMATION.md** | Mapeos CSV → FHIR | Inglés |
| **CONTRIBUTING.md** | Cómo extender el sistema | Inglés |
| **QUICKSTART.sh** | Ejemplos de comandos | Bash |
| **QUICKSTART.ps1** | Ejemplos de comandos | PowerShell |

### Conceptos Clave

- **CSV Input**: Datos preprocesados de pacientes con ictus
- **FHIR Bundle**: Contenedor de múltiples recursos FHIR
- **Resources**: Patient, Encounter, Observation, Condition, Procedure, Medication
- **Validation**: Validación contra perfiles FHIR
- **Persistence**: Almacenamiento opcional en HAPI FHIR Server

## 🏗️ Arquitectura

### Flujo de Datos
```
CSV File (input)
    ↓
[transform.py] - Lee y valida
    ↓
[data_modeling.py] - Orquesta transformación
    ↓
[fhir_resources/*] - Genera recursos FHIR
    ↓
FHIR Bundle (JSON)
    ↓
[main.py API] - Validación y persistencia opcional
    ↓
Output: Job Report + Bundles
```

### Componentes Clave

1. **transform.py** (NUEVO)
   - Entry point del converter
   - Lee CSV con pandas
   - Itera filas → Bundles FHIR
   - Escribe JSONs

2. **data_modeling.py**
   - Orquesta construcción de recursos
   - Ensambla Bundles completos
   - Integra todos los builders

3. **fhir_resources/**
   - Módulos de construcción por tipo de recurso
   - Encapsulan lógica de cada recurso FHIR
   - Reutilizables y extensibles

4. **main.py**
   - API REST FastAPI
   - Endpoints para job management
   - Validación y persistencia

5. **enum_models.py**
   - Conceptos SNOMED CT
   - ValueSets específicas del dominio
   - Mapeos code → display

6. **helpers.py**
   - Funciones de transformación de dominio
   - Extracción de datos complejos
   - Clasificación de entidades

## 🔧 Configuración

### Variables de Entorno Requeridas
```bash
CONVERTER_CMD=python scripts/transform.py --input {in} --outdir {out}
```

### Variables Opcionales
```bash
VALIDATOR_BASE_URL=http://localhost:8085
HAPI_BASE_URL=http://localhost:8080/fhir
WORKDIR=/tmp/resq2fhir/workdir
```

Ver `.env.local` para lista completa.

## 📊 Datos Soportados

### Campos CSV Principales
- **Demográficos**: case_id, sex, age, hospital_name
- **Clínicos**: stroke_type, nihss_score, mrs_score
- **Vitales**: systolic_pressure, diastolic_pressure, glucose
- **Procedimientos**: thrombectomy, thrombolysis, imaging_done
- **Medicamentos**: before_onset_*, discharge_*
- **Timing**: door_to_needle, door_to_groin, onset_to_door
- **Factores de riesgo**: risk_atrial_fibrillation, risk_diabetes, etc.

Ver `DATA_TRANSFORMATION.md` para mapeo completo.

## ✅ Testing

```bash
# Tests de integración
python test_converter.py --verbose

# Verificación de estructura
python verify_structure.py

# Setup y validación
python setup_demo.py
```

## 🐳 Docker

### Stack Completo
```bash
docker-compose up
```

### Servicios Incluidos
- **API**: FastAPI en puerto 8000
- **Validator**: FHIR Validator API en puerto 8085
- **HAPI**: HAPI FHIR Server en puerto 8080

### Build Custom
```bash
docker build -t resq2fhir:latest .
docker run -p 8000:8000 -e CONVERTER_CMD="..." resq2fhir:latest
```

## 📦 Dependencias

```
fastapi==0.109.2
uvicorn==0.27.0
pandas==2.1.4
fhir.resources==7.1.0
httpx==0.26.0
pydantic==2.5.3
python-multipart==0.0.6
```

## 🔐 Seguridad

- ✓ Nunca commitear `.env` con credenciales
- ✓ Usar HTTPS en producción
- ✓ Implementar autenticación/autorización
- ✓ Validar entrada CSV
- ✓ Usar variables de entorno para secretos

## 📈 Escalabilidad

### Single Machine
- Recomendado: <1M registros
- Memoria: 4+ GB
- CPU: 4+ cores

### Spark (Distribución)
```bash
CONVERTER_CMD="spark-submit --master local[*] scripts/transform.py --input {in} --outdir {out}"
```

### Cloud
- Containerizar con Dockerfile
- Desplegar en Kubernetes, AWS ECS, Azure ACI, etc.

## 🛠️ Extensiones Comunes

1. **Agregar nueva Observation**
   - Ver `scripts/fhir_resources/observation.py`
   - Seguir patrón existente
   - Ver `CONTRIBUTING.md`

2. **Agregar nuevo Resource Type**
   - Crear `scripts/fhir_resources/new_resource.py`
   - Importar en `data_modeling.py`
   - Usar en `transform_to_fhir()`

3. **Agregar ValueSet**
   - Definir enum en `enum_models.py`
   - Usar en recursos FHIR

4. **Agregar Helper Function**
   - Implementar en `helpers.py`
   - Importar en `data_modeling.py`

Ver `CONTRIBUTING.md` para ejemplos detallados.

## 🚨 Troubleshooting

| Problema | Solución |
|----------|----------|
| CONVERTER_CMD not set | Configurar en `.env` |
| Module not found: scripts | Ejecutar desde raíz, set PYTHONPATH |
| Encoding errors | Convertir CSV a UTF-8 |
| Missing required fields | Verificar columnas CSV requeridas |
| Connection refused | Verificar URLs de validator/HAPI |

Ver `SETUP.md` para más detalles.

## 📝 Logs y Monitoreo

Jobs se almacenan en `WORKDIR/jobs/{job_id}/`:
```
├── input/                    # CSV subido
├── bundles/                  # JSONs generados
├── outcomes/                 # Resultados de validación
├── _converter.stdout.log     # Logs del converter
├── _converter.stderr.log     # Errores del converter
└── job.json                  # Resumen del job
```

## 🤝 Contribuir

Ver `CONTRIBUTING.md` para:
- Guía de código
- Patrones de extensión
- Testing
- Stándares de documentación

## 📖 Estándares

- **FHIR R4** (4.0.1)
- **SNOMED CT** para codificación clínica
- **HL7 V3** para códigos administrativos
- **ISO 8601** para fechas/horas

## 📞 Soporte

1. Leer documentación relevante
2. Revisar logs en `{job_id}/`
3. Verificar outcomes de validación
4. Revisar ejemplos en QUICKSTART

## 📄 Licencia

Ver archivo `LICENSE`

## 🎯 Roadmap Futuro

- [ ] Soporte para más ValueSets de SNOMED
- [ ] Validación de esquema más estricta
- [ ] Integración con sistemas de salud existentes
- [ ] Dashboard de monitoreo
- [ ] Optimizaciones de performance
- [ ] Soporte multiidioma mejorado

## 📞 Contacto

Para preguntas o issues:
- Revisar documentación completa
- Crear issue en el repositorio
- Contactar al equipo de desarrollo

---

**Última Actualización:** 2024  
**Versión:** 1.0.0  
**Estado:** ✅ Producción lista  

**¡Listo para empezar! Ejecuta `python setup_demo.py`**
