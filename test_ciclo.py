"""
Script de prueba para ejecutar un ciclo del scheduler sin esperar.
Útil para probar alertas sin esperar al próximo minuto.
"""

from main import AlertScheduler

def main():
    """Ejecuta un ciclo de prueba del scheduler."""
    print("🧪 Ejecutando ciclo de prueba...\n")
    
    scheduler = AlertScheduler()
    scheduler.ejecutar_ciclo()
    
    print("\n✅ Ciclo de prueba completado")

if __name__ == "__main__":
    main()
