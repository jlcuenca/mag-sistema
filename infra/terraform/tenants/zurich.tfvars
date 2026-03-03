# ═══════════════════════════════════════════════════════════════════
# zurich.tfvars — Configuración para Zurich Seguros (Ejemplo)
# ═══════════════════════════════════════════════════════════════════
# Uso: terraform workspace new zurich
#      terraform apply -var-file="tenants/zurich.tfvars"

tenant              = "zurich"
tenant_display_name = "Zurich Seguros"
tenant_ramos        = ["Vida Individual", "GMM Colectivo"]

db_tier     = "db-f1-micro"
db_storage_gb = 10

backend_memory        = "512Mi"
backend_cpu           = "1"
backend_min_instances = 0
backend_max_instances = 3

frontend_memory        = "256Mi"
frontend_min_instances = 0
frontend_max_instances = 2

demo_mode    = true
doc_base_url = ""
