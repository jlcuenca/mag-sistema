# ═══════════════════════════════════════════════════════════════════
# variables.tf — Variables de configuración por tenant/aseguradora
# ═══════════════════════════════════════════════════════════════════

variable "project_id" {
  description = "ID del proyecto GCP"
  type        = string
  default     = "magia-mag"
}

variable "region" {
  description = "Región GCP (us-central1 = Iowa, buena latencia para México)"
  type        = string
  default     = "us-central1"
}

# ── Tenant (Aseguradora) ──

variable "tenant" {
  description = "Identificador único del tenant/aseguradora (lowercase, sin espacios)"
  type        = string
  default     = "axa"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.tenant))
    error_message = "El tenant debe ser lowercase alfanumérico (ej: axa, gnp, zurich)"
  }
}

variable "tenant_display_name" {
  description = "Nombre comercial de la aseguradora (para UI)"
  type        = string
  default     = "AXA Seguros"
}

variable "tenant_ramos" {
  description = "Ramos que maneja esta aseguradora"
  type        = list(string)
  default     = ["Vida Individual", "GMM Individual"]
}

# ── Configuración de recursos ──

variable "db_tier" {
  description = "Tier de Cloud SQL (db-f1-micro=shared, db-g1-small=dedicado)"
  type        = string
  default     = "db-f1-micro"
}

variable "db_storage_gb" {
  description = "Almacenamiento inicial de Cloud SQL en GB"
  type        = number
  default     = 10
}

variable "backend_memory" {
  description = "Memoria del backend Cloud Run"
  type        = string
  default     = "512Mi"
}

variable "backend_cpu" {
  description = "CPUs del backend Cloud Run"
  type        = string
  default     = "1"
}

variable "backend_min_instances" {
  description = "Instancias mínimas del backend (0=escala a cero, 1=sin cold start)"
  type        = number
  default     = 0
}

variable "backend_max_instances" {
  description = "Instancias máximas del backend"
  type        = number
  default     = 5
}

variable "frontend_memory" {
  description = "Memoria del frontend Cloud Run"
  type        = string
  default     = "256Mi"
}

variable "frontend_min_instances" {
  description = "Instancias mínimas del frontend"
  type        = number
  default     = 0
}

variable "frontend_max_instances" {
  description = "Instancias máximas del frontend"
  type        = number
  default     = 3
}

variable "demo_mode" {
  description = "Si true, inserta datos de demo al arrancar"
  type        = bool
  default     = true
}

variable "doc_base_url" {
  description = "URL base del servidor de documentos PDF"
  type        = string
  default     = ""
}

variable "custom_domain_frontend" {
  description = "Dominio personalizado para el frontend (opcional)"
  type        = string
  default     = ""
}

variable "custom_domain_api" {
  description = "Dominio personalizado para el API (opcional)"
  type        = string
  default     = ""
}

# ── GitHub (para Cloud Build triggers) ──

variable "github_owner" {
  description = "Owner del repositorio GitHub"
  type        = string
  default     = "jlcuenca"
}

variable "github_repo" {
  description = "Nombre del repositorio GitHub"
  type        = string
  default     = "mag-sistema"
}
