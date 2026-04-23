import os
import sys
import subprocess

# Agregar el directorio raíz al path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_script(script_name):
    path = os.path.join(BASE_DIR, "scripts", script_name)
    print(f"\n{'='*60}")
    print(f"▶️ Ejecutando: {script_name}")
    print(f"{'='*60}")
    
    try:
        # Usar el mismo intérprete de python que está corriendo este script
        subprocess.run([sys.executable, path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar {script_name}: {e}")
        return False
    return True

def main():
    print("🌟 Iniciando Pipeline de Importación Oracle (MAG Sistema) 🌟")
    
    scripts = [
        "importar_maestro_polizas.py",
        "importar_pagtotal_oracle.py",
        "importar_solicitudes_oracle.py",
        "reprocesar_reglas_mag.py"
    ]
    
    success = True
    for s in scripts:
        if not run_script(s):
            success = False
            print(f"⚠️ El pipeline se detuvo o tuvo errores en {s}")
            # Decidir si continuar o no. Por ahora seguimos.
    
    if success:
        print(f"\n{'='*60}")
        print("✅ PIPELINE FINALIZADO EXITOSAMENTE")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print("❌ PIPELINE FINALIZADO CON ERRORES")
        print(f"{'='*60}")

if __name__ == "__main__":
    main()
