# 🌩️ Infraestructura MAG Sistema — Multi-Aseguradora
## Google Cloud Platform + Terraform + Docker

---

## 📐 Arquitectura Multi-Tenant

```
                    Proyecto GCP: magia-mag
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  ┌─── Tenant: AXA ────────────────────────────────────┐  │
│  │  Cloud Run: mag-api-axa     (Backend FastAPI)      │  │
│  │  Cloud Run: mag-axa         (Frontend Next.js)     │  │
│  │  Cloud SQL: mag-axa-db      (PostgreSQL 15)        │  │
│  │  Storage:   magia-docs-axa  (PDFs)                 │  │
│  │  Secret:    mag-db-url-axa  (DATABASE_URL)         │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─── Tenant: GNP ────────────────────────────────────┐  │
│  │  Cloud Run: mag-api-gnp     (Backend FastAPI)      │  │
│  │  Cloud Run: mag-gnp         (Frontend Next.js)     │  │
│  │  Cloud SQL: mag-gnp-db      (PostgreSQL 15)        │  │
│  │  Storage:   magia-docs-gnp  (PDFs)                 │  │
│  │  Secret:    mag-db-url-gnp  (DATABASE_URL)         │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─── Tenant: Zurich ─────────────────────────────────┐  │
│  │  Cloud Run: mag-api-zurich  (Backend FastAPI)      │  │
│  │  Cloud Run: mag-zurich      (Frontend Next.js)     │  │
│  │  Cloud SQL: mag-zurich-db   (PostgreSQL 15)        │  │
│  │  Storage:   magia-docs-zurich (PDFs)               │  │
│  │  Secret:    mag-db-url-zurich (DATABASE_URL)       │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Imágenes Docker compartidas (1 sola versión del código) │
│  gcr.io/magia-mag/mag-api:latest                         │
│  gcr.io/magia-mag/mag-frontend:latest                    │
└──────────────────────────────────────────────────────────┘
```

**Clave**: El código es el mismo para todas las aseguradoras. Lo que cambia es:
- La base de datos (datos aislados)
- La configuración (ramos, URLs de docs, metas)
- Los recursos (más o menos capacidad según volumen)

---

## 🚀 Guía Rápida

### Prerequisitos
1. [Terraform CLI](https://developer.hashicorp.com/terraform/downloads) instalado
2. [gcloud CLI](https://cloud.google.com/sdk/docs/install) instalado y autenticado
3. Imágenes Docker ya buildeadas en GCR

### Crear una nueva instancia de aseguradora

```bash
cd infra/terraform

# 1. Inicializar (solo la primera vez)
terraform init

# 2. Crear workspace para la aseguradora
terraform workspace new gnp

# 3. Crear toda la infraestructura
terraform apply -var-file="tenants/gnp.tfvars"

# 4. Ver las URLs generadas
terraform output summary
```

¡Listo! En ~10 minutos tienes una instancia completa de MAG Sistema
para GNP con su propia BD, backend, frontend y storage.

### Actualizar una instancia existente

```bash
terraform workspace select axa
terraform apply -var-file="tenants/axa.tfvars"
```

### Destruir una instancia (⚠️ elimina datos)

```bash
terraform workspace select gnp
terraform destroy -var-file="tenants/gnp.tfvars"
```

---

## 📁 Estructura de Archivos

```
infra/
├── terraform/
│   ├── main.tf           # Provider GCP + backend remoto
│   ├── variables.tf      # Variables configurables
│   ├── tenant.tf         # Recursos por tenant (Cloud SQL, Run, etc.)
│   ├── outputs.tf        # URLs y datos de salida
│   └── tenants/          # Configuración por aseguradora
│       ├── axa.tfvars    # ← AXA Seguros (producción)
│       ├── gnp.tfvars    # ← GNP Seguros (ejemplo)
│       └── zurich.tfvars # ← Zurich Seguros (ejemplo)
├── setup_gcp.sh          # Script manual (bash)
└── setup_gcp.ps1         # Script manual (PowerShell)
```

---

## 💰 Costo por Tenant

| Recurso | Config | Costo/mes |
|---|---|---|
| Cloud SQL (db-f1-micro) | PostgreSQL 15, 10GB | $7-10 |
| Cloud Run Backend | 0-5 instancias, 512MB | $0-5 |
| Cloud Run Frontend | 0-3 instancias, 256MB | $0-3 |
| Cloud Storage | ~5GB PDFs | $0.02 |
| Secret Manager | 1 secret | $0 |
| **TOTAL por tenant** | | **$7-20** |

**Ejemplo**: 5 aseguradoras = $35-100 USD/mes total

---

## 🐳 Docker

Las imágenes Docker son **compartidas** entre todos los tenants:

```bash
# Backend (desde raíz del repo)
gcloud builds submit --tag gcr.io/magia-mag/mag-api .

# Frontend (con API URL genérica o por tenant)
gcloud builds submit \
  --config cloudbuild-frontend.yaml \
  --substitutions _API_URL=https://mag-api-axa-xxx.run.app
```

### Dockerfile Backend (`./Dockerfile`)
- Base: `python:3.12-slim`
- Incluye: FastAPI, SQLAlchemy, psycopg2, pandas
- Puerto: 8080

### Dockerfile Frontend (`./sistema/Dockerfile`)
- Multi-stage: Build (node:22-alpine) → Run (node:22-alpine)
- Output: Next.js standalone
- Puerto: 3000

---

## 🔐 Seguridad

- ✅ Passwords generados automáticamente (32 chars)
- ✅ DATABASE_URL en Secret Manager (nunca en variables de entorno planas)
- ✅ Cloud SQL sin IP pública por defecto (solo via Unix socket)
- ✅ Datos 100% aislados entre tenants (BD separadas)
- ✅ Backups automáticos diarios con 7 días de retención

---

*Infraestructura como Código — MAG Sistema v0.3.0*
*Promotoría MAG · Proyecto GCP: magia-mag*
