"""
Módulo para la carga y monitoreo de alertas desde la base de datos.
Maneja la obtención de configuraciones de alertas y la detección de cambios.
"""

import os
from datetime import datetime


class AlertLoader:
    """Maneja la carga de alertas desde la base de datos y monitoreo de cambios."""
    
    def __init__(self, db_connection, alert_scheduler):
        """
        Inicializa el cargador de alertas.
        
        Args:
            db_connection: Conexión activa a la base de datos
            alert_scheduler: Instancia de AlertScheduler para programar alertas
        """
        self.db_connection = db_connection
        self.alert_scheduler = alert_scheduler
        self.ultima_revision = datetime.now()
    
    def obtener_alertas_activas(self):
        """
        Obtiene todas las alertas activas desde la base de datos.
        
        Returns:
            list: Lista de diccionarios con datos de alertas activas
        """
        with self.db_connection.cursor() as cur:
            cur.execute("""
                SELECT id, tipo_alerta_id, destinatario_id, canal_id, tipo_disparo, 
                       frecuencia, hora_envio, dias_semana, dias_mes, webhook_id
                FROM ct_alertas_configuracion
                WHERE activo = 1
            """)
            
            alertas = []
            for row in cur.fetchall():
                alerta = {
                    "id": row.id,
                    "tipo_alerta_id": row.tipo_alerta_id,
                    "destinatario_id": row.destinatario_id,
                    "canal_id": row.canal_id,
                    "tipo_disparo": row.tipo_disparo,
                    "frecuencia": row.frecuencia,
                    "hora_envio": str(row.hora_envio) if row.hora_envio else None,
                    "dias_semana": str(row.dias_semana) if row.dias_semana else None,
                    "dias_mes": str(row.dias_mes) if row.dias_mes else None,
                    "webhook_id": row.webhook_id
                }
                alertas.append(alerta)
            
            return alertas
    
    def mostrar_informacion_alerta(self, alerta):
        """
        Muestra información detallada de una alerta en consola.
        
        Args:
            alerta (dict): Diccionario con los datos de la alerta
        """
        print(f"\n🔍 Revisando Alerta #{alerta['id']}:")
        print(f"   📅 Frecuencia: {alerta['frecuencia'] or 'NO DEFINIDA'}")
        print(f"   ⏰ Hora: {alerta['hora_envio'] or 'NO DEFINIDA'}")
        
        if alerta['frecuencia'] == 'SEMANAL':
            print(f"   📆 Días: {alerta['dias_semana'] or 'NO DEFINIDOS'}")
        elif alerta['frecuencia'] == 'MENSUAL':
            print(f"   📆 Días del mes: {alerta['dias_mes'] or 'NO DEFINIDOS'}")
        elif alerta['frecuencia'] == 'ANUAL':
            print(f"   📆 Días del mes: {alerta['dias_mes'] or 'NO DEFINIDOS'}")
    
    def limpiar_pantalla(self):
        """Limpia la pantalla de la consola."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def cargar_alertas(self, es_recarga=False):
        """
        Carga y programa todas las alertas activas desde la base de datos.
        
        Args:
            es_recarga (bool): Si es True, limpia la pantalla antes de mostrar info
            
        Returns:
            dict: Estadísticas de la carga (programadas, omitidas, total)
        """
        if es_recarga:
            self.limpiar_pantalla()
            print("🔄 RECARGANDO CONFIGURACIÓN...")
            print()
        
        print("=" * 60)
        print("📋 CARGANDO ALERTAS DESDE LA BASE DE DATOS")
        print("=" * 60)
        
        # Obtener alertas desde BD
        alertas = self.obtener_alertas_activas()
        
        # Contadores para estadísticas
        alertas_programadas = 0
        alertas_omitidas = 0
        alertas_cargadas = len(alertas)
        
        # Procesar cada alerta
        for alerta in alertas:
            self.mostrar_informacion_alerta(alerta)
            
            resultado = self.alert_scheduler.programar_alerta(alerta)
            if resultado:
                alertas_programadas += 1
            else:
                alertas_omitidas += 1
        
        # Mostrar resumen
        print("\n" + "=" * 60)
        print(f"📊 RESUMEN:")
        print(f"   ✅ Alertas programadas: {alertas_programadas}")
        print(f"   ⚠️  Alertas omitidas: {alertas_omitidas}")
        print(f"   📝 Total procesadas: {alertas_cargadas}")
        print("=" * 60)
        
        return {
            'programadas': alertas_programadas,
            'omitidas': alertas_omitidas,
            'total': alertas_cargadas
        }
    
    def verificar_cambios(self):
        """
        Verifica si hay nuevas alertas en la base de datos desde la última revisión.
        Si encuentra cambios, recarga todas las alertas.
        
        Returns:
            bool: True si se detectaron cambios y se recargó, False en caso contrario
        """
        try:
            with self.db_connection.cursor() as cur:
                # Verificar por fecha_creacion ya que fecha_modificacion no existe
                cur.execute("""
                    SELECT COUNT(*) FROM ct_alertas_configuracion
                    WHERE fecha_creacion > ?
                """, (self.ultima_revision,))
                count = cur.fetchone()[0]
            
            if count > 0:
                print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] ¡NUEVAS ALERTAS DETECTADAS!")
                print(f"    Se encontraron {count} alertas nuevas en la base de datos")
                print("    Recargando configuración...")
                
                # Limpiar trabajos existentes y recargar
                self.alert_scheduler.limpiar_trabajos()
                self.cargar_alertas(es_recarga=True)
                self.ultima_revision = datetime.now()
                
                print("\n🔄 MODO MONITOREO REACTIVADO")
                print("   El sistema sigue revisando nuevas alertas cada minuto...")
                print("   Presiona Ctrl+C para detener\n")
                return True
                
        except Exception as e:
            print(f"⚠️  Error al verificar cambios: {e}")
        
        return False