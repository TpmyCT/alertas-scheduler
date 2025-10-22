"""
Scheduler de Alertas - Punto de entrada principal.

Este script orquesta el sistema de alertas programadas, conectando los diferentes
módulos para configurar, programar y ejecutar alertas automáticamente.

Módulos utilizados:
- database_config: Configuración y conexión a la base de datos
- webhook_sender: Envío de webhooks y registro de resultados
- alert_scheduler: Programación de alertas con diferentes frecuencias
- alert_loader: Carga y monitoreo de alertas desde la base de datos
"""

import time
import os
from datetime import datetime

from database_config import DatabaseConfig
from webhook_sender import WebhookSender
from alert_scheduler import AlertScheduler
from alert_loader import AlertLoader


def limpiar_pantalla():
    """Limpia la pantalla de la consola."""
    os.system('cls' if os.name == 'nt' else 'clear')


def inicializar_sistema():
    """
    Inicializa todos los componentes del sistema de alertas.
    
    Returns:
        tuple: (db_config, webhook_sender, alert_scheduler, alert_loader)
    """
    print("🚀 INICIANDO SCHEDULER DE ALERTAS")
    
    # Configurar conexión a base de datos
    try:
        db_config = DatabaseConfig()
        conn = db_config.connect()
        print("💫 Conectado a la base de datos")
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
        exit(1)
    
    # Inicializar componentes
    webhook_sender = WebhookSender(conn)
    alert_scheduler = AlertScheduler(webhook_sender)
    alert_loader = AlertLoader(conn, alert_scheduler)
    
    # Iniciar scheduler
    alert_scheduler.iniciar()
    print("⚡ Programador automático activado")
    
    return db_config, webhook_sender, alert_scheduler, alert_loader


def ejecutar_ciclo_principal(alert_loader):
    """
    Ejecuta el ciclo principal de monitoreo del sistema.
    
    Args:
        alert_loader: Instancia de AlertLoader para verificar cambios
    """
    print("\n🔄 MODO MONITOREO ACTIVADO")
    print("   El sistema revisa nuevas alertas cada minuto...")
    print("   Presiona Ctrl+C para detener\n")
    
    try:
        while True:
            alert_loader.verificar_cambios()
            time.sleep(60)  # Esperar 1 minuto antes de la próxima verificación
    except KeyboardInterrupt:
        print("\n\n� SCHEDULER DETENIDO")
        print("   ¡Hasta luego!")


def main():
    """Función principal que orquesta todo el sistema."""
    # Limpiar pantalla al inicio
    limpiar_pantalla()
    
    # Inicializar sistema
    db_config, webhook_sender, alert_scheduler, alert_loader = inicializar_sistema()
    
    try:
        # Cargar alertas iniciales
        alert_loader.cargar_alertas()
        
        # Ejecutar ciclo principal de monitoreo
        ejecutar_ciclo_principal(alert_loader)
        
    except Exception as e:
        print(f"❌ Error crítico en el sistema: {e}")
    finally:
        # Limpiar recursos
        alert_scheduler.detener()
        db_config.close_connection()


if __name__ == "__main__":
    main()


