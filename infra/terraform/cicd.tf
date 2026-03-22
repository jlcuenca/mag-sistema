# ═══════════════════════════════════════════════════════════════════
# cicd.tf — Cloud Build triggers per-tenant
#
# Cada tenant tiene su propio trigger que:
#   1. Re-builda las imágenes Docker (backend + frontend)
#   2. Despliega a los Cloud Run services de ese tenant
#
# El trigger se activa con push a main, pero despliega solo
# a los servicios del tenant (no afecta otros tenants).
# ═══════════════════════════════════════════════════════════════════

# ── Cloud Build trigger per-tenant ──
resource "google_cloudbuild_trigger" "deploy_tenant" {
  name     = "deploy-${local.tenant}"
  project  = var.project_id
  location = var.region

  description = "Build & deploy MAG Sistema para ${var.tenant_display_name}"

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "^main$"
    }
  }

  substitutions = {
    _TENANT        = local.tenant
    _BACKEND_NAME  = local.backend_name
    _FRONTEND_NAME = local.frontend_name
    _API_URL       = google_cloud_run_v2_service.backend.uri
    _REGION        = var.region
  }

  filename = "cloudbuild-tenant.yaml"

  included_files = [
    "api/**",
    "main.py",
    "requirements.txt",
    "Dockerfile",
    "sistema/**",
    "cloudbuild-tenant.yaml",
  ]

  tags = [
    "tenant-${local.tenant}",
    "mag-sistema",
  ]
}

# ── Service Account para Cloud Build (opcional, más seguro) ──
# Descomenta si quieres un SA dedicado por tenant
#
# resource "google_service_account" "cloudbuild" {
#   account_id   = "mag-build-${local.tenant}"
#   display_name = "MAG Build - ${var.tenant_display_name}"
#   project      = var.project_id
# }
#
# resource "google_project_iam_member" "cloudbuild_run" {
#   project = var.project_id
#   role    = "roles/run.developer"
#   member  = "serviceAccount:${google_service_account.cloudbuild.email}"
# }
