# ═══════════════════════════════════════════════════════════════════
# axa.tfvars — Configuración para AXA Seguros
# ═══════════════════════════════════════════════════════════════════
# Uso: terraform apply -var-file="tenants/axa.tfvars"

tenant              = "axa"
tenant_display_name = "AXA Seguros"
tenant_ramos        = ["Vida Individual", "GMM Individual"]

# Recursos
db_tier     = "db-f1-micro"
db_storage_gb = 10

backend_memory        = "512Mi"
backend_cpu           = "1"
backend_min_instances = 0
backend_max_instances = 5

frontend_memory        = "256Mi"
frontend_min_instances = 0
frontend_max_instances = 3

# Configuración
demo_mode    = false
doc_base_url = "http://54.184.22.19:7070/cartera-0.1/static/archivos"

# Dominios personalizados (opcional)
# custom_domain_frontend = "axa.mag-sistema.com"
# custom_domain_api      = "api-axa.mag-sistema.com"
