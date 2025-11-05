"""
Alert Processor - Processes and sends alerts
"""

import json
import time
import uuid
import logging
from datetime import datetime
from bejerman_queries import BejermanQueries
from table_names import (
    TABLE_ALERTAS_CONFIG,
    TABLE_ALERTAS_MENSAJES,
    TABLE_ALERTAS_TIPOS,
    TABLE_ALERTAS_CANALES,
    TABLE_EMPRESAS,
    TABLE_ALERTAS_WEBHOOKS,
    TABLE_ALERTAS_QUERIES,
    TABLE_ALERTAS_PLANTILLAS,
    TABLE_BEJERMAN_CONTACTOS,
    TABLE_BEJERMAN_PERFILES
)

logger = logging.getLogger(__name__)


def process_and_send_alerts(alerts, errors, summary, db_config, webhook_sender):
    """Processes and sends all alerts."""
    logger.info("\n" + "=" * 70)
    logger.info("🚀 Enviando alertas...\n")
    
    bejerman_queries = BejermanQueries(db_config)
    
    for alert in alerts:
        _process_single_alert(alert, errors, summary, db_config, webhook_sender, bejerman_queries)


def show_alerts_summary(alerts, db_config):
    """Shows summary of alerts to be sent with recipients."""
    logger.info(f"\n📬 {len(alerts)} alertas para enviar ahora:")
    logger.info("=" * 70)
    
    bejerman_queries = BejermanQueries(db_config)
    
    for alert in alerts:
        cfg_cod = alert['cfg_Cod']
        canal = alert.get('can_Desc', 'N/A')
        tipo = alert.get('cfg_TipoDisparo', 'N/A')
        
        hora = alert.get('cfg_HoraEnvio', 'N/A') if tipo == 'PERIODICO' else alert.get('cfg_FechasPuntuales', 'N/A')
        
        logger.info(f"• {cfg_cod} ({canal}) - Hora: {hora}")
        
        destinatarios = _get_recipients(alert, bejerman_queries)
        if destinatarios:
            for dest in destinatarios:
                contacto_info = dest.get('Tcon_Email') or dest.get('Tcon_Celular') or 'N/A'
                logger.info(f"  → {dest.get('Tper_Desc', 'N/A')} ({contacto_info})")
        else:
            logger.info(f"  ⚠️ Sin destinatarios")


# ------------------------------------------------------------------------
# PRIVATE HELPERS
# ------------------------------------------------------------------------

def _process_single_alert(alert, errors, summary, db_config, webhook_sender, bejerman_queries):
    """Processes a single alert: recipients → query → template → send."""
    cfg_cod = alert['cfg_Cod']
    
    try:
        destinatarios = _get_recipients(alert, bejerman_queries)
        if not destinatarios:
            logger.warning(f"⚠️ {cfg_cod}: Sin destinatarios")
            return
        
        datos_query_list = _execute_dynamic_queries(alert, destinatarios, bejerman_queries, errors)
        
        mensajes_enviados = 0
        sch_cod = _generate_unique_code()
        
        for idx, destinatario in enumerate(destinatarios):
            datos_query = datos_query_list[idx] if idx < len(datos_query_list) else (datos_query_list[0] if datos_query_list else {})
            mensaje_procesado = _process_template(alert, destinatario, datos_query, bejerman_queries)
            
            if _send_to_recipient(alert, destinatario, mensaje_procesado, datos_query, db_config, webhook_sender, errors, summary):
                mensajes_enviados += 1
        
        _register_execution(sch_cod, cfg_cod, mensajes_enviados, alert, datos_query_list, destinatarios, db_config, errors)
        
    except Exception as e:
        from alert_filters import _add_error
        _add_error(errors, 'PROCESAMIENTO', cfg_cod, f'Error processing alert: {str(e)}', alert, e)
        logger.error(f"❌ {cfg_cod}: Error al procesar - {e}")


def _get_recipients(alert, bejerman_queries):
    """Gets recipients based on INDIVIDUAL or PERFIL mode."""
    emp_conexion = alert.get('emp_Conexion')
    
    if not emp_conexion:
        return [{
            'Tper_Cod': alert.get('cfgper_Cod', 'GENERICO'),
            'Tper_Desc': 'Mensaje Genérico',
            'Tcon_Cod': alert.get('cfgcon_Cod', 'GENERICO'),
            'Tcon_Desc': 'Genérico',
            'Tcon_Email': 'GENERICO',
            'Tcon_Celular': 'GENERICO',
            'Trppbej_Cod': None
        }]
    
    if alert.get('cfgper_Cod'):
        return bejerman_queries.obtener_destinatarios_individual(
            emp_conexion, alert['cfgper_Cod'], alert.get('cfgcon_Cod'), alert['cfgcan_Cod']
        )
    elif alert.get('cfgprf_Cod'):
        return bejerman_queries.obtener_destinatarios_perfil(
            emp_conexion, alert['cfgprf_Cod'], alert['cfgcan_Cod']
        )
    
    return []


