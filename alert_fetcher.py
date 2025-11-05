"""
Alert Fetcher - Retrieves active alerts from database
"""

import logging
from database_config import DatabaseConfig
from table_names import (
    TABLE_ALERTAS_CONFIG,
    TABLE_ALERTAS_TIPOS,
    TABLE_ALERTAS_CANALES,
    TABLE_EMPRESAS,
    TABLE_ALERTAS_WEBHOOKS,
    TABLE_ALERTAS_QUERIES,
    TABLE_ALERTAS_PLANTILLAS
)

logger = logging.getLogger(__name__)


def fetch_all_active_alerts(db_config: DatabaseConfig):
    """Fetches all active alerts with JOINs from CT_Alertas_Config."""
    conn = db_config.connect()
    cursor = conn.cursor()
    
    query = f"""
    SELECT 
        cfg.*, 
        tip.*, 
        can.*, 
        emp.*,
        wbh.*,
        qry.*,
        plt.*
    FROM {TABLE_ALERTAS_CONFIG} cfg
    INNER JOIN {TABLE_ALERTAS_TIPOS} tip ON tip.tip_Cod = cfg.cfgtip_Cod
    INNER JOIN {TABLE_ALERTAS_CANALES} can ON can.can_Cod = cfg.cfgcan_Cod
    LEFT JOIN {TABLE_EMPRESAS} emp ON emp.emp_Cod = cfg.cfgemp_Cod
    LEFT JOIN {TABLE_ALERTAS_WEBHOOKS} wbh ON wbh.wbh_Cod = tip.tipwbh_Cod
    LEFT JOIN {TABLE_ALERTAS_QUERIES} qry ON qry.qrytip_Cod = tip.tip_Cod 
        AND (qry.qryprf_Cod = cfg.cfgprf_Cod OR (cfg.cfgprf_Cod IS NULL AND qry.qryprf_Cod IS NULL))
        AND (qry.qry_Activo = 1 OR qry.qry_Activo IS NULL)
    LEFT JOIN {TABLE_ALERTAS_PLANTILLAS} plt ON plt.plttip_Cod = tip.tip_Cod 
        AND plt.pltcan_Cod = can.can_Cod 
        AND (plt.pltprf_Cod = cfg.cfgprf_Cod OR (cfg.cfgprf_Cod IS NULL AND plt.pltprf_Cod IS NULL))
        AND (plt.plt_Activo = 1 OR plt.plt_Activo IS NULL)
    WHERE cfg.cfg_Activo = 1 
        AND tip.tip_Activo = 1 
        AND can.can_Activo = 1
        AND (emp.emp_Activo = 1 OR emp.emp_Activo IS NULL)
        AND (wbh.wbh_Activo = 1 OR wbh.wbh_Activo IS NULL)
    """
    
    logger.info("📋 Ejecutando query de consulta de alertas...")
    cursor.execute(query)
    columnas = [desc[0] for desc in cursor.description]
    
    alertas = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    logger.info(f"📊 Encontradas {len(alertas)} alertas activas")
    return alertas
