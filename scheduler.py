"""
Scheduler de Alertas - Arquitectura de Polling con Filtros en Python

Este scheduler implementa una arquitectura stateless que:
1. Se sincroniza al minuto exacto (segundo 00)
2. Consulta la vista VW_Scheduler_Alertas (sin filtros)
3. Aplica 3 filtros en Python: ventana de hora, frecuencia, anti-duplicados
4. Por cada alerta que pasa los filtros, registra en CT_Alertas_Mensajes y envía webhook
5. Acumula errores y envía notificaciones por email

Cada ejecución es completamente independiente.
"""

import time
import logging
import uuid
import traceback
from datetime import datetime, timedelta
import pyodbc
from database_config import DatabaseConfig
from webhook_sender import WebhookSender
from email_notifier import EmailNotifier


# Configurar logging con formato personalizado
import os
from datetime import datetime

# Crear directorio de logs si no existe
logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configurar logging tanto a consola como a archivo
log_filename = os.path.join(logs_dir, f'scheduler_{datetime.now().strftime("%Y%m%d")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(),  # Consola
        logging.FileHandler(log_filename, encoding='utf-8')  # Archivo
    ]
)
logger = logging.getLogger(__name__)


class AlertScheduler:
    """Scheduler de alertas con filtros en Python y notificaciones por email."""
    
    def __init__(self):
        """Inicializa el scheduler con los componentes necesarios."""
        self.db_config = DatabaseConfig()
        self.webhook_sender = WebhookSender()
        self.email_notifier = EmailNotifier(self.db_config)
        
    def generar_msg_cod(self):
        """
        Genera un código único para el mensaje.
        
        Returns:
            str: Código único de 6 caracteres
        """
        timestamp = str(int(time.time()))[-4:]
        uuid_part = str(uuid.uuid4()).replace('-', '')[:2].upper()
        return f"{timestamp}{uuid_part}"
    
    def calcular_segundos_hasta_proximo_minuto(self):
        """
        Calcula cuántos segundos faltan para el próximo minuto exacto.
        
        Returns:
            float: Segundos hasta el próximo minuto (incluyendo microsegundos)
        """
        ahora = datetime.now()
        proximo_minuto = (ahora + timedelta(minutes=1)).replace(second=0, microsecond=0)
        delta = proximo_minuto - ahora
        return delta.total_seconds()
    
    def sincronizar_al_proximo_minuto(self):
        """Espera hasta el próximo minuto exacto antes de continuar."""
        segundos_espera = self.calcular_segundos_hasta_proximo_minuto()
        logger.info(f"🚀 Scheduler iniciado - sincronizando al próximo minuto...")
        logger.info(f"⏳ Esperando {segundos_espera:.1f} segundos...")
        time.sleep(segundos_espera)
    
    def consultar_todas_las_alertas(self):
        """
        Consulta TODAS las alertas activas desde la vista (sin filtros).
        
        Returns:
            list: Lista de diccionarios con datos de alertas o None si error
        """
        try:
            conn = self.db_config.connect()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                config_id, tipo_disparo, frecuencia, hora_envio, dias_semana, dias_mes,
                tipo_codigo, tipo_descripcion, empresa_codigo, empresa_nombre, empresa_conexion,
                persona_codigo, persona_nombre, canal_codigo, canal_nombre, 
                webhook_url, webhook_nombre
            FROM VW_Scheduler_Alertas
            """
            
            cursor.execute(query)
            columnas = [description[0] for description in cursor.description]
            
            alertas = []
            for fila in cursor.fetchall():
                alerta = dict(zip(columnas, fila))
                alertas.append(alerta)
            
            cursor.close()
            conn.close()
            return alertas
            
        except Exception as e:
            # Error crítico - retornar None para que se capture en el ciclo principal
            raise Exception(f"Error al consultar vista VW_Scheduler_Alertas: {e}")
    
    def filtro_ventana_hora(self, alerta, errores_ciclo):
        """
        FILTRO A: Verifica si la alerta está en la ventana de ±2 minutos.
        
        Args:
            alerta (dict): Datos de la alerta
            errores_ciclo (list): Lista para agregar errores
            
        Returns:
            bool: True si pasa el filtro, False si no
        """
        try:
            hora_actual = datetime.now().time()
            hora_alerta = alerta['hora_envio']
            
            if not hora_alerta:
                errores_ciclo.append({
                    'timestamp': datetime.now(),
                    'tipo_error': 'FILTRADO',
                    'config_id': alerta['config_id'],
                    'mensaje': 'hora_envio es NULL',
                    'stack_trace': 'N/A',
                    'datos_alerta': alerta
                })
                return False
            
            # Convertir a minutos para facilitar cálculo
            minutos_actual = hora_actual.hour * 60 + hora_actual.minute
            minutos_alerta = hora_alerta.hour * 60 + hora_alerta.minute
            
            diferencia = abs(minutos_actual - minutos_alerta)
            
            # Manejar caso de cambio de día (23:59 vs 00:01)
            diferencia = min(diferencia, 1440 - diferencia)  # 1440 = minutos en un día
            
            return diferencia <= 2
            
        except Exception as e:
            errores_ciclo.append({
                'timestamp': datetime.now(),
                'tipo_error': 'FILTRADO',
                'config_id': alerta.get('config_id', 'UNKNOWN'),
                'mensaje': f'Error al validar ventana de hora: {str(e)}',
                'stack_trace': traceback.format_exc(),
                'datos_alerta': alerta
            })
            return False
    
    def filtro_frecuencia(self, alerta, errores_ciclo):
        """
        FILTRO B: Verifica si la alerta debe ejecutarse según su frecuencia.
        
        Args:
            alerta (dict): Datos de la alerta
            errores_ciclo (list): Lista para agregar errores
            
        Returns:
            bool: True si pasa el filtro, False si no
        """
        try:
            frecuencia = alerta.get('frecuencia', '').upper()
            hoy = datetime.now()
            
            if frecuencia == 'DIARIO':
                return True
            
            elif frecuencia == 'SEMANAL':
                dias_semana = alerta.get('dias_semana', '')
                if not dias_semana:
                    errores_ciclo.append({
                        'timestamp': datetime.now(),
                        'tipo_error': 'FILTRADO',
                        'config_id': alerta['config_id'],
                        'mensaje': 'dias_semana vacío para frecuencia SEMANAL',
                        'stack_trace': 'N/A',
                        'datos_alerta': alerta
                    })
                    return False
                
                # Convertir día de Python a formato SQL Server
                # Python: 1=Lunes, 2=Martes, ..., 7=Domingo
                # SQL Server: 1=Domingo, 2=Lunes, ..., 7=Sábado
                dia_python = hoy.isoweekday()  # 1-7
                dia_sql_server = 1 if dia_python == 7 else dia_python + 1
                
                dias_permitidos = [int(d.strip()) for d in dias_semana.split(',') if d.strip().isdigit()]
                return dia_sql_server in dias_permitidos
            
            elif frecuencia == 'MENSUAL':
                dias_mes = alerta.get('dias_mes', '')
                if not dias_mes:
                    errores_ciclo.append({
                        'timestamp': datetime.now(),
                        'tipo_error': 'FILTRADO',
                        'config_id': alerta['config_id'],
                        'mensaje': 'dias_mes vacío para frecuencia MENSUAL',
                        'stack_trace': 'N/A',
                        'datos_alerta': alerta
                    })
                    return False
                
                dias_permitidos = [int(d.strip()) for d in dias_mes.split(',') if d.strip().isdigit()]
                return hoy.day in dias_permitidos
            
            else:
                errores_ciclo.append({
                    'timestamp': datetime.now(),
                    'tipo_error': 'FILTRADO',
                    'config_id': alerta['config_id'],
                    'mensaje': f'Frecuencia desconocida: {frecuencia}',
                    'stack_trace': 'N/A',
                    'datos_alerta': alerta
                })
                return False
                
        except Exception as e:
            errores_ciclo.append({
                'timestamp': datetime.now(),
                'tipo_error': 'FILTRADO',
                'config_id': alerta.get('config_id', 'UNKNOWN'),
                'mensaje': f'Error al validar frecuencia: {str(e)}',
                'stack_trace': traceback.format_exc(),
                'datos_alerta': alerta
            })
            return False
    
    def filtro_anti_duplicados(self, alerta, errores_ciclo):
        """
        FILTRO C: Verifica que la alerta no se haya enviado hoy.
        
        Args:
            alerta (dict): Datos de la alerta
            errores_ciclo (list): Lista para agregar errores
            
        Returns:
            bool: True si pasa el filtro (no enviada hoy), False si ya fue enviada
        """
        try:
            conn = self.db_config.connect()
            cursor = conn.cursor()
            
            query = """
            SELECT COUNT(*) 
            FROM CT_Alertas_Mensajes 
            WHERE msgcfg_Cod = ? AND CAST(msg_FechaEnvio AS DATE) = CAST(GETDATE() AS DATE)
            """
            
            cursor.execute(query, alerta['config_id'])
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return count == 0  # True si no hay registros (no enviada hoy)
            
        except Exception as e:
            errores_ciclo.append({
                'timestamp': datetime.now(),
                'tipo_error': 'ANTI_DUPLICADO',
                'config_id': alerta.get('config_id', 'UNKNOWN'),
                'mensaje': f'Error al verificar duplicados: {str(e)}',
                'stack_trace': traceback.format_exc(),
                'datos_alerta': alerta
            })
            # En caso de error, SKIP la alerta por seguridad
            return False
    
    def registrar_mensaje_en_bd(self, msg_cod, config_id, errores_ciclo):
        """
        Registra el mensaje en la tabla CT_Alertas_Mensajes con estado PENDIENTE.
        
        Args:
            msg_cod (str): Código único del mensaje
            config_id (str): ID de configuración de la alerta
            errores_ciclo (list): Lista para agregar errores
            
        Returns:
            bool: True si se registró correctamente, False en caso contrario
        """
        try:
            conn = self.db_config.connect()
            cursor = conn.cursor()
            
            query = """
            INSERT INTO CT_Alertas_Mensajes 
            (msg_Cod, msg_Wamid, msgcfg_Cod, msgbej_Tel, msg_Estado)
            VALUES (?, '', ?, '', 'PENDIENTE')
            """
            
            cursor.execute(query, msg_cod, config_id)
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            error_msg = f'Error al insertar mensaje en CT_Alertas_Mensajes: {str(e)}'
            errores_ciclo.append({
                'timestamp': datetime.now(),
                'tipo_error': 'DB_INSERT',
                'config_id': config_id,
                'mensaje': error_msg,
                'stack_trace': traceback.format_exc(),
                'datos_alerta': {'msg_cod': msg_cod, 'config_id': config_id, 'tabla': 'CT_Alertas_Mensajes'}
            })
            logger.error(f"❌ {error_msg}")
            return False
    
    def actualizar_estado_mensaje(self, msg_cod, nuevo_estado, errores_ciclo):
        """
        Actualiza el estado de un mensaje en la BD.
        
        Args:
            msg_cod (str): Código del mensaje
            nuevo_estado (str): Nuevo estado (ENVIADO o ERROR)
            errores_ciclo (list): Lista para agregar errores
        """
        try:
            conn = self.db_config.connect()
            cursor = conn.cursor()
            
            query = """
            UPDATE CT_Alertas_Mensajes 
            SET msg_Estado = ?, msg_FechaRespuesta = GETDATE()
            WHERE msg_Cod = ?
            """
            
            cursor.execute(query, nuevo_estado, msg_cod)
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            error_msg = f'Error al actualizar estado en CT_Alertas_Mensajes: {str(e)}'
            errores_ciclo.append({
                'timestamp': datetime.now(),
                'tipo_error': 'DB_INSERT',
                'config_id': 'UNKNOWN',
                'mensaje': error_msg,
                'stack_trace': traceback.format_exc(),
                'datos_alerta': {'msg_cod': msg_cod, 'nuevo_estado': nuevo_estado, 'tabla': 'CT_Alertas_Mensajes', 'operacion': 'UPDATE'}
            })
            logger.error(f"❌ {error_msg}")
    
    def procesar_alerta(self, alerta, errores_ciclo, resumen):
        """
        Procesa una alerta individual: registra en BD y envía webhook.
        
        Args:
            alerta (dict): Datos de la alerta desde la vista
            errores_ciclo (list): Lista para agregar errores
            resumen (dict): Diccionario de contadores
        """
        config_id = alerta['config_id']
        webhook_url = alerta['webhook_url']
        
        # Generar código único para el mensaje
        msg_cod = self.generar_msg_cod()
        
        # 1. Registrar PRIMERO en la BD para evitar duplicados
        if not self.registrar_mensaje_en_bd(msg_cod, config_id, errores_ciclo):
            logger.error(f"❌ No se pudo registrar mensaje para alerta {config_id}")
            return
        
        # 2. Preparar payload JSON con todos los campos
        payload = {
            "config_id": alerta['config_id'],
            "tipo_codigo": alerta['tipo_codigo'],
            "empresa_codigo": alerta['empresa_codigo'],
            "empresa_conexion": alerta['empresa_conexion'],
            "persona_codigo": alerta['persona_codigo'],
            "canal_codigo": alerta['canal_codigo']
        }
        
        # 3. Enviar webhook
        logger.info(f"✉️ Enviando alerta {config_id}...")
        
        exito, error_msg = self.webhook_sender.enviar_webhook(webhook_url, payload)
        
        # 4. Actualizar estado según resultado
        if exito:
            self.actualizar_estado_mensaje(msg_cod, 'ENVIADO', errores_ciclo)
            logger.info(f"✅ Alerta {config_id} enviada")
            resumen['alertas_enviadas'] += 1
        else:
            self.actualizar_estado_mensaje(msg_cod, 'ERROR', errores_ciclo)
            logger.error(f"❌ Error en alerta {config_id}: {error_msg}")
            
            # Agregar error de webhook a la lista
            errores_ciclo.append({
                'timestamp': datetime.now(),
                'tipo_error': 'WEBHOOK',
                'config_id': config_id,
                'mensaje': error_msg,
                'stack_trace': 'N/A',
                'datos_alerta': alerta
            })
    
    def generar_reporte_html_local(self, errores_ciclo, resumen):
        """
        Genera un reporte HTML local de errores.
        
        Args:
            errores_ciclo (list): Lista de errores del ciclo
            resumen (dict): Resumen de ejecución
        """
        try:
            # Crear directorio de reportes si no existe
            reportes_dir = os.path.join(os.path.dirname(__file__), 'reportes')
            os.makedirs(reportes_dir, exist_ok=True)
            
            # Generar nombre del archivo
            timestamp = resumen['timestamp_inicio'].strftime('%Y%m%d_%H%M%S')
            filename = f'reporte_errores_{timestamp}.html'
            filepath = os.path.join(reportes_dir, filename)
            
            # Generar HTML usando el email_notifier
            html_content = self.email_notifier.generar_html_errores(errores_ciclo, resumen)
            
            # Guardar archivo
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"📄 Reporte HTML guardado: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error al generar reporte HTML local: {e}")
    
    def ejecutar_ciclo(self):
        """Ejecuta un ciclo completo de polling con filtros y manejo de errores."""
        # Inicializar estructuras de datos del ciclo
        errores_ciclo = []
        resumen = {
            'timestamp_inicio': datetime.now(),
            'timestamp_fin': None,
            'total_alertas': 0,
            'alertas_enviadas': 0,
            'alertas_skip_hora': 0,
            'alertas_skip_dia': 0,
            'alertas_skip_duplicado': 0,
            'total_errores': 0
        }
        
        try:
            # Mostrar inicio del ciclo
            timestamp_actual = datetime.now().strftime('%H:%M:%S')
            logger.info(f"⏰ [{timestamp_actual}] Consultando alertas...")
            
            # Consultar TODAS las alertas activas (sin filtros)
            alertas = self.consultar_todas_las_alertas()
            resumen['total_alertas'] = len(alertas)
            logger.info(f"📊 Encontradas {len(alertas)} alertas en total")
            
            # Procesar cada alerta con los 3 filtros
            for alerta in alertas:
                config_id = alerta['config_id']
                logger.info(f"� Evaluando alerta {config_id}...")
                
                # FILTRO A: Ventana de hora (±2 minutos)
                if not self.filtro_ventana_hora(alerta, errores_ciclo):
                    logger.info(f"⏱️ Alerta {config_id} fuera de ventana")
                    resumen['alertas_skip_hora'] += 1
                    continue
                
                # FILTRO B: Frecuencia (día de la semana/mes)
                if not self.filtro_frecuencia(alerta, errores_ciclo):
                    logger.info(f"� Alerta {config_id} no aplica hoy")
                    resumen['alertas_skip_dia'] += 1
                    continue
                
                # FILTRO C: Anti-duplicados
                if not self.filtro_anti_duplicados(alerta, errores_ciclo):
                    logger.info(f"🔁 Alerta {config_id} ya enviada hoy")
                    resumen['alertas_skip_duplicado'] += 1
                    continue
                
                # Si llegó hasta acá, procesar la alerta
                self.procesar_alerta(alerta, errores_ciclo, resumen)
            
        except Exception as e:
            # Error crítico en consulta de BD
            errores_ciclo.append({
                'timestamp': datetime.now(),
                'tipo_error': 'BD_QUERY',
                'config_id': 'N/A',
                'mensaje': f'Error crítico al consultar alertas: {str(e)}',
                'stack_trace': traceback.format_exc(),
                'datos_alerta': None
            })
            logger.error(f"❌ Error crítico al consultar alertas: {e}")
        
        finally:
            # Finalizar resumen
            resumen['timestamp_fin'] = datetime.now()
            resumen['total_errores'] = len(errores_ciclo)
            
            # Mostrar resumen en consola
            logger.info(f"📬 Total enviadas: {resumen['alertas_enviadas']} | Errores: {resumen['total_errores']}")
            
            # Generar reporte HTML local y enviar email si hay errores
            if errores_ciclo:
                try:
                    # Generar y guardar reporte HTML local
                    self.generar_reporte_html_local(errores_ciclo, resumen)
                    
                    # Enviar notificación por email
                    self.email_notifier.enviar_notificacion_errores(errores_ciclo, resumen)
                except Exception as e:
                    logger.error(f"❌ Error al procesar errores: {e}")
    
    def ejecutar(self):
        """
        Ejecuta el scheduler principal con polling cada minuto.
        Se sincroniza primero al minuto exacto y mantiene esa sincronización.
        """
        # Sincronizar al próximo minuto antes de empezar
        self.sincronizar_al_proximo_minuto()
        
        logger.info("🔄 Scheduler activo - ejecutando cada minuto exacto")
        logger.info("Presiona Ctrl+C para detener\n")
        
        try:
            while True:
                # Ejecutar ciclo de polling
                self.ejecutar_ciclo()
                
                # Calcular tiempo hasta el próximo minuto
                segundos_espera = self.calcular_segundos_hasta_proximo_minuto()
                logger.info(f"⏳ Esperando hasta el próximo minuto... ({segundos_espera:.1f}s)")
                
                # Esperar hasta el próximo minuto exacto
                time.sleep(segundos_espera)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Scheduler detenido por el usuario")
        except Exception as e:
            logger.error(f"❌ Error crítico en el scheduler: {e}")
            raise


def main():
    """Función principal que inicia el scheduler."""
    try:
        scheduler = AlertScheduler()
        scheduler.ejecutar()
    except Exception as e:
        logger.error(f"❌ Error al inicializar el scheduler: {e}")


if __name__ == "__main__":
    main()


