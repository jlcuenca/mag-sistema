# deploy.ps1 — Script de despliegue MAG Sistema Demo
# Ejecutar en PowerShell como: .\deploy.ps1
# Requiere: Node.js instalado (ya está), Python 3.12 (ya está)
#
# Resultado:
#   Backend  → https://mag-api-XXXX.onrender.com
#   Frontend → https://mag-sistema-XXXX.vercel.app

param(
    [string]$RenderApiUrl = ""   # Se llena automáticamente o se pasa como argumento
)

$ErrorActionPreference = "Stop"
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   MAG Sistema — Script de Despliegue Demo" -ForegroundColor Cyan
Write-Host "   FastAPI (Render) + Next.js (Vercel)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ──────────────────────────────────────────────────────────────────
# PASO 1: Crear ZIP del backend para Render
# ──────────────────────────────────────────────────────────────────
Write-Host "PASO 1/3: Preparando backend para Render..." -ForegroundColor Yellow

$backendZip = "C:\Users\jlcue\Documents\mag\mag-backend.zip"
$backendSrc = "C:\Users\jlcue\Documents\mag"

# Eliminar ZIP anterior si existe
if (Test-Path $backendZip) { Remove-Item $backendZip }

# Crear ZIP excluyendo carpetas innecesarias
Add-Type -AssemblyName System.IO.Compression.FileSystem
$comprimir = [System.IO.Compression.ZipFile]

$tmp = [System.IO.Path]::GetTempPath() + "mag_backend_" + [System.Guid]::NewGuid().ToString()
New-Item -ItemType Directory -Path $tmp | Out-Null

# Copiar solo lo necesario
$incluir = @("main.py", "requirements.txt", "render.yaml", "api")
foreach ($item in $incluir) {
    $src = Join-Path $backendSrc $item
    $dst = Join-Path $tmp $item
    if (Test-Path $src -PathType Container) {
        Copy-Item $src $dst -Recurse
    } elseif (Test-Path $src) {
        Copy-Item $src $dst
    }
}

[System.IO.Compression.ZipFile]::CreateFromDirectory($tmp, $backendZip)
Remove-Item $tmp -Recurse -Force

$sizeMb = [math]::Round((Get-Item $backendZip).Length / 1MB, 2)
Write-Host "   Backend ZIP creado: $backendZip ($sizeMb MB)" -ForegroundColor Green
Write-Host ""

# ──────────────────────────────────────────────────────────────────
# PASO 2: Instrucciones para Render
# ──────────────────────────────────────────────────────────────────
Write-Host "PASO 2/3: Desplegar Backend en Render" -ForegroundColor Yellow
Write-Host ""
Write-Host "   1. Ve a: https://render.com" -ForegroundColor White
Write-Host "   2. Crea una cuenta o inicia sesion" -ForegroundColor White
Write-Host "   3. Click en [New +] -> [Web Service]" -ForegroundColor White
Write-Host "   4. Selecciona 'Deploy from ZIP file'" -ForegroundColor White
Write-Host "   5. Sube el archivo: $backendZip" -ForegroundColor Cyan
Write-Host "   6. Configura:" -ForegroundColor White
Write-Host "      Name:          mag-api" -ForegroundColor DarkGray
Write-Host "      Runtime:       Python 3" -ForegroundColor DarkGray
Write-Host "      Build Command: pip install -r requirements.txt" -ForegroundColor DarkGray
Write-Host "      Start Command: uvicorn main:app --host 0.0.0.0 --port `$PORT" -ForegroundColor DarkGray
Write-Host "      Plan:          Free" -ForegroundColor DarkGray
Write-Host "   7. En Environment Variables agrega:" -ForegroundColor White
Write-Host "      DEMO_MODE=true" -ForegroundColor DarkGray
Write-Host "      PYTHONUTF8=1" -ForegroundColor DarkGray
Write-Host "   8. Click [Create Web Service] y espera ~3 min" -ForegroundColor White
Write-Host ""

if ($RenderApiUrl -eq "") {
    $RenderApiUrl = Read-Host "   Cuando termine, pega aqui la URL de Render (ej: https://mag-api-xxxx.onrender.com)"
}

Write-Host ""
Write-Host "   URL del backend: $RenderApiUrl" -ForegroundColor Green

# ──────────────────────────────────────────────────────────────────
# PASO 3: Build y deploy del frontend en Vercel
# ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "PASO 3/3: Desplegando Frontend en Vercel..." -ForegroundColor Yellow

Set-Location "C:\Users\jlcue\Documents\mag\sistema"

# Guardar la URL del backend en el env local
"NEXT_PUBLIC_API_URL=$RenderApiUrl" | Out-File -FilePath ".env.local" -Encoding UTF8

# Build de produccion
Write-Host "   Construyendo Next.js para produccion..." -ForegroundColor White
$env:NEXT_PUBLIC_API_URL = $RenderApiUrl
& "C:\Program Files\nodejs\npm.cmd" run build

# Deploy con Vercel CLI
Write-Host ""
Write-Host "   Iniciando deploy en Vercel (se abrira el browser para autenticacion)..." -ForegroundColor White
Write-Host "   Si no tienes cuenta, crea una en https://vercel.com" -ForegroundColor DarkGray
Write-Host ""

& "C:\Program Files\nodejs\npx.cmd" -y vercel --prod `
    --name mag-sistema `
    --yes `
    --env "NEXT_PUBLIC_API_URL=$RenderApiUrl"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   DESPLIEGUE COMPLETADO" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "   Backend API:  $RenderApiUrl" -ForegroundColor Cyan
Write-Host "   API Docs:     $RenderApiUrl/docs" -ForegroundColor Cyan
Write-Host "   Frontend:     Ver URL de Vercel en la salida de arriba" -ForegroundColor Cyan
Write-Host ""
Write-Host "   NOTA: El tier gratuito de Render tiene cold start de ~30s" -ForegroundColor Yellow
Write-Host "   Si el dashboard tarda, espera un poco y refresca." -ForegroundColor Yellow
Write-Host ""
