# ═══════════════════════════════════════════════════════════════════
# outputs.tf — URLs y datos de salida por tenant
# ═══════════════════════════════════════════════════════════════════

output "tenant" {
  description = "Identificador del tenant"
  value       = local.tenant
}

output "tenant_display_name" {
  description = "Nombre comercial de la aseguradora"
  value       = var.tenant_display_name
}

output "frontend_url" {
  description = "URL del frontend"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "api_url" {
  description = "URL del API backend"
  value       = google_cloud_run_v2_service.backend.uri
}

output "api_docs_url" {
  description = "URL de la documentación Swagger"
  value       = "${google_cloud_run_v2_service.backend.uri}/docs"
}

output "db_instance" {
  description = "Nombre de la instancia Cloud SQL"
  value       = google_sql_database_instance.db.name
}

output "db_connection_name" {
  description = "Connection name para Cloud SQL proxy"
  value       = local.conn_name
}

output "docs_bucket" {
  description = "Bucket de documentos PDF"
  value       = google_storage_bucket.docs.name
}

output "summary" {
  description = "Resumen completo del tenant"
  value = <<-EOT

  ═══════════════════════════════════════════════════
    MAG Sistema — ${var.tenant_display_name}
    Tenant: ${local.tenant}
  ═══════════════════════════════════════════════════

    🌐 Frontend  : ${google_cloud_run_v2_service.frontend.uri}
    🔌 API       : ${google_cloud_run_v2_service.backend.uri}
    📚 Swagger   : ${google_cloud_run_v2_service.backend.uri}/docs
    🗄️  Cloud SQL : ${local.db_instance} (${var.db_tier})
    📁 Docs      : gs://${local.bucket_name}/

  EOT
}
