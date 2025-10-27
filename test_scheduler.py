"""
Script de prueba del scheduler sin conexión a BD real.
Simula datos para probar la lógica de filtros y logging.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from main import AlertScheduler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class MockDatabaseConfig:
    """Simulador de base de datos para pruebas."""
    
    def connect(self):
        logger.info("🧪 Usando conexión simulada para pruebas")
        return MockConnection()

class MockConnection:
    """Conexión simulada."""
    
    def cursor(self):
        return MockCursor()
    
    def commit(self):
        pass
    
    def close(self):
        pass

class MockCursor:
    """Cursor simulado con datos de prueba."""
    
    def __init__(self):
        self.description = [
            ('config_id',), ('tipo_disparo',), ('frecuencia',), ('hora_envio',), 
            ('dias_semana',), ('dias_mes',), ('tipo_codigo',), ('tipo_descripcion',),
            ('empresa_codigo',), ('empresa_nombre',), ('empresa_conexion',),
            ('persona_codigo',), ('persona_nombre',), ('canal_codigo',), 
            ('canal_nombre',), ('webhook_url',), ('webhook_nombre',)
        ]
    
    def execute(self, query, *params):
        if 'VW_Scheduler_Alertas' in query:
            # Simular consulta de alertas
            self._simulate_alerts_query()
        elif 'CT_Alertas_Mensajes' in query and 'COUNT' in query:
            # Simular verificación de duplicados
            self._simulate_duplicate_check()
        elif 'CT_Alertas_Mensajes' in query and 'INSERT' in query:
            # Simular inserción de mensaje
            logger.info(f"🧪 Mock INSERT: mensaje registrado")
        elif 'CT_Alertas_Mensajes' in query and 'UPDATE' in query:
            # Simular actualización de estado
            logger.info(f"🧪 Mock UPDATE: estado actualizado")
        elif 'CT_Alertas_Admin_Emails' in query:
            # Simular consulta de destinatarios
            self._simulate_admin_emails()
    
    def _simulate_alerts_query(self):
        """Simula alertas de prueba."""
        ahora = datetime.now()
        
        # Crear alertas de prueba con diferentes escenarios
        self._test_alerts = [
            # Alerta que debe pasar todos los filtros
            ('000001', 'PERIODICO', 'DIARIO', ahora.time(), '', '', 
             'T001', 'Tipo Test', 'E001', 'Empresa Test', 'Q29uZXhpb25fc3RyaW5nX3Rlc3Q=',
             'P001', 'Persona Test', 'C001', 'Canal Test', 
             'https://webhook.site/test001', 'Webhook Test 1'),
            
            # Alerta fuera de ventana de tiempo
            ((ahora - timedelta(hours=1)).time() if ahora.hour > 1 else (ahora + timedelta(hours=1)).time(),
             '000002', 'PERIODICO', 'DIARIO', '', '', 
             'T002', 'Tipo Test 2', 'E002', 'Empresa Test 2', 'Q29uZXhpb25fc3RyaW5nX3Rlc3Q=',
             'P002', 'Persona Test 2', 'C002', 'Canal Test 2', 
             'https://webhook.site/test002', 'Webhook Test 2'),
            
            # Alerta semanal que no aplica hoy
            ('000003', 'PERIODICO', 'SEMANAL', ahora.time(), '1', '',  # Solo lunes
             'T003', 'Tipo Test 3', 'E003', 'Empresa Test 3', 'Q29uZXhpb25fc3RyaW5nX3Rlc3Q=',
             'P003', 'Persona Test 3', 'C003', 'Canal Test 3', 
             'https://webhook.site/test003', 'Webhook Test 3'),
        ]
    
    def _simulate_duplicate_check(self):
        """Simula verificación de duplicados - siempre 0 (no duplicado)."""
        self._count_result = [0]
    
    def _simulate_admin_emails(self):
        """Simula destinatarios de email."""
        self._admin_emails = [
            ('test@empresa.com', 'Admin Test'),
            ('soporte@empresa.com', 'Soporte Test')
        ]
    
    def fetchall(self):
        if hasattr(self, '_test_alerts'):
            return self._test_alerts
        elif hasattr(self, '_admin_emails'):
            return self._admin_emails
        return []
    
    def fetchone(self):
        if hasattr(self, '_count_result'):
            return self._count_result
        return [0]
    
    def close(self):
        pass

class MockWebhookSender:
    """Simulador de webhook sender."""
    
    def enviar_webhook(self, url, payload):
        logger.info(f"🧪 Mock webhook a {url}")
        logger.info(f"🧪 Payload: {payload}")
        
        # Simular éxito para la primera alerta, error para otras
        if '000001' in payload.get('config_id', ''):
            return True, None
        else:
            return False, "Error simulado para pruebas"

def test_scheduler():
    """Ejecuta una prueba del scheduler."""
    logger.info("🧪 INICIANDO PRUEBA DEL SCHEDULER")
    logger.info("=" * 50)
    
    # Crear scheduler con mocks
    scheduler = AlertScheduler()
    scheduler.db_config = MockDatabaseConfig()
    scheduler.webhook_sender = MockWebhookSender()
    
    # Deshabilitar email notifier para pruebas
    scheduler.email_notifier = None
    
    logger.info("🔧 Configuración de prueba lista")
    logger.info("📊 Simulando un ciclo de ejecución...")
    logger.info("")
    
    # Ejecutar un solo ciclo
    try:
        scheduler.ejecutar_ciclo()
    except Exception as e:
        logger.error(f"❌ Error en prueba: {e}")
    
    logger.info("")
    logger.info("=" * 50)
    logger.info("🎉 PRUEBA COMPLETADA")

if __name__ == "__main__":
    test_scheduler()