#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# setup_gcp.sh — Provisión del proyecto 'magia' en Google Cloud
# MAG Sistema — Promotoría MAG · AXA Seguros México
# ═══════════════════════════════════════════════════════════════════
#
# Uso: bash infra/setup_gcp.sh
# Prerequisito: gcloud CLI instalado y autenticado
#
# Este script crea:
# 1. Proyecto GCP "magia"
# 2. Habilita APIs necesarias
# 3. Crea instancia Cloud SQL (PostgreSQL)
# 4. Crea bucket Cloud Storage para PDFs
# 5. Configura Secret Manager
# 6. Despliega backend y frontend en Cloud Run
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Variables ──
PROJECT_ID="magia"
REGION="us-central1"
DB_INSTANCE="mag-db"
DB_NAME="mag_sistema"
DB_USER="mag_user"
DB_PASS="$(openssl rand -base64 24)"  # Genera password seguro
BUCKET="magia-docs"

echo "═══════════════════════════════════════════"
echo "  MAG Sistema — Setup GCP (Proyecto: $PROJECT_ID)"
echo "═══════════════════════════════════════════"

# ── Paso 0: Crear proyecto ──
echo ""
echo "🔧 Paso 0: Configurando proyecto..."
gcloud projects create $PROJECT_ID --name="MAG Sistema" 2>/dev/null || echo "Proyecto ya existe"
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# ── Paso 1: Habilitar APIs ──
echo ""
echo "🔌 Paso 1: Habilitando APIs..."
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com \
  containerregistry.googleapis.com

# ── Paso 2: Cloud SQL (PostgreSQL) ──
echo ""
echo "🗄️  Paso 2: Creando Cloud SQL (PostgreSQL)..."
gcloud sql instances create $DB_INSTANCE \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --storage-size=10GB \
  --storage-auto-increase \
  --backup-start-time=04:00 \
  --availability-type=zonal \
  --deletion-protection 2>/dev/null || echo "Instancia ya existe"

gcloud sql databases create $DB_NAME \
  --instance=$DB_INSTANCE 2>/dev/null || echo "BD ya existe"

gcloud sql users create $DB_USER \
  --instance=$DB_INSTANCE \
  --password="$DB_PASS" 2>/dev/null || echo "Usuario ya existe"

# Guardar password en Secret Manager
DB_URL="postgresql://$DB_USER:$DB_PASS@/$DB_NAME?host=/cloudsql/$PROJECT_ID:$REGION:$DB_INSTANCE"
echo -n "$DB_URL" | gcloud secrets create mag-db-url --data-file=- 2>/dev/null || \
  echo -n "$DB_URL" | gcloud secrets versions add mag-db-url --data-file=-

echo "  ✅ Cloud SQL creado: $DB_INSTANCE"
echo "  📋 DATABASE_URL guardado en Secret Manager: mag-db-url"

# ── Paso 3: Cloud Storage ──
echo ""
echo "📁 Paso 3: Creando bucket Cloud Storage..."
gsutil mb -l $REGION gs://$BUCKET/ 2>/dev/null || echo "Bucket ya existe"
echo "  ✅ Bucket: gs://$BUCKET/"

# ── Paso 4: Build & Deploy Backend ──
echo ""
echo "🐍 Paso 4: Construyendo y desplegando Backend..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/mag-api .

# Obtener connection name de Cloud SQL
CONN_NAME="$PROJECT_ID:$REGION:$DB_INSTANCE"

gcloud run deploy mag-api \
  --image gcr.io/$PROJECT_ID/mag-api:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 5 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --add-cloudsql-instances $CONN_NAME \
  --set-env-vars "DEMO_MODE=false,PYTHONUTF8=1" \
  --set-secrets "DATABASE_URL=mag-db-url:latest"

# Obtener URL del backend
API_URL=$(gcloud run services describe mag-api --region $REGION --format='value(status.url)')
echo "  ✅ Backend desplegado: $API_URL"

# Guardar frontend URL secret
echo -n "$API_URL" | gcloud secrets create mag-api-url --data-file=- 2>/dev/null || \
  echo -n "$API_URL" | gcloud secrets versions add mag-api-url --data-file=-

# ── Paso 5: Build & Deploy Frontend ──
echo ""
echo "⚛️  Paso 5: Construyendo y desplegando Frontend..."
cd sistema
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/mag-frontend \
  --substitutions "_NEXT_PUBLIC_API_URL=$API_URL"

gcloud run deploy mag-frontend \
  --image gcr.io/$PROJECT_ID/mag-frontend:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 3 \
  --memory 256Mi \
  --cpu 1
cd ..

FRONTEND_URL=$(gcloud run services describe mag-frontend --region $REGION --format='value(status.url)')
echo "  ✅ Frontend desplegado: $FRONTEND_URL"

# ── Paso 6: Configurar CORS ──
echo ""
echo "🔒 Paso 6: Configurando CORS..."
gcloud run services update mag-api \
  --region $REGION \
  --update-env-vars "FRONTEND_URL=$FRONTEND_URL"

# ── Resumen ──
echo ""
echo "═══════════════════════════════════════════"
echo "  ✅ MIGRACIÓN COMPLETADA"
echo "═══════════════════════════════════════════"
echo ""
echo "  🌐 Frontend : $FRONTEND_URL"
echo "  🔌 API      : $API_URL"
echo "  📚 API Docs : $API_URL/docs"
echo "  🗄️  Cloud SQL: $PROJECT_ID:$REGION:$DB_INSTANCE"
echo "  📁 Storage  : gs://$BUCKET/"
echo ""
echo "  ⚠️  No olvides:"
echo "  1. Vincular billing: gcloud billing accounts list"
echo "  2. Importar datos: POST $API_URL/importar/excel-polizas"
echo "  3. Subir PDFs a gs://$BUCKET/"
echo ""
echo "  🔑 DB Password (guardar en lugar seguro): $DB_PASS"
echo "═══════════════════════════════════════════"
