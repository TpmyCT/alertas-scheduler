"""
Alert Scheduler - Main Entry Point

Orquestador simple que coordina el procesamiento de alertas.
Cada función hace una cosa clara y específica.
"""

import time
from datetime import datetime
from typing import List, Dict, Any
import logging

from logger_config import setup_logging
from database_config import DatabaseConfig
from webhook_sender import WebhookSender
from email_notifier import EmailNotifier
from alert_fetcher import fetch_all_active_alerts
from alert_filters import filter_by_date_and_frequency, filter_by_time_window
from alert_processor import process_and_send_alerts, show_alerts_summary
from scheduler_utils import (
    wait_until_next_minute,
    calculate_seconds_until_next_minute,
    create_summary,
    log_critical_error,
    finalize_cycle
)

logger: logging.Logger = setup_logging()


class AlertScheduler:
    """Scheduler principal que orquesta el procesamiento de alertas."""
    
    def __init__(self) -> None:
        """Inicializa los componentes necesarios."""
        self.db: DatabaseConfig = DatabaseConfig()
        self.webhook: WebhookSender = WebhookSender()
        self.email = EmailNotifier(self.db)
    
    def run(self) -> None:
        """Loop principal: sincroniza y ejecuta cada minuto."""
        # Sincronizar al próximo minuto exacto antes de empezar
        wait_until_next_minute()
        logger.info("🔄 Scheduler active")
        logger.info("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Ejecutar un ciclo completo
                self.run_cycle()
                
                # Calcular tiempo hasta el próximo minuto
                seconds: float = calculate_seconds_until_next_minute()
                logger.info(f"⏳ Next run in {seconds:.1f}s")
                time.sleep(seconds)
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopped by user")
    
    def run_cycle(self) -> None:
        """Un ciclo completo: consultar → filtrar → procesar → enviar."""
        errors: List[Dict[str, Any]] = []
        summary: Dict[str, Any] = create_summary()
        
        try:
            logger.info(f"⏰ [{datetime.now().strftime('%H:%M:%S')}] Checking alerts...")
            
            # 1. Traer todas las alertas activas de la BD
            alerts: List[Dict[str, Any]] = fetch_all_active_alerts(self.db)
            summary['total_alertas'] = len(alerts)
            
            if not alerts:
                logger.info("🔍 No alerts configured")
                return
            
            # 2. Filtrar por día/frecuencia y que no se hayan enviado hoy
            pending: List[Dict[str, Any]] = filter_by_date_and_frequency(alerts, errors)
            logger.info(f"📊 {len(alerts)} total | {len(pending)} pending today")
            
            if not pending:
                return
            
            # 3. Filtrar por ventana de tiempo (±2 minutos)
            to_send: List[Dict[str, Any]] = filter_by_time_window(pending, errors)
            if not to_send:
                return
            
            # 4. Mostrar resumen de lo que se va a enviar
            show_alerts_summary(to_send, self.db)
            
            # 5. Procesar y enviar cada alerta
            process_and_send_alerts(to_send, errors, summary, self.db, self.webhook)
            
        except Exception as e:
            log_critical_error(e, errors)
            logger.error(f"❌ Critical error: {e}")
        finally:
            # Finalizar: enviar notificaciones de errores si hubo
            finalize_cycle(errors, summary, self.email, logger)


def main() -> None:
    """Punto de entrada principal - inicia el scheduler."""
    scheduler: AlertScheduler = AlertScheduler()
    scheduler.run()


if __name__ == "__main__":
    main()
