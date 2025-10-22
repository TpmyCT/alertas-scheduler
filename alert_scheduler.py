"""
Módulo para la programación y validación de alertas.
Maneja la lógica de programación de trabajos con APScheduler según diferentes frecuencias.
"""

from apscheduler.schedulers.background import BackgroundScheduler


class AlertScheduler:
    """Maneja la programación de alertas con diferentes frecuencias."""
    
    def __init__(self, webhook_sender):
        """
        Inicializa el programador de alertas.
        
        Args:
            webhook_sender: Instancia de WebhookSender para ejecutar alertas
        """
        self.scheduler = BackgroundScheduler()
        self.webhook_sender = webhook_sender
        self.dias_semana_nombres = {
            '1': 'Lunes', '2': 'Martes', '3': 'Miércoles', 
            '4': 'Jueves', '5': 'Viernes', '6': 'Sábado', '7': 'Domingo'
        }
    
    def iniciar(self):
        """Inicia el scheduler en segundo plano."""
        self.scheduler.start()
    
    def detener(self):
        """Detiene el scheduler."""
        self.scheduler.shutdown()
    
    def limpiar_trabajos(self):
        """Elimina todos los trabajos programados."""
        self.scheduler.remove_all_jobs()
    
    def validar_datos_alerta(self, alerta):
        """
        Valida que una alerta tenga todos los datos necesarios para ser programada.
        
        Args:
            alerta (dict): Diccionario con los datos de la alerta
            
        Returns:
            tuple: (es_valida: bool, mensaje_error: str)
        """
        if not alerta["hora_envio"] or alerta["hora_envio"] == "None":
            return False, "Falta la hora de envío"
        
        if not alerta["frecuencia"] or alerta["frecuencia"] == "None":
            return False, "Falta la frecuencia (diario/semanal/mensual)"
        
        # Validar campos específicos según frecuencia
        if alerta["frecuencia"] == "SEMANAL":
            if not alerta["dias_semana"] or alerta["dias_semana"] == "None":
                return False, "Falta definir los días de la semana"
        
        elif alerta["frecuencia"] in ["MENSUAL", "ANUAL"]:
            if not alerta["dias_mes"] or alerta["dias_mes"] == "None":
                return False, "Falta definir los días del mes"
        
        # Validar formato de hora
        try:
            hora, minuto, *_ = map(int, alerta["hora_envio"].split(":"))
            if not (0 <= hora <= 23 and 0 <= minuto <= 59):
                return False, f"Hora inválida: '{alerta['hora_envio']}'"
        except (ValueError, AttributeError):
            return False, f"Formato de hora inválido: '{alerta['hora_envio']}'"
        
        return True, "Validación exitosa"
    
    def convertir_dia_bd_a_scheduler(self, dia_bd):
        """
        Convierte día de formato BD (1-7) a formato APScheduler (0-6).
        
        Args:
            dia_bd (str): Día en formato BD (1=Lunes, 7=Domingo)
            
        Returns:
            str: Día en formato APScheduler (0=Lunes, 6=Domingo)
        """
        if dia_bd == '7':  # Domingo especial
            return '6'
        else:
            return str(int(dia_bd) - 1)
    
    def programar_alerta_diaria(self, alerta, hora, minuto):
        """Programa una alerta diaria."""
        try:
            self.scheduler.add_job(
                self.webhook_sender.ejecutar_alerta_completa,
                trigger="cron",
                hour=hora,
                minute=minuto,
                args=[alerta],
                id=f"alerta_{alerta['id']}_diario",
                replace_existing=True
            )
            print(f"   ✅ PROGRAMADA - Todos los días a las {hora:02d}:{minuto:02d}")
            return True
        except Exception as e:
            print(f"   ❌ ERROR al programar: {e}")
            return False
    
    def programar_alerta_semanal(self, alerta, hora, minuto):
        """Programa una alerta semanal."""
        try:
            dias = alerta["dias_semana"].split(",")
            dias_nombres = []
            
            for d in dias:
                d = d.strip()
                if d:  # Solo agregar si el día no está vacío
                    dia_scheduler = self.convertir_dia_bd_a_scheduler(d)
                    
                    self.scheduler.add_job(
                        self.webhook_sender.ejecutar_alerta_completa,
                        trigger="cron",
                        day_of_week=dia_scheduler,
                        hour=hora,
                        minute=minuto,
                        args=[alerta],
                        id=f"alerta_{alerta['id']}_{d}",
                        replace_existing=True
                    )
                    dias_nombres.append(self.dias_semana_nombres.get(d, f'Día {d}'))
            
            print(f"   ✅ PROGRAMADA - Cada {', '.join(dias_nombres)} a las {hora:02d}:{minuto:02d}")
            return True
        except Exception as e:
            print(f"   ❌ ERROR al programar: {e}")
            return False
    
    def programar_alerta_mensual(self, alerta, hora, minuto):
        """Programa una alerta mensual."""
        try:
            dias = alerta["dias_mes"].split(",")
            dias_nombres = []
            
            for d in dias:
                d = d.strip()
                if d and d.isdigit() and 1 <= int(d) <= 31:
                    self.scheduler.add_job(
                        self.webhook_sender.ejecutar_alerta_completa,
                        trigger="cron",
                        day=int(d),
                        hour=hora,
                        minute=minuto,
                        args=[alerta],
                        id=f"alerta_{alerta['id']}_mensual_{d}",
                        replace_existing=True
                    )
                    dias_nombres.append(d)
            
            print(f"   ✅ PROGRAMADA - Días {', '.join(dias_nombres)} de cada mes a las {hora:02d}:{minuto:02d}")
            return True
        except Exception as e:
            print(f"   ❌ ERROR al programar: {e}")
            return False
    
    def programar_alerta_anual(self, alerta, hora, minuto):
        """Programa una alerta anual."""
        try:
            dias = alerta["dias_mes"].split(",")
            dias_nombres = []
            
            for d in dias:
                d = d.strip()
                if d and d.isdigit() and 1 <= int(d) <= 31:
                    self.scheduler.add_job(
                        self.webhook_sender.ejecutar_alerta_completa,
                        trigger="cron",
                        month=1,  # Enero
                        day=int(d),
                        hour=hora,
                        minute=minuto,
                        args=[alerta],
                        id=f"alerta_{alerta['id']}_anual_{d}",
                        replace_existing=True
                    )
                    dias_nombres.append(d)
            
            print(f"   ✅ PROGRAMADA - Días {', '.join(dias_nombres)} de enero cada año a las {hora:02d}:{minuto:02d}")
            return True
        except Exception as e:
            print(f"   ❌ ERROR al programar: {e}")
            return False
    
    def programar_alerta(self, alerta):
        """
        Programa una alerta según su frecuencia configurada.
        
        Args:
            alerta (dict): Diccionario con los datos de la alerta
            
        Returns:
            bool: True si la alerta fue programada exitosamente
        """
        # Validar datos de la alerta
        es_valida, mensaje_error = self.validar_datos_alerta(alerta)
        if not es_valida:
            print(f"   ❌ NO SE PUEDE PROGRAMAR - {mensaje_error}")
            return False
        
        # Extraer hora y minuto
        hora, minuto, *_ = map(int, alerta["hora_envio"].split(":"))
        
        # Programar según frecuencia
        frecuencia = alerta["frecuencia"].upper()
        
        if frecuencia == "DIARIO":
            return self.programar_alerta_diaria(alerta, hora, minuto)
        elif frecuencia == "SEMANAL":
            return self.programar_alerta_semanal(alerta, hora, minuto)
        elif frecuencia == "MENSUAL":
            return self.programar_alerta_mensual(alerta, hora, minuto)
        elif frecuencia == "ANUAL":
            return self.programar_alerta_anual(alerta, hora, minuto)
        else:
            print(f"   ❌ FRECUENCIA NO SOPORTADA: '{alerta['frecuencia']}'")
            return False