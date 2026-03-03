# ═══════════════════════════════════════════════════════════════════
# setup_gcp.ps1 — Provisión del proyecto 'magia' en Google Cloud
# MAG Sistema — Promotoría MAG · AXA Seguros México
# ═══════════════════════════════════════════════════════════════════
#
# Uso: powershell -ExecutionPolicy Bypass -File infra\setup_gcp.ps1
# Prerequisito: gcloud CLI instalado y autenticado (gcloud auth login)
# ═══════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Continue"

# ── Variables ──
$PROJECT_ID = "magia"
$REGION = "us-central1"
$DB_INSTANCE = "mag-db"
$DB_NAME = "mag_sistema"
$DB_USER = "mag_user"
$BUCKET = "magia-docs"

Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  MAG Sistema — Setup GCP (Proyecto: $PROJECT_ID)" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan

# ── Paso 0: Login y proyecto ──
Write-Host ""
Write-Host "🔐 Paso 0: Verificando autenticación..." -ForegroundColor Yellow
$account = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
if (-not $account) {
    Write-Host "  No hay sesión activa. Abriendo login..." -ForegroundColor Red
    gcloud auth login
}
Write-Host "  ✅ Autenticado como: $account" -ForegroundColor Green

Write-Host ""
Write-Host "🔧 Paso 0b: Configurando proyecto..." -ForegroundColor Yellow
gcloud projects create $PROJECT_ID --name="MAG Sistema" 2>$null
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION
Write-Host "  ✅ Proyecto: $PROJECT_ID" -ForegroundColor Green

# ── Paso 1: Habilitar APIs ──
Write-Host ""
Write-Host "🔌 Paso 1: Habilitando APIs..." -ForegroundColor Yellow
$apis = @(
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "storage.googleapis.com",
    "containerregistry.googleapis.com"
)
gcloud services enable $apis
Write-Host "  ✅ APIs habilitadas" -ForegroundColor Green

# ── Paso 2: Cloud SQL (PostgreSQL) ──
Write-Host ""
Write-Host "🗄️  Paso 2: Creando Cloud SQL (PostgreSQL)..." -ForegroundColor Yellow
Write-Host "  ⏳ Esto puede tardar 3-5 minutos..." -ForegroundColor DarkGray

gcloud sql instances create $DB_INSTANCE `
    --database-version=POSTGRES_15 `
    --tier=db-f1-micro `
    --region=$REGION `
    --storage-size=10GB `
    --storage-auto-increase `
    --backup-start-time=04:00 `
    --availability-type=zonal 2>$null

gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE 2>$null

# Generar password
$DB_PASS = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 24 | ForEach-Object {[char]$_})
gcloud sql users create $DB_USER --instance=$DB_INSTANCE --password="$DB_PASS" 2>$null

# Guardar en Secret Manager
$DB_URL = "postgresql://${DB_USER}:${DB_PASS}@/${DB_NAME}?host=/cloudsql/${PROJECT_ID}:${REGION}:${DB_INSTANCE}"
$DB_URL | gcloud secrets create mag-db-url --data-file=- 2>$null

Write-Host "  ✅ Cloud SQL: $DB_INSTANCE" -ForegroundColor Green
Write-Host "  🔑 Password guardado en Secret Manager" -ForegroundColor Green

# ── Paso 3: Cloud Storage ──
Write-Host ""
Write-Host "📁 Paso 3: Creando bucket Cloud Storage..." -ForegroundColor Yellow
gsutil mb -l $REGION "gs://${BUCKET}/" 2>$null
Write-Host "  ✅ Bucket: gs://$BUCKET/" -ForegroundColor Green

# ── Paso 4: Build Backend ──
Write-Host ""
Write-Host "🐍 Paso 4: Construyendo Backend..." -ForegroundColor Yellow
Write-Host "  ⏳ Build puede tardar 2-3 minutos..." -ForegroundColor DarkGray
gcloud builds submit --tag "gcr.io/$PROJECT_ID/mag-api" .

$CONN_NAME = "${PROJECT_ID}:${REGION}:${DB_INSTANCE}"

gcloud run deploy mag-api `
    --image "gcr.io/$PROJECT_ID/mag-api:latest" `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --min-instances 0 `
    --max-instances 5 `
    --memory 512Mi `
    --cpu 1 `
    --timeout 60 `
    --add-cloudsql-instances $CONN_NAME `
    --set-env-vars "DEMO_MODE=false,PYTHONUTF8=1" `
    --set-secrets "DATABASE_URL=mag-db-url:latest"

$API_URL = gcloud run services describe mag-api --region $REGION --format="value(status.url)"
Write-Host "  ✅ Backend: $API_URL" -ForegroundColor Green

# ── Paso 5: Build Frontend ──
Write-Host ""
Write-Host "⚛️  Paso 5: Construyendo Frontend..." -ForegroundColor Yellow
Push-Location sistema
gcloud builds submit `
    --tag "gcr.io/$PROJECT_ID/mag-frontend" `
    --substitutions "_NEXT_PUBLIC_API_URL=$API_URL"

gcloud run deploy mag-frontend `
    --image "gcr.io/$PROJECT_ID/mag-frontend:latest" `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --min-instances 0 `
    --max-instances 3 `
    --memory 256Mi `
    --cpu 1
Pop-Location

$FRONTEND_URL = gcloud run services describe mag-frontend --region $REGION --format="value(status.url)"
Write-Host "  ✅ Frontend: $FRONTEND_URL" -ForegroundColor Green

# ── Paso 6: Configurar CORS ──
Write-Host ""
Write-Host "🔒 Paso 6: Configurando CORS..." -ForegroundColor Yellow
gcloud run services update mag-api `
    --region $REGION `
    --update-env-vars "FRONTEND_URL=$FRONTEND_URL"
Write-Host "  ✅ CORS configurado" -ForegroundColor Green

# ── Resumen ──
Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ MIGRACIÓN COMPLETADA — Proyecto: $PROJECT_ID" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  🌐 Frontend : $FRONTEND_URL" -ForegroundColor White
Write-Host "  🔌 API      : $API_URL" -ForegroundColor White
Write-Host "  📚 API Docs : $API_URL/docs" -ForegroundColor White
Write-Host "  🗄️  Cloud SQL: ${PROJECT_ID}:${REGION}:${DB_INSTANCE}" -ForegroundColor White
Write-Host "  📁 Storage  : gs://$BUCKET/" -ForegroundColor White
Write-Host ""
Write-Host "  ⚠️  Próximos pasos:" -ForegroundColor Yellow
Write-Host "  1. Vincular billing: gcloud billing accounts list" -ForegroundColor DarkGray
Write-Host "  2. Importar datos: POST $API_URL/importar/excel-polizas" -ForegroundColor DarkGray
Write-Host "  3. Subir PDFs: gsutil cp *.pdf gs://$BUCKET/polizas/" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  🔑 DB Password: $DB_PASS" -ForegroundColor Red
Write-Host "  (Guardar en lugar seguro y borrar de la terminal)" -ForegroundColor DarkGray
Write-Host ""