def _execute_dynamic_queries(alert, destinatarios, bejerman_queries, errors):
    """Executes dynamic query if needed."""
    emp_conexion = alert.get('emp_Conexion')
    query_sql = alert.get('qry_SQL')
    query_requiere_bej = alert.get('query_requiere_bej', False)
    
    if not query_sql or not emp_conexion:
        return []
    
    resultados = []
    
    if query_requiere_bej:
        for destinatario in destinatarios:
            bej_cod = destinatario.get('bej_cod')
            if bej_cod:
                resultado = bejerman_queries.ejecutar_query_dinamico(emp_conexion, query_sql, bej_cod)
                resultados.append(resultado[0] if resultado else {})
            else:
                resultados.append({})
    else:
        resultado = bejerman_queries.ejecutar_query_dinamico(emp_conexion, query_sql, None)
        resultados.append(resultado[0] if resultado else {})
    
    return resultados


def _process_template(alert, destinatario, datos_query, bejerman_queries):
    """Processes template with placeholders."""
    plantilla = alert.get('plt_Mensaje', '')
    if not plantilla:
        return 'Sin plantilla'
    
    # Combinar datos del query con datos del destinatario
    datos_completos = {
        **datos_query,
        **destinatario  # Agregar TODOS los campos del destinatario con sus nombres originales
    }
    
    return bejerman_queries.procesar_plantilla(plantilla, datos_completos)


def _send_to_recipient(alert, destinatario, mensaje, datos_query, db_config, webhook_sender, errors, summary):
    """Sends message to a specific recipient."""
    cfg_cod = alert['cfg_Cod']
    msg_cod = _generate_unique_code()
    
    try:
        payload = _create_webhook_payload(alert, destinatario, mensaje, datos_query, msg_cod)
        
        # Usar Tcon_Email o Tcon_Celular según el canal para el registro
        canal_cod = alert.get('cfgcan_Cod', '0001')
        if canal_cod == '0001':  # Email
            contacto_registro = destinatario.get('Tcon_Email', '')
        else:  # WhatsApp, SMS, Telegram
            contacto_registro = destinatario.get('Tcon_Celular', '')
        
        # Validar que el contacto no esté vacío o NULL
        if not contacto_registro or contacto_registro.strip() == '':
            canal_nombre = alert.get('can_Desc', 'N/A')
            logger.warning(f"⚠️ {cfg_cod} → {destinatario.get('Tper_Desc', 'N/A')}: Sin contacto válido para {canal_nombre}")
            return False
        
        _insert_message_record(msg_cod, cfg_cod, contacto_registro, canal_cod, db_config)
        
        webhook_url = alert.get('wbh_Url', '')
        if not webhook_url:
            logger.warning(f"⚠️ No webhook URL for alert {cfg_cod}")
            return False
        
        exito, error_msg = webhook_sender.enviar_webhook(webhook_url, payload)
        
        if exito:
            _update_message_status(msg_cod, 'ENVIADO', db_config)
            logger.info(f"✅ {cfg_cod} → {destinatario.get('Tper_Desc', 'N/A')} ({contacto_registro}) | MsgID: {msg_cod}")
            summary['alertas_enviadas'] += 1
            return True
        else:
            _update_message_status(msg_cod, 'ERROR', db_config)
            logger.error(f"❌ {cfg_cod} → {destinatario.get('Tper_Desc', 'N/A')} ({contacto_registro}): {error_msg}")
            logger.error(f"   🔗 Webhook: {webhook_url}")
            from alert_filters import _add_error
            _add_error(errors, 'WEBHOOK', cfg_cod, error_msg, alert)
            return False
    except Exception as e:
        from alert_filters import _add_error
        _add_error(errors, 'ENVIO', cfg_cod, f'Error sending message: {str(e)}', alert, e)
        logger.error(f"❌ {cfg_cod}: Error al enviar - {e}")
        return False


