# 🚀 Scheduler de Alertas Automático

## 📋 Descripción

Este sistema automatizado lee alertas desde una base de datos SQL Server y las programa automáticamente usando **APScheduler**. Cuando llega el momento configurado, envía webhooks HTTP y registra los resultados en un log.

## ✨ Características Principales

- 🔄 **Programación automática** de alertas desde base de datos
- 📅 **Múltiples frecuencias**: Diario, Semanal, Mensual
- 🔔 **Ejecución automática** de webhooks en horarios configurados
- 📝 **Logging completo** de todas las ejecuciones
- 🔍 **Monitoreo en tiempo real** de nuevas alertas
- 🧹 **Interfaz limpia** con mensajes fáciles de entender
- ⚡ **Refresco automático** cuando se detectan cambios

## 🛠️ Tecnologías Utilizadas

- **Python 3.x**
- **APScheduler** - Para programación de tareas
- **pyodbc** - Conexión a SQL Server
- **requests** - Envío de webhooks HTTP
- **python-dotenv** - Manejo de variables de entorno

## 📊 Tipos de Alertas Soportadas

| Frecuencia | Descripción | Campo Requerido |
|------------|-------------|----------------|
| `DIARIO` | Se ejecuta todos los días a la hora especificada | `hora_envio` |
| `SEMANAL` | Se ejecuta en días específicos de la semana | `hora_envio`, `dias_semana` |
| `MENSUAL` | Se ejecuta en días específicos de cada mes | `hora_envio`, `dias_mes` |
| `ANUAL` | Se ejecuta en días específicos de enero cada año | `hora_envio`, `dias_mes` |

## 🗃️ Estructura de Base de Datos

### Tabla: `ct_alertas_configuracion`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | int | ID único de la alerta |
| `tipo_alerta_id` | int | Tipo de alerta |
| `destinatario_id` | int | ID del destinatario |
| `canal_id` | int | ID del canal |
| `tipo_disparo` | nvarchar(40) | Tipo de disparo |
| `frecuencia` | nvarchar(40) | DIARIO/SEMANAL/MENSUAL/ANUAL |
| `hora_envio` | time | Hora de envío (HH:MM:SS) |
| `dias_semana` | nvarchar(40) | Días para alertas semanales (1-7) |
| `dias_mes` | nvarchar(40) | Días del mes para alertas mensuales/anuales |
| `webhook_id` | int | ID del webhook a ejecutar |
| `activo` | bit | Si la alerta está activa |
| `fecha_creacion` | datetime | Fecha de creación |

### Tabla: `ct_alertas_log`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `alerta_id` | int | ID de la alerta ejecutada |
| `fecha_ejecucion` | datetime | Cuándo se ejecutó |
| `resultado` | nvarchar | Resultado de la ejecución |

## ⚙️ Configuración

1. **Instalar dependencia adicional**:
   ```bash
   pip install python-dotenv
   ```

2. **Crear archivo de configuración**:
   Copia `.env.example` a `.env` y edita las credenciales:
   ```bash
   copy .env.example .env
   ```

3. **Configurar credenciales** en el archivo `.env`:
   ```env
   DB_DRIVER=ODBC Driver 17 for SQL Server
   DB_SERVER=tu_servidor
   DB_DATABASE=tu_base_datos
   DB_USER=tu_usuario
   DB_PASSWORD=tu_contraseña
   ```

## 🎯 Uso

1. **Activar entorno virtual**:
   ```bash
   .\venv\Scripts\Activate.ps1
   ```

2. **Ejecutar el scheduler**:
   ```bash
   python scheduler.py
   ```

3. **Detener el scheduler**:
   Presiona `Ctrl+C`

## 📺 Ejemplo de Salida

```
🚀 INICIANDO SCHEDULER DE ALERTAS
💫 Conectado a la base de datos
⚡ Programador automático activado

============================================================
📋 CARGANDO ALERTAS DESDE LA BASE DE DATOS
============================================================

🔍 Revisando Alerta #1:
   📅 Frecuencia: SEMANAL
   ⏰ Hora: 09:00:00
   📆 Días: 1,2,3,4,5
   ✅ PROGRAMADA - Cada Lunes, Martes, Miércoles, Jueves, Viernes a las 09:00

🔍 Revisando Alerta #2:
   📅 Frecuencia: MENSUAL
   ⏰ Hora: 08:00:00
   📆 Días del mes: 1,15
   ✅ PROGRAMADA - Días 1, 15 de cada mes a las 08:00

🔍 Revisando Alerta #3:
   📅 Frecuencia: ANUAL
   ⏰ Hora: 10:00:00
   📆 Días del mes: 1
   ✅ PROGRAMADA - Días 1 de enero cada año a las 10:00

============================================================
📊 RESUMEN:
   ✅ Alertas programadas: 3
   ⚠️  Alertas omitidas: 0
   📝 Total procesadas: 3
============================================================

🔄 MODO MONITOREO ACTIVADO
   El sistema revisa nuevas alertas cada minuto...
   Presiona Ctrl+C para detener
```

## 🔔 Ejecución de Alertas

Cuando se ejecuta una alerta, verás:

```
🔔 [14:30:15] EJECUTANDO ALERTA #1
   📡 Enviando webhook a: https://api.constec.ar/webhook/123
   ✅ Webhook enviado exitosamente (Código: 200)
   📝 Resultado guardado en el log
   ✅ Alerta completada
```

## 📅 Formato de Días de la Semana

El campo `dias_semana` usa el formato:
- `1` = Lunes
- `2` = Martes  
- `3` = Miércoles
- `4` = Jueves
- `5` = Viernes
- `6` = Sábado
- `7` = Domingo

**Ejemplo**: `1,2,3,4,5` = Lunes a Viernes

## � Formato de Días del Mes

El campo `dias_mes` usa números separados por comas:
- `1` = Día 1 del mes
- `15` = Día 15 del mes  
- `1,15,30` = Días 1, 15 y 30 del mes

**Ejemplo**: Para alertas mensuales el día 1 y 15: `1,15`

## �🔍 Monitoreo Automático

- El sistema revisa **cada minuto** si hay nuevas alertas
- Cuando detecta cambios, **recarga automáticamente** la configuración
- La pantalla se **limpia y actualiza** mostrando solo información fresca

## ⚠️ Validaciones

El sistema automáticamente omite alertas que:
- No tienen `hora_envio` definida
- No tienen `frecuencia` definida  
- Alertas SEMANALES sin `dias_semana`
- Alertas MENSUALES/ANUALES sin `dias_mes`
- Tienen formato de hora inválido

## �️ Crear Tabla de Logs

Ejecuta el archivo `create_log_table.sql` en tu base de datos para crear la tabla de logs necesaria.