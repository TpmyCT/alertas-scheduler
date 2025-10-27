"""
Módulo simple para el envío de webhooks con timeout configurado.
"""

import requests
import json


class WebhookSender:
    """Maneja el envío simple de webhooks con timeout de 10 segundos."""
    
    def __init__(self):
        """Inicializa el enviador de webhooks."""
        self.timeout = 10  # Timeout de 10 segundos como especificado
    
    def enviar_webhook(self, webhook_url, payload):
        """
        Envía un webhook POST con el payload JSON.
        
        Args:
            webhook_url (str): URL completa del webhook
            payload (dict): Datos a enviar en formato JSON
            
        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        if not webhook_url:
            return False, "URL de webhook vacía"
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'AlertScheduler/1.0'
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            # Verificar si la respuesta fue exitosa (códigos 2xx)
            response.raise_for_status()
            
            return True, None
            
        except requests.exceptions.Timeout:
            return False, f"Timeout después de {self.timeout} segundos"
        except requests.exceptions.ConnectionError:
            return False, "Error de conexión al servidor"
        except requests.exceptions.HTTPError as e:
            return False, f"Error HTTP {response.status_code}: {e}"
        except requests.exceptions.RequestException as e:
            return False, f"Error en la petición: {e}"
        except Exception as e:
            return False, f"Error inesperado: {e}"