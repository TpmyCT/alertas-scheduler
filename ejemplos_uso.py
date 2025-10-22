"""
Ejemplos de uso de los módulos del sistema de alertas.

Este archivo demuestra cómo utilizar cada módulo de forma independiente
para tareas específicas o testing.
"""

from database_config import DatabaseConfig
from webhook_sender import WebhookSender
from alert_scheduler import AlertScheduler
from alert_loader import AlertLoader


def ejemplo_conexion_bd():
    """Ejemplo de cómo usar DatabaseConfig para conectar a la base de datos."""
    print("=== Ejemplo: Conexión a Base de Datos ===")
    
    try:
        # Crear configuración
        db_config = DatabaseConfig()
        
        # Establecer conexión
        conn = db_config.connect()
        print("✅ Conexión exitosa")
        
        # Usar la conexión para una consulta simple
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM ct_alertas_configuracion")
            count = cur.fetchone()[0]
            print(f"📊 Total de alertas en BD: {count}")
        
        # Cerrar conexión
        db_config.close_connection()
        print("✅ Conexión cerrada")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def ejemplo_envio_webhook():
    """Ejemplo de cómo usar WebhookSender para enviar un webhook."""
    print("\n=== Ejemplo: Envío de Webhook ===")
    
    try:
        # Configurar base de datos
        db_config = DatabaseConfig()
        conn = db_config.connect()
        
        # Crear sender
        webhook_sender = WebhookSender(conn)
        
        # Enviar webhook de prueba (cambia el webhook_id por uno real)
        webhook_id = "tu-webhook-id-aqui"
        alerta_id = 999  # ID de prueba
        
        exito, mensaje = webhook_sender.enviar_webhook(webhook_id, alerta_id)
        
        if exito:
            print(f"✅ Webhook enviado: {mensaje}")
        else:
            print(f"❌ Error en webhook: {mensaje}")
        
        # Registrar resultado
        webhook_sender.registrar_ejecucion(alerta_id, mensaje)
        
        db_config.close_connection()
        
    except Exception as e:
        print(f"❌ Error: {e}")


def ejemplo_programacion_alerta():
    """Ejemplo de cómo usar AlertScheduler para programar una alerta."""
    print("\n=== Ejemplo: Programación de Alerta ===")
    
    try:
        # Configurar base de datos y webhook sender
        db_config = DatabaseConfig()
        conn = db_config.connect()
        webhook_sender = WebhookSender(conn)
        
        # Crear scheduler
        alert_scheduler = AlertScheduler(webhook_sender)
        alert_scheduler.iniciar()
        
        # Alerta de ejemplo (diaria a las 09:00)
        alerta_ejemplo = {
            "id": 999,
            "frecuencia": "DIARIO",
            "hora_envio": "09:00",
            "webhook_id": "tu-webhook-id-aqui",
            "dias_semana": None,
            "dias_mes": None
        }
        
        # Programar la alerta
        resultado = alert_scheduler.programar_alerta(alerta_ejemplo)
        
        if resultado:
            print("✅ Alerta programada correctamente")
        else:
            print("❌ Error al programar alerta")
        
        # Limpiar y cerrar
        alert_scheduler.detener()
        db_config.close_connection()
        
    except Exception as e:
        print(f"❌ Error: {e}")


def ejemplo_carga_alertas():
    """Ejemplo de cómo usar AlertLoader para cargar alertas desde BD."""
    print("\n=== Ejemplo: Carga de Alertas ===")
    
    try:
        # Configurar componentes
        db_config = DatabaseConfig()
        conn = db_config.connect()
        webhook_sender = WebhookSender(conn)
        alert_scheduler = AlertScheduler(webhook_sender)
        alert_scheduler.iniciar()
        
        # Crear loader
        alert_loader = AlertLoader(conn, alert_scheduler)
        
        # Cargar alertas
        estadisticas = alert_loader.cargar_alertas()
        
        print(f"\n📊 Estadísticas de carga:")
        print(f"   - Programadas: {estadisticas['programadas']}")
        print(f"   - Omitidas: {estadisticas['omitidas']}")
        print(f"   - Total: {estadisticas['total']}")
        
        # Limpiar y cerrar
        alert_scheduler.detener()
        db_config.close_connection()
        
    except Exception as e:
        print(f"❌ Error: {e}")


def ejemplo_validacion_alerta():
    """Ejemplo de cómo validar datos de una alerta."""
    print("\n=== Ejemplo: Validación de Alertas ===")
    
    # Configurar webhook sender (necesario para AlertScheduler)
    db_config = DatabaseConfig()
    conn = db_config.connect()
    webhook_sender = WebhookSender(conn)
    alert_scheduler = AlertScheduler(webhook_sender)
    
    # Alertas de prueba con diferentes configuraciones
    alertas_prueba = [
        {
            "id": 1,
            "frecuencia": "DIARIO",
            "hora_envio": "14:30",
            "webhook_id": "test-webhook",
            "dias_semana": None,
            "dias_mes": None
        },
        {
            "id": 2,
            "frecuencia": "SEMANAL",
            "hora_envio": "09:00",
            "webhook_id": "test-webhook",
            "dias_semana": "1,3,5",  # Lunes, Miércoles, Viernes
            "dias_mes": None
        },
        {
            "id": 3,
            "frecuencia": "MENSUAL",
            "hora_envio": "08:00",
            "webhook_id": "test-webhook",
            "dias_semana": None,
            "dias_mes": "1,15"  # Día 1 y 15 de cada mes
        },
        {
            "id": 4,
            "frecuencia": None,  # Error: sin frecuencia
            "hora_envio": "10:00",
            "webhook_id": "test-webhook",
            "dias_semana": None,
            "dias_mes": None
        }
    ]
    
    for alerta in alertas_prueba:
        es_valida, mensaje = alert_scheduler.validar_datos_alerta(alerta)
        estado = "✅ VÁLIDA" if es_valida else "❌ INVÁLIDA"
        print(f"Alerta #{alerta['id']}: {estado} - {mensaje}")
    
    db_config.close_connection()


if __name__ == "__main__":
    """
    Ejecuta todos los ejemplos.
    
    NOTA: Asegúrate de tener configurado el archivo .env
    antes de ejecutar estos ejemplos.
    """
    print("🚀 EJECUTANDO EJEMPLOS DE USO")
    print("=" * 50)
    
    # Ejecutar ejemplos (comenta los que no quieras ejecutar)
    ejemplo_conexion_bd()
    # ejemplo_envio_webhook()  # Comentado para evitar envíos reales
    # ejemplo_programacion_alerta()  # Comentado para evitar programación real
    ejemplo_carga_alertas()
    ejemplo_validacion_alerta()
    
    print("\n✅ EJEMPLOS COMPLETADOS")