def _create_webhook_payload(alert, destinatario, mensaje, datos_query, msg_cod):
    """Creates webhook payload separating fields by source table."""
    
    def _serialize_value(value):
        """Converts datetime, date, time and other non-JSON types to serializable formats."""
        from datetime import date, time
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, date):
            return value.isoformat()
        elif isinstance(value, time):
            return value.isoformat()
        return value
    
    def _filter_non_null_dict(data_dict):
        """Removes entries where all values are None."""
        if not data_dict or all(v is None for v in data_dict.values()):
            return {}
        return data_dict
    
    # Identificar campos por prefijo de tabla (nombres extraídos dinámicamente de la BD)
    ct_alertas_config = {k: _serialize_value(v) for k, v in alert.items() if k.startswith('cfg_')}
    ct_alertas_tipos = {k: _serialize_value(v) for k, v in alert.items() if k.startswith('tip_')}
    ct_alertas_canales = {k: _serialize_value(v) for k, v in alert.items() if k.startswith('can_')}
    ct_empresas = {k: _serialize_value(v) for k, v in alert.items() if k.startswith('emp_')}
    ct_alertas_webhooks = {k: _serialize_value(v) for k, v in alert.items() if k.startswith('wbh_')}
    ct_alertas_queries = {k: _serialize_value(v) for k, v in alert.items() if k.startswith('qry_')}
    ct_alertas_plantillas = {k: _serialize_value(v) for k, v in alert.items() if k.startswith('plt_')}
    
    # Filtrar diccionarios que solo tienen NULLs (de LEFT JOINs sin match)
    ct_alertas_queries = _filter_non_null_dict(ct_alertas_queries)
    ct_alertas_plantillas = _filter_non_null_dict(ct_alertas_plantillas)
    
    # Agregar resultados del query a CT_Alertas_Queries si existen
    if datos_query:
        if not ct_alertas_queries:
            ct_alertas_queries = {}
        ct_alertas_queries['query_resultados'] = {k: _serialize_value(v) for k, v in datos_query.items()}
    
    # Separar datos de Bejerman por tabla (contactos y perfiles)
    bejerman_contactos = {k: _serialize_value(v) for k, v in destinatario.items() if k.startswith('Tcon_') or k.startswith('Tper_') or k == 'Trppbej_Cod'}
    bejerman_perfiles = {k: _serialize_value(v) for k, v in destinatario.items() if k.startswith('Tprf_')}
    bejerman_perfiles = _filter_non_null_dict(bejerman_perfiles)
    
    payload = {
        TABLE_ALERTAS_CONFIG: ct_alertas_config,
        TABLE_ALERTAS_TIPOS: ct_alertas_tipos,
        TABLE_ALERTAS_CANALES: ct_alertas_canales,
        TABLE_EMPRESAS: ct_empresas,
        TABLE_ALERTAS_WEBHOOKS: ct_alertas_webhooks,
        'Bejerman': {
            TABLE_BEJERMAN_CONTACTOS: bejerman_contactos
        },
        'msg_cod': msg_cod,
        'timestamp': datetime.now().isoformat()
    }
    
    # Solo incluir tablas opcionales si tienen datos
    if ct_alertas_queries:
        payload[TABLE_ALERTAS_QUERIES] = ct_alertas_queries
    if ct_alertas_plantillas:
        payload[TABLE_ALERTAS_PLANTILLAS] = ct_alertas_plantillas
    if bejerman_perfiles:
        payload['Bejerman'][TABLE_BEJERMAN_PERFILES] = bejerman_perfiles
    
    return payload


def _insert_message_record(msg_cod, cfg_cod, contacto_valor, canal_cod, db_config):
    """Inserts message record in CT_Alertas_Mensajes."""
    conn = db_config.connect()
    cursor = conn.cursor()
    
    query = f"""
    INSERT INTO {TABLE_ALERTAS_MENSAJES} 
    (msg_Cod, msg_Wamid, msgcfg_Cod, msg_Destinatario, msg_Estado, msgcan_Cod)
    VALUES (?, '', ?, ?, 'PENDIENTE', ?)
    """
    
    cursor.execute(query, msg_cod, cfg_cod, contacto_valor, canal_cod)
    conn.commit()
    cursor.close()
    conn.close()


def _update_message_status(msg_cod, nuevo_estado, db_config):
    """Updates message status in CT_Alertas_Mensajes."""
    conn = db_config.connect()
    cursor = conn.cursor()
    
    query = f"""
    UPDATE {TABLE_ALERTAS_MENSAJES} 
    SET msg_Estado = ?, msg_FechaRespuesta = GETDATE()
    WHERE msg_Cod = ?
    """
    
    cursor.execute(query, nuevo_estado, msg_cod)
    conn.commit()
    cursor.close()
    conn.close()


def _register_execution(sch_cod, cfg_cod, cant_mensajes, alert, datos_query_list, destinatarios, db_config, errors):
    """Registers execution in CT_Scheduler_Alertas."""
    conn = db_config.connect()
    cursor = conn.cursor()
    hoy = datetime.now().date()
    
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


def _generate_unique_code():
    """Generates unique 6-character code."""
    timestamp = str(int(time.time()))[-4:]
    uuid_part = str(uuid.uuid4()).replace('-', '')[:2].upper()
    return f"{timestamp}{uuid_part}"
