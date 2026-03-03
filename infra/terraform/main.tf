# ═══════════════════════════════════════════════════════════════════
# Terraform — MAG Sistema Multi-Aseguradora
# Proyecto GCP: magia-mag
#
# CONCEPTO:
# Cada aseguradora (AXA, GNP, Zurich, Chubb, etc.) obtiene su propia
# instancia aislada del sistema con:
#   - Su propia base de datos Cloud SQL
#   - Su propio backend Cloud Run
#   - Su propio frontend Cloud Run
#   - Su propio bucket de documentos
#
# BENEFICIO: Datos 100% aislados entre aseguradoras.
# COSTO: ~$7-20 USD/mes por instancia adicional
#
# USO:
#   terraform init
#   terraform plan -var="tenant=axa"
#   terraform apply -var="tenant=axa"
#
#   # Crear otra instancia para GNP:
#   terraform workspace new gnp
#   terraform apply -var="tenant=gnp" -var="tenant_display_name=GNP Seguros"
# ═══════════════════════════════════════════════════════════════════

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Backend remoto para estado compartido (recomendado)
  backend "gcs" {
    bucket = "magia-terraform-state"
    prefix = "terraform/state"
  }
}

# ── Provider ──
provider "google" {
  project = var.project_id
  region  = var.region
}
