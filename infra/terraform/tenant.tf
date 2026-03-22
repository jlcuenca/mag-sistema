# ═══════════════════════════════════════════════════════════════════
# tenant.tf — Recursos por tenant/aseguradora
#
# Cada apply de este módulo crea una instancia completa y aislada:
#   1. Cloud SQL PostgreSQL (mag-{tenant}-db)
#   2. Secret Manager (DATABASE_URL)
#   3. Cloud Run Backend (mag-api-{tenant})
#   4. Cloud Run Frontend (mag-{tenant})
#   5. Cloud Storage bucket (magia-docs-{tenant})
# ═══════════════════════════════════════════════════════════════════

locals {
  tenant         = var.tenant
  name_prefix    = "mag-${local.tenant}"
  db_instance    = "${local.name_prefix}-db"
  db_name        = "mag_${replace(local.tenant, "-", "_")}"
  db_user        = "mag_user"
  backend_name   = "mag-api-${local.tenant}"
  frontend_name  = "mag-${local.tenant}"
  bucket_name    = "magia-docs-${local.tenant}"
  secret_db_url  = "mag-db-url-${local.tenant}"
  conn_name      = "${var.project_id}:${var.region}:${local.db_instance}"

  # Ramos como string separado por comas (para env var)
  tenant_ramos_str = join(",", var.tenant_ramos)
}

# ── 1. Password de BD (generado automáticamente) ──
resource "random_password" "db_password" {
  length  = 32
  special = false
}

# ── 2. Cloud SQL (PostgreSQL 15) ──
resource "google_sql_database_instance" "db" {
  name             = local.db_instance
  database_version = "POSTGRES_15"
  region           = var.region
  project          = var.project_id

  deletion_protection = true

  settings {
    tier              = var.db_tier
    disk_size         = var.db_storage_gb
    disk_autoresize   = true
    availability_type = "ZONAL"

    backup_configuration {
      enabled                        = true
      start_time                     = "04:00"
      point_in_time_recovery_enabled = false
      backup_retention_settings {
        retained_backups = 7
      }
    }

    ip_configuration {
      ipv4_enabled = true
    }

    user_labels = {
      tenant      = local.tenant
      app         = "mag-sistema"
      environment = var.demo_mode ? "demo" : "production"
    }
  }
}

resource "google_sql_database" "db" {
  name     = local.db_name
  instance = google_sql_database_instance.db.name
  project  = var.project_id
}

resource "google_sql_user" "db_user" {
  name     = local.db_user
  instance = google_sql_database_instance.db.name
  password = random_password.db_password.result
  project  = var.project_id
}

# ── 3. Secret Manager (DATABASE_URL) ──
resource "google_secret_manager_secret" "db_url" {
  secret_id = local.secret_db_url
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    tenant = local.tenant
    app    = "mag-sistema"
  }
}

resource "google_secret_manager_secret_version" "db_url" {
  secret      = google_secret_manager_secret.db_url.id
  secret_data = "postgresql+psycopg2://${local.db_user}:${random_password.db_password.result}@/${local.db_name}?host=/cloudsql/${local.conn_name}"
}

# Permitir que Cloud Run lea el secreto
data "google_project" "current" {
  project_id = var.project_id
}

resource "google_secret_manager_secret_iam_member" "cloud_run_access" {
  secret_id = google_secret_manager_secret.db_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

# ── 4. Cloud Run — Backend API (recurso ÚNICO, sin duplicado) ──
resource "google_cloud_run_v2_service" "backend" {
  name     = local.backend_name
  location = var.region
  project  = var.project_id

  template {
    scaling {
      min_instance_count = var.backend_min_instances
      max_instance_count = var.backend_max_instances
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [local.conn_name]
      }
    }

    containers {
      image = "gcr.io/${var.project_id}/mag-api:latest"

      resources {
        limits = {
          memory = var.backend_memory
          cpu    = var.backend_cpu
        }
      }

      # ── Tenant config ──
      env {
        name  = "TENANT"
        value = local.tenant
      }

      env {
        name  = "TENANT_DISPLAY_NAME"
        value = var.tenant_display_name
      }

      env {
        name  = "TENANT_RAMOS"
        value = local.tenant_ramos_str
      }

      # ── App config ──
      env {
        name  = "DEMO_MODE"
        value = var.demo_mode ? "true" : "false"
      }

      env {
        name  = "PYTHONUTF8"
        value = "1"
      }

      env {
        name  = "ENVIRONMENT"
        value = var.demo_mode ? "demo" : "production"
      }

      env {
        name  = "DOCS_BUCKET"
        value = local.bucket_name
      }

      env {
        name  = "DOC_BASE_URL"
        value = var.doc_base_url
      }

      # FRONTEND_URL se actualiza con null_resource después del frontend deploy
      env {
        name  = "FRONTEND_URL"
        value = ""
      }

      # ── Database ──
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_url.secret_id
            version = "latest"
          }
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      ports {
        container_port = 8080
      }

      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 5
        period_seconds        = 5
        failure_threshold     = 3
      }
    }
  }

  depends_on = [
    google_sql_database.db,
    google_sql_user.db_user,
    google_secret_manager_secret_version.db_url,
  ]
}

# Hacer el backend público (sin auth)
resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  project  = var.project_id
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── 5. Cloud Run — Frontend ──
resource "google_cloud_run_v2_service" "frontend" {
  name     = local.frontend_name
  location = var.region
  project  = var.project_id

  template {
    scaling {
      min_instance_count = var.frontend_min_instances
      max_instance_count = var.frontend_max_instances
    }

    containers {
      image = "gcr.io/${var.project_id}/mag-frontend-${local.tenant}:latest"

      resources {
        limits = {
          memory = var.frontend_memory
          cpu    = "1"
        }
      }

      env {
        name  = "TENANT"
        value = local.tenant
      }

      ports {
        container_port = 3000
      }
    }
  }

  depends_on = [
    google_cloud_run_v2_service.backend,
  ]
}

# Hacer el frontend público
resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  name     = google_cloud_run_v2_service.frontend.name
  location = var.region
  project  = var.project_id
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── 6. Cloud Storage — Documentos PDF ──
resource "google_storage_bucket" "docs" {
  name          = local.bucket_name
  location      = var.region
  project       = var.project_id
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  labels = {
    tenant      = local.tenant
    environment = var.demo_mode ? "demo" : "production"
    app         = "mag-sistema"
  }
}

# ── 7. Actualizar CORS del backend con URL del frontend ──
# Usa gcloud CLI para update in-place sin duplicar el recurso
resource "null_resource" "backend_cors_update" {
  triggers = {
    frontend_uri = google_cloud_run_v2_service.frontend.uri
  }

  provisioner "local-exec" {
    command = <<-EOT
      gcloud run services update ${local.backend_name} \
        --region=${var.region} \
        --project=${var.project_id} \
        --update-env-vars="FRONTEND_URL=${google_cloud_run_v2_service.frontend.uri}"
    EOT
  }

  depends_on = [
    google_cloud_run_v2_service.backend,
    google_cloud_run_v2_service.frontend,
  ]
}
