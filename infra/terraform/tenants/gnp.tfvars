# ═══════════════════════════════════════════════════════════════════
# gnp.tfvars — Configuración para GNP Seguros (Ejemplo)
# ═══════════════════════════════════════════════════════════════════
# Uso: terraform workspace new gnp
#      terraform apply -var-file="tenants/gnp.tfvars"

tenant              = "gnp"
tenant_display_name = "GNP Seguros"
tenant_ramos        = ["Vida Individual", "GMM Individual", "Automóviles"]

# Recursos (puede ajustarse según volumen de cada aseguradora)
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
demo_mode    = true   # Empezar con datos demo
doc_base_url = ""     # Se configura cuando se tenga el servidor de docs

# Dominios personalizados (opcional)
# custom_domain_frontend = "gnp.mag-sistema.com"
# custom_domain_api      = "api-gnp.mag-sistema.com"
