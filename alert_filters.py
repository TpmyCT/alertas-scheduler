"""
Alert Filters - Filters alerts by day, frequency, time window, and duplicates
"""

import traceback
from datetime import datetime
from database_config import DatabaseConfig


def filter_by_date_and_frequency(alerts, errors):
    """Filters alerts that should run today and haven't been sent yet."""
    pending = []
    for alert in alerts:
        if _should_run_today(alert, errors) and _not_sent_today(alert, errors):
            pending.append(alert)
    return pending


def filter_by_time_window(alerts, errors):
    """Filters alerts within ±2 minute time window."""
    to_process = []
    for alert in alerts:
        trigger_type = alert.get('cfg_TipoDisparo', '').upper()
        
        if trigger_type == 'PERIODICO' and _is_within_window_periodico(alert, errors):
            to_process.append(alert)
        elif trigger_type == 'PUNTUAL' and _is_within_window_puntual(alert, errors):
            to_process.append(alert)
    
    return to_process


# ------------------------------------------------------------------------
# PRIVATE HELPERS
# ------------------------------------------------------------------------

def _should_run_today(alert, errors):
    """Checks if alert should run today based on frequency."""
    try:
        trigger_type = alert.get('cfg_TipoDisparo', '').upper()
        today = datetime.now()
        
        if trigger_type == 'PERIODICO':
            return _check_periodico_frequency(alert, today, errors)
        elif trigger_type == 'PUNTUAL':
            return _check_puntual_dates(alert, today)
        else:
            _add_error(errors, 'FILTRADO', alert['cfg_Cod'], 
                      f'Unknown trigger type: {trigger_type}', alert)
            return False
    except Exception as e:
        _add_error(errors, 'FILTRADO', alert.get('cfg_Cod', 'UNKNOWN'),
                  f'Error validating trigger type: {str(e)}', alert, e)
        return False


def _check_periodico_frequency(alert, today, errors):
    """Checks if PERIODICO alert should run today."""
    freq = alert.get('cfg_Frecuencia', '').upper()
    
    if freq == 'DIARIO':
        return True
    
    elif freq == 'SEMANAL':
        dias_semana = alert.get('cfg_DiasSemana', '')
        if not dias_semana:
            _add_error(errors, 'FILTRADO', alert['cfg_Cod'],
                      'cfg_DiasSemana empty for SEMANAL frequency', alert)
            return False
        
        dia_hoy = today.isoweekday()  # 1=Mon, 7=Sun
        dias_permitidos = [int(d.strip()) for d in dias_semana.split(',') if d.strip().isdigit()]
        return dia_hoy in dias_permitidos
    
    elif freq == 'MENSUAL':
        dias_mes = alert.get('cfg_DiasMes', '')
        if not dias_mes:
            _add_error(errors, 'FILTRADO', alert['cfg_Cod'],
                      'cfg_DiasMes empty for MENSUAL frequency', alert)
            return False
        
        dias_permitidos = [int(d.strip()) for d in dias_mes.split(',') if d.strip().isdigit()]
        return today.day in dias_permitidos
    
    elif freq == 'ANUAL':
        dias_mes = alert.get('cfg_DiasMes', '')
        if not dias_mes:
            return False
        dias_permitidos = [int(d.strip()) for d in dias_mes.split(',') if d.strip().isdigit()]
        return today.day in dias_permitidos
    
    else:
        _add_error(errors, 'FILTRADO', alert['cfg_Cod'],
                  f'Unknown frequency: {freq}', alert)
        return False


def _check_puntual_dates(alert, today):
    """Checks if today matches any PUNTUAL date."""
    fechas_puntuales = alert.get('cfg_FechasPuntuales', '')
    if not fechas_puntuales:
        return False
    
    for fecha_str in str(fechas_puntuales).split(','):
        fecha_str = fecha_str.strip()
        try:
            try:
                fecha_puntual = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                fecha_puntual = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M')
            
            if fecha_puntual.date() == today.date():
                return True
        except ValueError:
            continue
    
    return False


def _not_sent_today(alert, errors):
    """Checks alert wasn't sent today (anti-duplicate filter)."""
    try:
        from database_config import DatabaseConfig
        db_config = DatabaseConfig()
        conn = db_config.connect()
        cursor = conn.cursor()
        
        query = """
        SELECT COUNT(*) 
        FROM CT_Scheduler_Alertas sa
        INNER JOIN CT_Alertas_Config cfg ON cfg.cfg_Cod = sa.schcfg_Cod
        WHERE sa.schcfg_Cod = ? 
            AND cfg.cfgcan_Cod = ?
            AND CAST(sa.sch_Fecha AS DATE) = CAST(GETDATE() AS DATE)
            AND sa.sch_Estado = 'OK'
        """
        
        cursor.execute(query, alert['cfg_Cod'], alert['cfgcan_Cod'])
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return count == 0
    except Exception as e:
        _add_error(errors, 'ANTI_DUPLICADO', alert.get('cfg_Cod', 'UNKNOWN'),
                  f'Error checking duplicates: {str(e)}', alert, e)
        return False


def _is_within_window_periodico(alert, errors):
    """Checks if PERIODICO alert is within ±2 minute window."""
    try:
        hora_actual = datetime.now().time()
        hora_alerta = alert['cfg_HoraEnvio']
        
        if not hora_alerta:
            _add_error(errors, 'FILTRADO', alert['cfg_Cod'],
                      'cfg_HoraEnvio is NULL', alert)
            return False
        
        minutos_actual = hora_actual.hour * 60 + hora_actual.minute
        minutos_alerta = hora_alerta.hour * 60 + hora_alerta.minute
        
        diferencia = abs(minutos_actual - minutos_alerta)
        diferencia = min(diferencia, 1440 - diferencia)  # Handle day change
        
        return diferencia <= 2
        
    except Exception as e:
        _add_error(errors, 'FILTRADO', alert.get('cfg_Cod', 'UNKNOWN'),
                  f'Error validating time window: {str(e)}', alert, e)
        return False


def _is_within_window_puntual(alert, errors):
    """Checks if any PUNTUAL date is within ±2 minute window."""
    try:
        fechas_puntuales = alert.get('cfg_FechasPuntuales', '')
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
        _add_error(errors, 'FILTRADO', alert.get('cfg_Cod', 'UNKNOWN'),
                  f'Error checking puntual time: {str(e)}', alert, e)
        return False


def _add_error(errors, error_type, config_id, message, alert_data, exception=None):
    """Adds error to error list."""
    errors.append({
        'timestamp': datetime.now(),
        'tipo_error': error_type,
        'config_id': config_id,
        'mensaje': message,
        'stack_trace': traceback.format_exc() if exception else 'N/A',
        'datos_alerta': alert_data
    })
