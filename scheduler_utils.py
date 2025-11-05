"""
Scheduler Utils - Helper functions for timing and summaries
"""

import time
import traceback
from datetime import datetime, timedelta


def wait_until_next_minute():
    """Waits until the next exact minute."""
    seconds = calculate_seconds_until_next_minute()
    print(f"🚀 Syncing to next minute... ({seconds:.1f}s)")
    time.sleep(seconds)


def calculate_seconds_until_next_minute():
    """Calculates seconds until next exact minute."""
    now = datetime.now()
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    return (next_minute - now).total_seconds()


def create_summary():
    """Creates execution summary dictionary."""
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


def log_critical_error(exception, errors):
    """Logs critical error."""
    errors.append({
        'timestamp': datetime.now(),
        'tipo_error': 'CRITICAL',
        'config_id': 'N/A',
        'mensaje': f'Critical error: {str(exception)}',
        'stack_trace': traceback.format_exc(),
        'datos_alerta': None
    })


def finalize_cycle(errors, summary, email_notifier, logger):
    """Finalizes cycle: updates summary and sends notifications."""
    summary['timestamp_fin'] = datetime.now()
    summary['total_errores'] = len(errors)
    
    if summary['alertas_enviadas'] > 0 or errors:
        logger.info(f"\n📊 Sent: {summary['alertas_enviadas']} | Errors: {summary['total_errores']}")
    
    if errors:
        try:
            email_notifier.enviar_notificacion_errores(errors, summary)
        except Exception as e:
            logger.error(f"❌ Error sending notifications: {e}")
