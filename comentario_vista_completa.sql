/*
================================================================================
VISTA: VW_Alertas_Completa
================================================================================

PROPÓSITO:
Vista unificada que proporciona una visión completa y user-friendly de todas las 
configuraciones de alertas activas del sistema. Combina información organizacional 
y de programación temporal en un formato legible para dashboards y reportes.

FUNCIONALIDAD PRINCIPAL:
- Consolida datos de 6 tablas relacionadas en una sola vista
- Formatea horarios de 24h a 12h con AM/PM para mejor legibilidad
- Traduce códigos numéricos de días a nombres legibles (Lun-Vie, etc.)
- Muestra información completa del destinatario y cliente
- Incluye detalles del canal de comunicación y webhooks asociados
- Solo muestra configuraciones activas (activo = 1)

CASOS DE USO:
✓ Dashboard administrativo de alertas programadas
✓ Reportes ejecutivos de configuraciones activas
✓ Interfaz de usuario para gestión visual de alertas
✓ Auditoría rápida de qué alertas están configuradas para cada cliente
✓ Planificación y revisión de cronogramas de notificaciones

CAMPOS DE SALIDA:

IDENTIFICACIÓN:
- config_id: ID único de la configuración
- cliente: Nombre del cliente/empresa
- usuario: Nombre del destinatario de la alerta

CONTACTO:
- email: Dirección de correo electrónico del destinatario
- telefono: Número de teléfono para notificaciones (WhatsApp, SMS)

TIPO DE ALERTA:
- tipo_alerta: Código del tipo (BACKUP, CUENTAS, etc.)
- descripcion_alerta: Descripción detallada del propósito de la alerta
- canal: Método de envío (EMAIL, WHATSAPP, etc.)

PROGRAMACIÓN TEMPORAL:
- disparador: Tipo de activación (PERIODICO, MANUAL, WEBHOOK)
- frecuencia: Periodicidad (DIARIO, SEMANAL, MENSUAL, ANUAL)
- hora_envio: Hora formateada en formato 12h con AM/PM (ej: "09:30 AM")
- dias_semana: Días de la semana en formato legible:
  * "Lun-Vie" para días laborables (1,2,3,4,5)
  * "Lun-Sáb" para incluir sábado (1,2,3,4,5,6)  
  * "Lun-Dom" para toda la semana (1,2,3,4,5,6,7)
  * Días individuales como "Lun,Mié,Vie" para patrones personalizados
- dias_mes: Días específicos del mes para alertas mensuales (1-31)

INTEGRACIÓN:
- webhook_nombre: Nombre del webhook asociado (si aplica)
- estado: Estado legible de la configuración ("Activa" o "Inactiva")

RELACIONES DE TABLAS:
- CT_Alertas_Configuracion (principal) → CT_Alertas_Destinatarios → CT_Alertas_Clientes
- CT_Alertas_Configuracion → CT_Alertas_Tipos
- CT_Alertas_Configuracion → CT_Alertas_Canales  
- CT_Alertas_Configuracion → CT_Alertas_Webhooks (opcional)

EJEMPLOS DE RESULTADOS:
┌──────────────┬─────────┬───────┬─────────────────────┬───────────┬──────────┬─────────┬─────────────┐
│ cliente      │ usuario │ canal │ tipo_alerta         │ frecuencia │ hora_envio │ dias_semana │ estado  │
├──────────────┼─────────┼───────┼─────────────────────┼───────────┼──────────┼─────────────┼─────────┤
│ Constec      │ Tomy    │ EMAIL │ BACKUP             │ SEMANAL   │ 09:00 AM │ Lun-Vie     │ Activa  │
│ Constec      │ Tomy    │ WHATSAPP│ CUENTAS          │ MENSUAL   │ 08:00 AM │ NULL        │ Activa  │
└──────────────┴─────────┴───────┴─────────────────────┴───────────┴──────────┴─────────────┴─────────┘

FILTROS APLICADOS:
- Solo configuraciones activas (config.activo = 1)
- Excluye registros eliminados o deshabilitados

RENDIMIENTO:
- Vista optimizada con JOINs necesarios
- Índices recomendados en claves foráneas
- Cálculos de formato realizados en tiempo de consulta

MANTENIMIENTO:
- Actualizar lógica de formateo de días si se agregan nuevos patrones
- Revisar performance si el volumen de configuraciones crece significativamente
- Considerar materialización si se usa intensivamente en reportes

VERSIÓN: 1.0
CREADO: 2025-10-21
AUTOR: Sistema de Alertas CTAutomatizaciones
*/