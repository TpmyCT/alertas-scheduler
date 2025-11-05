"""
Scheduler de Alertas - Arquitectura de Polling con Filtros en Python

Este scheduler implementa una arquitectura stateless que:
1. Se sincroniza al minuto exacto (segundo 00)
2. Consulta CT_Alertas_Config con joins a tablas relacionadas
3. Aplica filtros en Python: ventana de hora, frecuencia/fechas puntuales, anti-duplicados
4. Por cada alerta que pasa los filtros:
   - Obtiene destinatarios (modo INDIVIDUAL o PERFIL) desde Bejerman
   - Ejecuta query dinámico si corresponde
   - Procesa plantilla con datos del query
   - Envía webhook con payload completo por cada destinatario
5. Acumula errores y envía notificaciones por email

Cada ejecución es completamente independiente.
"""

import time
import logging
import uuid
import traceback
import json
from datetime import datetime, timedelta
import pyodbc
from database_config import DatabaseConfig
from webhook_sender import WebhookSender
from email_notifier import EmailNotifier
from bejerman_queries import BejermanQueries


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

import os

logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(logs_dir, exist_ok=True)

log_filename = os.path.join(logs_dir, f'scheduler_{datetime.now().strftime("%Y%m%d")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_filename, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# ALERT SCHEDULER
# ============================================================================

class AlertScheduler:
    """Scheduler de alertas con filtros en Python y notificaciones por email."""
    
    def __init__(self):
        """Inicializa el scheduler con los componentes necesarios."""
        self.db_config = DatabaseConfig()
        self.webhook_sender = WebhookSender()
        self.email_notifier = EmailNotifier(self.db_config)
        self.bejerman_queries = BejermanQueries(self.db_config)
    
    # ------------------------------------------------------------------------
    # MAIN EXECUTION LOOP
    # ------------------------------------------------------------------------
    
    def ejecutar(self):
        """
        Ejecuta el scheduler principal con polling cada minuto.
        Se sincroniza primero al minuto exacto y mantiene esa sincronización.
        """
        self._wait_until_next_minute()
        
        logger.info("🔄 Scheduler activo - ejecutando cada minuto exacto")
        logger.info("Presiona Ctrl+C para detener\n")
        
        try:
            while True:
                self.ejecutar_ciclo()
                
                segundos_espera = self._calculate_seconds_until_next_minute()
                logger.info(f"⏳ Esperando hasta el próximo minuto... ({segundos_espera:.1f}s)")
                
                time.sleep(segundos_espera)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Scheduler detenido por el usuario")
        except Exception as e:
            logger.error(f"❌ Error crítico en el scheduler: {e}")
            raise
    
    def ejecutar_ciclo(self):
        """Ejecuta un ciclo completo de polling con filtros y manejo de errores."""
        errores_ciclo = []
        resumen = self._init_summary()
        
        try:
            # 1. Fetch all active alerts from database
            timestamp_actual = datetime.now().strftime('%H:%M:%S')
            logger.info(f"⏰ [{timestamp_actual}] Consultando alertas...")
            
            alertas = self._fetch_all_active_alerts()
            if not alertas:
                logger.info("� No hay alertas configuradas")
                return
            
            # 2. Filter alerts for today (frequency + not sent)
            pendientes_hoy = self._filter_alerts_for_today(alertas, errores_ciclo)
            logger.info(f"📊 {len(alertas)} alertas en total | {len(pendientes_hoy)} pendientes para hoy")
            
            if not pendientes_hoy:
                return
            
            # 3. Filter alerts within time window (±2 minutes)
            procesar_ahora = self._filter_alerts_in_time_window(pendientes_hoy, errores_ciclo)
            
            if not procesar_ahora:
                return
            
            # 4. Show summary and process alerts
            self._show_alerts_summary(procesar_ahora)
            self._process_and_send_alerts(procesar_ahora, errores_ciclo, resumen)
            
        except Exception as e:
            self._log_critical_error(e, errores_ciclo)
        finally:
            self._finalize_cycle(errores_ciclo, resumen)
    
    # ------------------------------------------------------------------------
    # ALERT FETCHING & FILTERING
    # ------------------------------------------------------------------------
    
    def _fetch_all_active_alerts(self):
        """Consulta TODAS las alertas activas desde CT_Alertas_Config con JOINs."""
        try:
            conn = self.db_config.connect()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                cfg.cfg_Cod, cfg.cfg_Nombre, cfg.cfg_TipoDisparo, cfg.cfg_Frecuencia,
                cfg.cfg_HoraEnvio, cfg.cfg_DiasSemana, cfg.cfg_DiasMes, cfg.cfg_FechasPuntuales,
                cfg.cfgtip_Cod, cfg.cfgper_Cod, cfg.cfgprf_Cod, cfg.cfgcan_Cod, cfg.cfgcon_Cod, cfg.cfgemp_Cod,
                tip.tip_Desc, tip.tip_RequiereBejCod, tip.tipwbh_Cod,
                can.can_Desc,
                emp.emp_Desc AS empresa_nombre, emp.emp_Conexion,
                wbh.wbh_Url, wbh.wbh_Desc AS webhook_nombre,
                qry.qry_SQL, qry.qry_RequiereBejCod AS query_requiere_bej,
                plt.plt_Asunto, plt.plt_Mensaje
            FROM CT_Alertas_Config cfg
            INNER JOIN CT_Alertas_Tipos tip ON tip.tip_Cod = cfg.cfgtip_Cod
            INNER JOIN CT_Alertas_Canales can ON can.can_Cod = cfg.cfgcan_Cod
            LEFT JOIN CT_Empresas emp ON emp.emp_Cod = cfg.cfgemp_Cod
            LEFT JOIN CT_Alertas_Webhooks wbh ON wbh.wbh_Cod = tip.tipwbh_Cod
            LEFT JOIN CT_Alertas_Queries qry ON qry.qrytip_Cod = tip.tip_Cod 
                AND (qry.qryprf_Cod = cfg.cfgprf_Cod OR (cfg.cfgprf_Cod IS NULL AND qry.qryprf_Cod IS NULL))
            LEFT JOIN CT_Alertas_Plantillas plt ON plt.plttip_Cod = tip.tip_Cod 
                AND plt.pltcan_Cod = can.can_Cod 
                AND (plt.pltprf_Cod = cfg.cfgprf_Cod OR (cfg.cfgprf_Cod IS NULL AND plt.pltprf_Cod IS NULL))
            WHERE cfg.cfg_Activo = 1 
                AND tip.tip_Activo = 1 
                AND can.can_Activo = 1
                AND (emp.emp_Activo = 1 OR emp.emp_Activo IS NULL)
                AND (wbh.wbh_Activo = 1 OR wbh.wbh_Activo IS NULL)
            """
            
            logger.info("📋 Ejecutando query de consulta de alertas...")
            cursor.execute(query)
            columnas = [description[0] for description in cursor.description]
            
            alertas = []
            for fila in cursor.fetchall():
                alerta = dict(zip(columnas, fila))
                alertas.append(alerta)
            
            cursor.close()
            conn.close()
            
            logger.info(f"📊 Encontradas {len(alertas)} alertas activas")
            return alertas
            
        except Exception as e:
            raise Exception(f"Error al consultar CT_Alertas_Config: {e}")
    
    def _filter_alerts_for_today(self, alertas, errores_ciclo):
        """Filtra alertas que corresponden al día de hoy y no fueron enviadas."""
        pendientes_hoy = []
        
        for alerta in alertas:
            if self._should_run_today(alerta, errores_ciclo) and \
               self._not_sent_today(alerta, errores_ciclo):
                pendientes_hoy.append(alerta)
        
        return pendientes_hoy
    
    def _filter_alerts_in_time_window(self, alertas, errores_ciclo):
        """Filtra alertas que están dentro de la ventana de tiempo (±2 minutos)."""
        procesar_ahora = []
        
        for alerta in alertas:
            tipo_disparo = alerta.get('cfg_TipoDisparo', '').upper()
            
            if tipo_disparo == 'PERIODICO':
                if self._is_within_time_window_periodico(alerta, errores_ciclo):
                    procesar_ahora.append(alerta)
            elif tipo_disparo == 'PUNTUAL':
                if self._is_within_time_window_puntual(alerta, errores_ciclo):
                    procesar_ahora.append(alerta)
        
        return procesar_ahora
    
    def _is_within_time_window_periodico(self, alerta, errores_ciclo):
        """Verifica si alerta PERIODICO está en ventana de ±2 minutos."""
        try:
            hora_actual = datetime.now().time()
            hora_alerta = alerta['cfg_HoraEnvio']
            
            if not hora_alerta:
                self._add_error(errores_ciclo, 'FILTRADO', alerta['cfg_Cod'],
                               'cfg_HoraEnvio es NULL', alerta)
                return False
            
            minutos_actual = hora_actual.hour * 60 + hora_actual.minute
            minutos_alerta = hora_alerta.hour * 60 + hora_alerta.minute
            
            diferencia = abs(minutos_actual - minutos_alerta)
            diferencia = min(diferencia, 1440 - diferencia)  # Manejo de cambio de día
            
            return diferencia <= 2
            
        except Exception as e:
            self._add_error(errores_ciclo, 'FILTRADO', alerta.get('cfg_Cod', 'UNKNOWN'),
                           f'Error al validar ventana de hora: {str(e)}', alerta, e)
            return False
    
    def _should_run_today(self, alerta, errores_ciclo):
        """Verifica si la alerta debe ejecutarse hoy según tipo y frecuencia."""
        try:
            tipo_disparo = alerta.get('cfg_TipoDisparo', '').upper()
            hoy = datetime.now()
            
            if tipo_disparo == 'PERIODICO':
                return self._check_periodico_frequency(alerta, hoy, errores_ciclo)
            elif tipo_disparo == 'PUNTUAL':
                return self._check_puntual_dates(alerta, hoy)
            else:
                self._add_error(errores_ciclo, 'FILTRADO', alerta['cfg_Cod'], 
                               f'Tipo de disparo desconocido: {tipo_disparo}', alerta)
                return False
        except Exception as e:
            self._add_error(errores_ciclo, 'FILTRADO', alerta.get('cfg_Cod', 'UNKNOWN'),
                           f'Error al validar tipo de disparo/frecuencia: {str(e)}', alerta, e)
            return False
    
    def _check_periodico_frequency(self, alerta, hoy, errores_ciclo):
        """Verifica si alerta PERIODICO corresponde ejecutarse hoy."""
        frecuencia = alerta.get('cfg_Frecuencia', '').upper()
        
        if frecuencia == 'DIARIO':
            return True
        
        elif frecuencia == 'SEMANAL':
            dias_semana = alerta.get('cfg_DiasSemana', '')
            if not dias_semana:
                self._add_error(errores_ciclo, 'FILTRADO', alerta['cfg_Cod'],
                               'cfg_DiasSemana vacío para frecuencia SEMANAL', alerta)
                return False
            
            dia_hoy = hoy.isoweekday()  # 1=Lun, 7=Dom
            dias_permitidos = [int(d.strip()) for d in dias_semana.split(',') if d.strip().isdigit()]
            return dia_hoy in dias_permitidos
        
        elif frecuencia == 'MENSUAL':
            dias_mes = alerta.get('cfg_DiasMes', '')
            if not dias_mes:
                self._add_error(errores_ciclo, 'FILTRADO', alerta['cfg_Cod'],
                               'cfg_DiasMes vacío para frecuencia MENSUAL', alerta)
                return False
            
            dias_permitidos = [int(d.strip()) for d in dias_mes.split(',') if d.strip().isdigit()]
            return hoy.day in dias_permitidos
        
        elif frecuencia == 'ANUAL':
            dias_mes = alerta.get('cfg_DiasMes', '')
            if not dias_mes:
                return False
            dias_permitidos = [int(d.strip()) for d in dias_mes.split(',') if d.strip().isdigit()]
            return hoy.day in dias_permitidos
        
        else:
            self._add_error(errores_ciclo, 'FILTRADO', alerta['cfg_Cod'],
                           f'Frecuencia desconocida: {frecuencia}', alerta)
            return False
    
    def _check_puntual_dates(self, alerta, hoy):
        """Verifica si hoy coincide con alguna fecha puntual."""
        fechas_puntuales = alerta.get('cfg_FechasPuntuales', '')
        if not fechas_puntuales:
            return False
        
        for fecha_str in str(fechas_puntuales).split(','):
            fecha_str = fecha_str.strip()
            try:
                try:
                    fecha_puntual = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    fecha_puntual = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M')
                
                if fecha_puntual.date() == hoy.date():
                    return True
            except ValueError:
                continue
        
        return False
    
    def _add_error(self, errores_ciclo, tipo_error, config_id, mensaje, datos_alerta, exception=None):
        """Agrega error a la lista de errores del ciclo."""
        errores_ciclo.append({
            'timestamp': datetime.now(),
            'tipo_error': tipo_error,
            'config_id': config_id,
            'mensaje': mensaje,
            'stack_trace': traceback.format_exc() if exception else 'N/A',
            'datos_alerta': datos_alerta
        })
    
    def _not_sent_today(self, alerta, errores_ciclo):
        """
        FILTRO C: Verifica que la alerta no se haya enviado hoy.
        Considera cfg_Cod + cfgcan_Cod para distinguir alertas del mismo código pero diferentes canales.
        
        Args:
            alerta (dict): Datos de la alerta
            errores_ciclo (list): Lista para agregar errores
            
        Returns:
            bool: True si pasa el filtro (no enviada hoy), False si ya fue enviada
        """
        try:
            conn = self.db_config.connect()
            cursor = conn.cursor()
            
            # IMPORTANTE: Verificar por cfg_Cod Y cfgcan_Cod para distinguir entre canales
            query = """
            SELECT COUNT(*) 
            FROM CT_Scheduler_Alertas sa
            INNER JOIN CT_Alertas_Config cfg ON cfg.cfg_Cod = sa.schcfg_Cod
            WHERE sa.schcfg_Cod = ? 
                AND cfg.cfgcan_Cod = ?
                AND CAST(sa.sch_Fecha AS DATE) = CAST(GETDATE() AS DATE)
                AND sa.sch_Estado = 'OK'
            """
            
            cursor.execute(query, alerta['cfg_Cod'], alerta['cfgcan_Cod'])
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return count == 0  # True si no hay registros (no enviada hoy)
            
        except Exception as e:
            errores_ciclo.append({
                'timestamp': datetime.now(),
                'tipo_error': 'ANTI_DUPLICADO',
                'config_id': alerta.get('cfg_Cod', 'UNKNOWN'),
                'mensaje': f'Error al verificar duplicados: {str(e)}',
                'stack_trace': traceback.format_exc(),
                'datos_alerta': alerta
            })
            # En caso de error, SKIP la alerta por seguridad
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
                'tipo_error': 'DB_UPDATE',
                'config_id': 'UNKNOWN',
                'mensaje': error_msg,
                'stack_trace': traceback.format_exc(),
                'datos_alerta': {'msg_cod': msg_cod, 'nuevo_estado': nuevo_estado, 'tabla': 'CT_Alertas_Mensajes', 'operacion': 'UPDATE'}
            })
            logger.error(f"❌ {error_msg}")
    
    def procesar_alerta(self, alerta, errores_ciclo, resumen):
        """
        Procesa una alerta completa: obtiene destinatarios, ejecuta query, procesa plantilla y envía.
        
        Args:
            alerta (dict): Datos de la alerta
            errores_ciclo (list): Lista para agregar errores
            resumen (dict): Resumen de ejecución
        """
        cfg_cod = alerta['cfg_Cod']
        
        try:
            # 1. Obtener destinatarios según modo (INDIVIDUAL o PERFIL)
            destinatarios = self._obtener_destinatarios(alerta, errores_ciclo)
            
            if not destinatarios:
                logger.warning(f"⚠️ {cfg_cod}: Sin destinatarios")
                return
            
            # 2. Ejecutar query dinámico si corresponde (una vez por alerta, no por destinatario)
            datos_query_list = []
            if alerta.get('qry_SQL'):
                datos_query_list = self._ejecutar_query_alerta(alerta, destinatarios, errores_ciclo)
            
            # 3. Procesar plantilla y enviar por cada destinatario
            mensajes_enviados = 0
            sch_cod = self.generar_msg_cod()
            
            for idx, destinatario in enumerate(destinatarios):
                # Si hay query, usar datos específicos para este destinatario (o el primero si no hay bej_cod)
                datos_query = datos_query_list[idx] if idx < len(datos_query_list) else (datos_query_list[0] if datos_query_list else {})
                
                # Procesar plantilla
                mensaje_procesado = self._procesar_plantilla_alerta(alerta, destinatario, datos_query, errores_ciclo)
                
                # Enviar mensaje a este destinatario
                if self._enviar_mensaje_destinatario(alerta, destinatario, mensaje_procesado, datos_query, errores_ciclo, resumen):
                    mensajes_enviados += 1
            
            # 4. Registrar en CT_Scheduler_Alertas el resultado general
            self._registrar_scheduler_alerta(sch_cod, cfg_cod, mensajes_enviados, alerta, datos_query_list, destinatarios, errores_ciclo)
            
        except Exception as e:
            errores_ciclo.append({
                'timestamp': datetime.now(),
                'tipo_error': 'PROCESAMIENTO',
                'config_id': cfg_cod,
                'mensaje': f'Error al procesar alerta: {str(e)}',
                'stack_trace': traceback.format_exc(),
                'datos_alerta': alerta
            })
            logger.error(f"❌ {cfg_cod}: Error al procesar - {e}")
    
    def _obtener_destinatarios(self, alerta, errores_ciclo):
        """Obtiene destinatarios según modo INDIVIDUAL o PERFIL."""
        try:
            emp_conexion = alerta.get('emp_Conexion')
            
            # Si no hay empresa (mensaje genérico sin empresa), no hay destinatarios desde Bejerman
            if not emp_conexion:
                # Para mensajes genéricos, usar datos de la config misma
                return [{
                    'persona_cod': alerta.get('cfgper_Cod', 'GENERICO'),
                    'persona_desc': 'Mensaje Genérico',
                    'contacto_cod': alerta.get('cfgcon_Cod', 'GENERICO'),
                    'contacto_desc': 'Genérico',
                    'contacto_valor': 'GENERICO',
                    'bej_cod': None
                }]
            
            # Modo INDIVIDUAL: cfgper_Cod tiene valor, cfgprf_Cod es NULL
            if alerta.get('cfgper_Cod'):
                return self.bejerman_queries.obtener_destinatarios_individual(
                    emp_conexion,
                    alerta['cfgper_Cod'],
                    alerta.get('cfgcon_Cod'),
                    alerta['cfgcan_Cod']
                )
            
            # Modo PERFIL: cfgprf_Cod tiene valor, cfgper_Cod es NULL
            elif alerta.get('cfgprf_Cod'):
                return self.bejerman_queries.obtener_destinatarios_perfil(
                    emp_conexion,
                    alerta['cfgprf_Cod'],
                    alerta['cfgcan_Cod']
                )
            
            return []
            
        except Exception as e:
            errores_ciclo.append({
                'timestamp': datetime.now(),
                'tipo_error': 'DESTINATARIOS',
                'config_id': alerta['cfg_Cod'],
                'mensaje': f'Error al obtener destinatarios: {str(e)}',
                'stack_trace': traceback.format_exc(),
                'datos_alerta': alerta
            })
            return []
    
    def _ejecutar_query_alerta(self, alerta, destinatarios, errores_ciclo):
        """Ejecuta query dinámico para cada destinatario que tenga bej_cod."""
        try:
            emp_conexion = alerta.get('emp_Conexion')
            query_sql = alerta.get('qry_SQL')
            query_requiere_bej = alerta.get('query_requiere_bej', False)
            
            if not query_sql or not emp_conexion:
                return []
            
            resultados = []
            
            if query_requiere_bej:
                # Ejecutar query por cada destinatario con su bej_cod
                for destinatario in destinatarios:
                    bej_cod = destinatario.get('bej_cod')
                    if bej_cod:
                        resultado = self.bejerman_queries.ejecutar_query_dinamico(
                            emp_conexion, query_sql, bej_cod
                        )
                        resultados.append(resultado[0] if resultado else {})
                    else:
                        resultados.append({})
            else:
                # Ejecutar query una sola vez (sin bej_cod)
                resultado = self.bejerman_queries.ejecutar_query_dinamico(
                    emp_conexion, query_sql, None
                )
                resultados.append(resultado[0] if resultado else {})
            
            return resultados
            
        except Exception as e:
            errores_ciclo.append({
                'timestamp': datetime.now(),
                'tipo_error': 'QUERY_DINAMICO',
                'config_id': alerta['cfg_Cod'],
                'mensaje': f'Error al ejecutar query dinámico: {str(e)}',
                'stack_trace': traceback.format_exc(),
                'datos_alerta': alerta
            })
            return []
    
    def _procesar_plantilla_alerta(self, alerta, destinatario, datos_query, errores_ciclo):
        """Procesa plantilla reemplazando placeholders."""
        try:
            plantilla = alerta.get('plt_Mensaje', '')
            
            if not plantilla:
                return 'Sin plantilla'
            
            # Agregar datos del destinatario a los datos del query
            datos_completos = {
                **datos_query,
                'nombre': destinatario.get('persona_desc', ''),
                'persona_cod': destinatario.get('persona_cod', ''),
                'contacto': destinatario.get('contacto_valor', '')
            }
            
            return self.bejerman_queries.procesar_plantilla(plantilla, datos_completos)
            
        except Exception as e:
            errores_ciclo.append({
                'timestamp': datetime.now(),
                'tipo_error': 'PLANTILLA',
                'config_id': alerta['cfg_Cod'],
                'mensaje': f'Error al procesar plantilla: {str(e)}',
                'stack_trace': traceback.format_exc(),
                'datos_alerta': alerta
            })
            return 'Error en plantilla'
    
    def _enviar_mensaje_destinatario(self, alerta, destinatario, mensaje_procesado, datos_query, errores_ciclo, resumen):
        """Envía mensaje a un destinatario específico."""
        cfg_cod = alerta['cfg_Cod']
        msg_cod = self.generar_msg_cod()
        
        try:
            # 1. Preparar payload completo
            payload = {
                'config_cod': cfg_cod,
                'config_nombre': alerta.get('cfg_Nombre', ''),
                'tipo_cod': alerta.get('cfgtip_Cod', ''),
                'tipo_desc': alerta.get('tip_Desc', ''),
                'canal_cod': alerta.get('cfgcan_Cod', ''),
                'canal_desc': alerta.get('can_Desc', ''),
                'empresa_cod': alerta.get('cfgemp_Cod', ''),
                'empresa_nombre': alerta.get('empresa_nombre', ''),
                'destinatario': {
                    'persona_cod': destinatario.get('persona_cod', ''),
                    'persona_desc': destinatario.get('persona_desc', ''),
                    'contacto_cod': destinatario.get('contacto_cod', ''),
                    'contacto_desc': destinatario.get('contacto_desc', ''),
                    'contacto_valor': destinatario.get('contacto_valor', ''),
                    'bej_cod': destinatario.get('bej_cod', '')
                },
                'mensaje': mensaje_procesado,
                'asunto': alerta.get('plt_Asunto', ''),
                'datos_query': datos_query,
                'msg_cod': msg_cod,
                'timestamp': datetime.now().isoformat()
            }
            
            # 2. Insertar en CT_Alertas_Mensajes con estado PENDIENTE
            conn = self.db_config.connect()
            cursor = conn.cursor()
            
            query_insert = """
            INSERT INTO CT_Alertas_Mensajes 
            (msg_Cod, msg_Wamid, msgcfg_Cod, msg_Destinatario, msg_Estado, msgcan_Cod)
            VALUES (?, '', ?, ?, 'PENDIENTE', ?)
            """
            
            canal_cod = alerta.get('cfgcan_Cod', '0001')
            cursor.execute(query_insert, msg_cod, cfg_cod, destinatario.get('contacto_valor', ''), canal_cod)
            conn.commit()
            cursor.close()
            conn.close()
            
            # 3. Determinar webhook URL (según tipo o webhook genérico)
            webhook_url = alerta.get('wbh_Url', '')
            
            if not webhook_url:
                logger.warning(f"⚠️ No hay webhook URL para alerta {cfg_cod}")
                return False
            
            # 4. Enviar webhook
            exito, error_msg = self.webhook_sender.enviar_webhook(webhook_url, payload)
            
            # 5. Actualizar estado
            if exito:
                self.actualizar_estado_mensaje(msg_cod, 'ENVIADO', errores_ciclo)
                logger.info(f"✅ {cfg_cod} → {destinatario.get('persona_desc', 'N/A')}")
                resumen['alertas_enviadas'] += 1
                return True
            else:
                self.actualizar_estado_mensaje(msg_cod, 'ERROR', errores_ciclo)
                logger.error(f"❌ {cfg_cod} → {destinatario.get('persona_desc', 'N/A')}: {error_msg}")
                
                errores_ciclo.append({
                    'timestamp': datetime.now(),
                    'tipo_error': 'WEBHOOK',
                    'config_id': cfg_cod,
                    'mensaje': error_msg,
                    'stack_trace': 'N/A',
                    'datos_alerta': alerta
                })
                return False
                
        except Exception as e:
            errores_ciclo.append({
                'timestamp': datetime.now(),
                'tipo_error': 'ENVIO',
                'config_id': cfg_cod,
                'mensaje': f'Error al enviar mensaje: {str(e)}',
                'stack_trace': traceback.format_exc(),
                'datos_alerta': alerta
            })
            logger.error(f"❌ {cfg_cod}: Error al enviar - {e}")
            return False
    
    def _registrar_scheduler_alerta(self, sch_cod, cfg_cod, cant_mensajes, alerta, datos_query_list, destinatarios, errores_ciclo):
        """Registra resultado en CT_Scheduler_Alertas."""
        try:
            conn = self.db_config.connect()
            cursor = conn.cursor()
            hoy = datetime.now().date()
            
            # Preparar payload JSON resumido
            payload_json = json.dumps({
                'config': cfg_cod,
                'destinatarios_count': len(destinatarios),
                'mensajes_enviados': cant_mensajes,
                'query_resultados_count': len(datos_query_list)
            }, ensure_ascii=False)
            
            estado = 'OK' if cant_mensajes > 0 else 'ERROR'
            detalle_error = None if cant_mensajes > 0 else 'No se pudo enviar ningún mensaje'
            
            query = """
            INSERT INTO CT_Scheduler_Alertas 
            (sch_Cod, schcfg_Cod, sch_FechaIntento, sch_Fecha, sch_Estado, sch_CantMensajes, sch_DetalleError, sch_PayloadJson, sch_Activo)
            VALUES (?, ?, GETDATE(), ?, ?, ?, ?, ?, 1)
            """
            
            cursor.execute(query, sch_cod, cfg_cod, hoy, estado, cant_mensajes, detalle_error, payload_json)
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            errores_ciclo.append({
                'timestamp': datetime.now(),
                'tipo_error': 'DB_INSERT',
                'config_id': cfg_cod,
                'mensaje': f'Error al insertar en CT_Scheduler_Alertas: {str(e)}',
                'stack_trace': traceback.format_exc(),
                'datos_alerta': alerta
            })
            logger.error(f"❌ Error al registrar scheduler: {e}")
    
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
    
    # ------------------------------------------------------------------------
    # UTILITIES & HELPERS
    # ------------------------------------------------------------------------
    
    def _wait_until_next_minute(self):
        """Espera hasta el próximo minuto exacto."""
        segundos_espera = self._calculate_seconds_until_next_minute()
        logger.info(f"🚀 Scheduler iniciado - sincronizando al próximo minuto...")
        logger.info(f"⏳ Esperando {segundos_espera:.1f} segundos...")
        time.sleep(segundos_espera)
    
    def _calculate_seconds_until_next_minute(self):
        """Calcula segundos hasta el próximo minuto exacto."""
        ahora = datetime.now()
        proximo_minuto = (ahora + timedelta(minutes=1)).replace(second=0, microsecond=0)
        return (proximo_minuto - ahora).total_seconds()
    
    def _init_summary(self):
        """Crea diccionario de resumen de ejecución."""
        return {
            'timestamp_inicio': datetime.now(),
            'timestamp_fin': None,
            'total_alertas': 0,
            'alertas_enviadas': 0,
            'alertas_skip_hora': 0,
            'alertas_skip_dia': 0,
            'alertas_skip_duplicado': 0,
            'total_errores': 0
        }
    
    def _show_alerts_summary(self, alertas):
        """Muestra resumen de alertas a enviar con sus destinatarios."""
        logger.info(f"\n📬 {len(alertas)} alertas para enviar ahora:")
        logger.info("=" * 70)
        
        for alerta in alertas:
            cfg_cod = alerta['cfg_Cod']
            canal = alerta.get('can_Desc', 'N/A')
            tipo = alerta.get('cfg_TipoDisparo', 'N/A')
            
            hora = alerta.get('cfg_HoraEnvio', 'N/A') if tipo == 'PERIODICO' else alerta.get('cfg_FechasPuntuales', 'N/A')
            
            logger.info(f"• {cfg_cod} ({canal}) - Hora: {hora}")
            
            destinatarios = self._obtener_destinatarios(alerta, [])
            if destinatarios:
                for dest in destinatarios:
                    logger.info(f"  → {dest.get('persona_desc', 'N/A')} ({dest.get('contacto_valor', 'N/A')})")
            else:
                logger.info(f"  ⚠️ Sin destinatarios")
    
    def _process_and_send_alerts(self, alertas, errores_ciclo, resumen):
        """Procesa y envía cada alerta."""
        logger.info("\n" + "=" * 70)
        logger.info("🚀 Enviando alertas...\n")
        
        for alerta in alertas:
            self.procesar_alerta(alerta, errores_ciclo, resumen)
    
    def _log_critical_error(self, exception, errores_ciclo):
        """Registra error crítico."""
        errores_ciclo.append({
            'timestamp': datetime.now(),
            'tipo_error': 'BD_QUERY',
            'config_id': 'N/A',
            'mensaje': f'Error crítico al consultar alertas: {str(exception)}',
            'stack_trace': traceback.format_exc(),
            'datos_alerta': None
        })
        logger.error(f"❌ Error crítico al consultar alertas: {exception}")
    
    def _finalize_cycle(self, errores_ciclo, resumen):
        """Finaliza ciclo: actualiza resumen y envía notificaciones."""
        resumen['timestamp_fin'] = datetime.now()
        resumen['total_errores'] = len(errores_ciclo)
        
        if resumen['alertas_enviadas'] > 0 or errores_ciclo:
            logger.info(f"\n📊 Total enviadas: {resumen['alertas_enviadas']} | Errores: {resumen['total_errores']}")
        
        if errores_ciclo:
            try:
                self.email_notifier.enviar_notificacion_errores(errores_ciclo, resumen)
            except Exception as e:
                logger.error(f"❌ Error al procesar errores: {e}")
    
    def _is_within_time_window_puntual(self, alerta, errores_ciclo):
        """Verifica si alguna fecha puntual está en ventana de ±2 minutos."""
        try:
            fechas_puntuales = alerta.get('cfg_FechasPuntuales', '')
            if not fechas_puntuales:
                return False
            
            ahora = datetime.now()
            
            for fecha_str in fechas_puntuales.split(','):
                fecha_str = fecha_str.strip()
                
                try:
                    try:
                        fecha_puntual = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        fecha_puntual = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M')
                    
                    diferencia_minutos = abs((ahora - fecha_puntual).total_seconds() / 60)
                    
                    if diferencia_minutos <= 2:
                        return True
                except ValueError:
                    continue
            
            return False
            
        except Exception as e:
            self._add_error(errores_ciclo, 'FILTRADO', alerta.get('cfg_Cod', 'UNKNOWN'),
                           f'Error al verificar hora puntual: {str(e)}', alerta, e)
            return False


def main():
    """Función principal que inicia el scheduler."""
    try:
        scheduler = AlertScheduler()
        scheduler.ejecutar()
    except Exception as e:
        logger.error(f"❌ Error al inicializar el scheduler: {e}")


if __name__ == "__main__":
    main()

