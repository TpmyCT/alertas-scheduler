"""
Módulo para el envío de webhooks y registro de resultados.
Maneja el envío de notificaciones HTTP y el logging de las ejecuciones.
"""

import requests
from datetime import datetime


class WebhookSender:
    """Maneja el envío de webhooks y registro de resultados."""
    
    def __init__(self, db_connection):
        """
        Inicializa el enviador de webhooks.
        
        Args:
            db_connection: Conexión activa a la base de datos
        """
        self.db_connection = db_connection
        self.base_webhook_url = "https://api.constec.ar/webhook/"
    
    def enviar_webhook(self, webhook_id, alerta_id):
        """
        Envía un webhook a la URL especificada.
        
        Args:
            webhook_id (str): ID del webhook configurado
            alerta_id (int): ID de la alerta que se está ejecutando
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not webhook_id:
            return False, "No hay webhook configurado"
        
        try:
            url = f"{self.base_webhook_url}{webhook_id}"
            print(f"   📡 Enviando webhook a: {url}")
            
            response = requests.post(url, json={"alerta_id": alerta_id})
            response.raise_for_status()  # Lanza excepción si hay error HTTP
            
            mensaje = f"OK - Código de respuesta: {response.status_code}"
            print(f"   ✅ Webhook enviado exitosamente (Código: {response.status_code})")
            return True, mensaje
            
        except requests.exceptions.RequestException as e:
            mensaje = f"ERROR: {e}"
            print(f"   ❌ Error al enviar webhook: {e}")
            return False, mensaje
        except Exception as e:
            mensaje = f"ERROR inesperado: {e}"
            print(f"   ❌ Error inesperado al enviar webhook: {e}")
            return False, mensaje
    
    def registrar_ejecucion(self, alerta_id, resultado):
        """
        Registra el resultado de la ejecución en la base de datos.
        
        Args:
            alerta_id (int): ID de la alerta ejecutada
            resultado (str): Resultado de la ejecución
            
        Returns:
            bool: True si el registro fue exitoso, False si hubo error
        """
        try:
            with self.db_connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO ct_alertas_log (alerta_id, fecha_ejecucion, resultado)
                    VALUES (?, GETDATE(), ?)
                """, (alerta_id, resultado))
                self.db_connection.commit()
                print(f"   📝 Resultado guardado en el log")
                return True
                
        except Exception as e:
            print(f"   ⚠️  Error al guardar en base de datos: {e}")
            return False
    
    def ejecutar_alerta_completa(self, alerta):
        """
        Ejecuta una alerta completa: envía webhook y registra el resultado.
        
        Args:
            alerta (dict): Diccionario con los datos de la alerta
        """
        hora_actual = datetime.now().strftime('%H:%M:%S')
        print(f"\n🔔 [{hora_actual}] EJECUTANDO ALERTA #{alerta['id']}")
        
        # Enviar webhook
        exito, resultado = self.enviar_webhook(alerta['webhook_id'], alerta['id'])
        
        # Registrar resultado en base de datos
        self.registrar_ejecucion(alerta['id'], resultado)
        
        print("   ✅ Alerta completada\n")