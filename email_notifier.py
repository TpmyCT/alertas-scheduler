"""
Módulo de notificaciones por email para errores del scheduler.

Este módulo maneja:
- Consulta de destinatarios activos desde la BD
- Generación de HTML con tabla de errores
- Envío de emails usando SMTP
"""

import os
import smtplib
import traceback
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Maneja las notificaciones por email de errores del scheduler."""
    
    def __init__(self, db_config):
        """
        Inicializa el notificador de emails.
        
        Args:
            db_config: Instancia de DatabaseConfig para conexiones
        """
        self.db_config = db_config
        self._cargar_configuracion_smtp()
    
    def _cargar_configuracion_smtp(self):
        """Carga la configuración SMTP desde variables de entorno."""
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        if not all([self.smtp_server, self.smtp_user, self.smtp_password]):
            logger.warning("⚠️ Configuración SMTP incompleta - notificaciones deshabilitadas")
            self.smtp_habilitado = False
        else:
            self.smtp_habilitado = True
    
    def obtener_destinatarios(self):
        """
        Consulta los destinatarios activos desde la BD.
        
        Returns:
            list: Lista de tuplas (email, nombre) de destinatarios activos
        """
        try:
            conn = self.db_config.connect()
            cursor = conn.cursor()
            
            query = """
            SELECT adm_Email, adm_Nombre 
            FROM CT_Alertas_Admin_Emails 
            WHERE adm_Activo = 1
            ORDER BY adm_Nombre
            """
            
            cursor.execute(query)
            destinatarios = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return destinatarios
            
        except Exception as e:
            logger.error(f"❌ Error al obtener destinatarios: {e}")
            return []
    
    def generar_html_errores(self, errores_ciclo, resumen_ejecucion):
        """
        Genera HTML completo con tabla de errores y resumen de ejecución.
        
        Args:
            errores_ciclo (list): Lista de diccionarios con errores
            resumen_ejecucion (dict): Resumen con contadores y timestamps
            
        Returns:
            str: HTML completo del email
        """
        # Colores para tipos de error
        colores_error = {
            'BD_QUERY': '#ff4444',      # Rojo
            'FILTRADO': '#ff8800',      # Naranja
            'ANTI_DUPLICADO': '#ffaa00', # Amarillo
            'WEBHOOK': '#aa00ff',       # Morado
            'DB_INSERT': '#ff0066'      # Rosa
        }
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f44336; color: white; padding: 15px; border-radius: 5px; }}
                .resumen {{ background-color: #f9f9f9; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .tabla {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .tabla th, .tabla td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                .tabla th {{ background-color: #f2f2f2; font-weight: bold; }}
                .tabla tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .tipo-error {{ padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; }}
                .stack-trace {{ font-family: monospace; font-size: 11px; max-width: 400px; word-break: break-all; }}
                .contador {{ display: inline-block; margin: 10px; padding: 10px; background-color: #e3f2fd; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>⚠️ Errores en Scheduler de Alertas</h2>
                <p>Fecha: {resumen_ejecucion['timestamp_inicio'].strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
            
            <div class="resumen">
                <h3>📊 Resumen de Ejecución</h3>
                <div class="contador">📋 Total Alertas: <strong>{resumen_ejecucion['total_alertas']}</strong></div>
                <div class="contador">✅ Enviadas: <strong>{resumen_ejecucion['alertas_enviadas']}</strong></div>
                <div class="contador">⏱️ Skip Hora: <strong>{resumen_ejecucion['alertas_skip_hora']}</strong></div>
                <div class="contador">📅 Skip Día: <strong>{resumen_ejecucion['alertas_skip_dia']}</strong></div>
                <div class="contador">🔁 Skip Duplicado: <strong>{resumen_ejecucion['alertas_skip_duplicado']}</strong></div>
                <div class="contador">❌ Total Errores: <strong>{resumen_ejecucion['total_errores']}</strong></div>
                <p><strong>Duración:</strong> {(resumen_ejecucion['timestamp_fin'] - resumen_ejecucion['timestamp_inicio']).total_seconds():.1f} segundos</p>
            </div>
            
            <h3>🚨 Detalle de Errores</h3>
            <table class="tabla">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Tipo Error</th>
                        <th>Config ID</th>
                        <th>Mensaje</th>
                        <th>Stack Trace</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for error in errores_ciclo:
            color = colores_error.get(error['tipo_error'], '#666666')
            html += f"""
                    <tr>
                        <td>{error['timestamp'].strftime('%H:%M:%S')}</td>
                        <td><span class="tipo-error" style="background-color: {color};">{error['tipo_error']}</span></td>
                        <td>{error.get('config_id', 'N/A')}</td>
                        <td>{error['mensaje']}</td>
                        <td class="stack-trace">{error['stack_trace'][:200]}{'...' if len(error['stack_trace']) > 200 else ''}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
            
            <hr>
            <p><small>Este email fue generado automáticamente por el Scheduler de Alertas.</small></p>
        </body>
        </html>
        """
        
        return html
    
    def enviar_notificacion_errores(self, errores_ciclo, resumen_ejecucion):
        """
        Envía notificación por email si hay errores.
        
        Args:
            errores_ciclo (list): Lista de errores del ciclo
            resumen_ejecucion (dict): Resumen con contadores
        """
        # Si no hay errores, no hacer nada
        if not errores_ciclo:
            return
        
        # Verificar configuración SMTP
        if not self.smtp_habilitado:
            logger.warning("⚠️ SMTP no configurado - no se pueden enviar notificaciones")
            return
        
        # Obtener destinatarios
        destinatarios = self.obtener_destinatarios()
        if not destinatarios:
            logger.warning("⚠️ No hay destinatarios configurados para notificaciones")
            return
        
        # Generar contenido del email
        subject = f"⚠️ Errores en Scheduler - {resumen_ejecucion['timestamp_inicio'].strftime('%d/%m/%Y %H:%M')}"
        html_content = self.generar_html_errores(errores_ciclo, resumen_ejecucion)
        
        # Enviar a cada destinatario
        enviados_exitosos = 0
        for email, nombre in destinatarios:
            try:
                self._enviar_email_individual(email, nombre, subject, html_content)
                enviados_exitosos += 1
                logger.info(f"📧 Notificación enviada a {nombre} ({email})")
            except Exception as e:
                logger.error(f"❌ Error al enviar email a {nombre} ({email}): {e}")
        
        logger.info(f"📊 Notificaciones enviadas: {enviados_exitosos}/{len(destinatarios)}")
    
    def _enviar_email_individual(self, email_destino, nombre_destino, subject, html_content):
        """
        Envía un email individual usando SMTP.
        
        Args:
            email_destino (str): Email del destinatario
            nombre_destino (str): Nombre del destinatario
            subject (str): Asunto del email
            html_content (str): Contenido HTML del email
        """
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.smtp_user
        msg['To'] = email_destino
        
        # Agregar contenido HTML
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Enviar email
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)