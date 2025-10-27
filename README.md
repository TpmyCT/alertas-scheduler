# 📬 Scheduler de Alertas

Sistema de alertas automatizado con arquitectura stateless que consulta una vista SQL cada minuto y aplica filtros en Python para determinar qué alertas enviar.

## ✨ Características

- 🔄 **Polling cada minuto** sincronizado al segundo 00
- 🎯 **3 filtros en Python**: ventana de hora, frecuencia, anti-duplicados
- 📧 **Notificaciones por email** cuando hay errores
- 📝 **Logging detallado** con emojis y timestamps
- 🔁 **Sin estado** - cada iteración es independiente
- ⚡ **Manejo robusto** de errores sin detener el procesamiento

## 🛠️ Tecnologías

- **Python 3.x**
- **pyodbc** - Conexión a SQL Server
- **requests** - Envío de webhooks HTTP
- **smtplib** - Envío de emails (incluido en Python)
- **python-dotenv** - Variables de entorno

## 🗄️ Base de Datos Requerida

### Vista: `VW_Scheduler_Alertas`
Debe devolver todas las alertas activas con estos campos:
- `config_id`, `tipo_disparo`, `frecuencia`, `hora_envio`, `dias_semana`, `dias_mes`
- `tipo_codigo`, `empresa_codigo`, `empresa_conexion`, `persona_codigo`, `canal_codigo`
- `webhook_url` y campos descriptivos

### Tabla: `CT_Alertas_Mensajes`
Para tracking de mensajes enviados:
```sql
CREATE TABLE CT_Alertas_Mensajes (
    msg_id INT IDENTITY PRIMARY KEY,
    msg_Cod VARCHAR(6),
    msgcfg_Cod VARCHAR(6),
    msg_Estado VARCHAR(20),
    msg_FechaEnvio DATETIME,
    msg_FechaRespuesta DATETIME
);
```

### Tabla: `CT_Alertas_Admin_Emails`
Para destinatarios de notificaciones de errores:
```sql
CREATE TABLE CT_Alertas_Admin_Emails (
    adm_id INT IDENTITY PRIMARY KEY,
    adm_Email VARCHAR(100),
    adm_Nombre VARCHAR(50),
    adm_Activo BIT DEFAULT 1
);
```

## ⚙️ Configuración

### 1. Variables de Entorno
Copia `.env.example` a `.env` y configura:
```env
# Base de Datos
DB_SERVER=tu_servidor
DB_DATABASE=tu_base_datos
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña

# SMTP (para notificaciones de errores)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_app_password
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar Destinatarios de Errores
```sql
INSERT INTO CT_Alertas_Admin_Emails (adm_Email, adm_Nombre) VALUES
('admin@empresa.com', 'Administrador'),
('soporte@empresa.com', 'Equipo Soporte');
```

## 🚀 Uso

```bash
python main.py
```

## 📊 Flujo de Ejecución

1. **Sincronización**: Se alinea al próximo minuto exacto
2. **Consulta**: `SELECT * FROM VW_Scheduler_Alertas`
3. **Filtros por alerta**:
   - ⏱️ Ventana de ±2 minutos de la hora configurada
   - 📅 Día válido según frecuencia (DIARIO/SEMANAL/MENSUAL)
   - 🔁 No enviada hoy (consulta `CT_Alertas_Mensajes`)
4. **Envío**: Si pasa filtros → INSERT BD → POST webhook → UPDATE estado
5. **Notificación**: Si hay errores → Email HTML a administradores

## 📋 Logging

```
⏰ [14:25:00] Consultando alertas...
📊 Encontradas 5 alertas en total
🔍 Evaluando alerta 000001...
⏱️ Alerta 000002 fuera de ventana
📅 Alerta 000003 no aplica hoy
🔁 Alerta 000004 ya enviada hoy
✉️ Enviando alerta 000001...
✅ Alerta 000001 enviada
📬 Total enviadas: 1 | Errores: 0
```

## 🔧 Arquitectura

- **Stateless**: Sin caché ni estado entre iteraciones
- **Vista SQL simple**: Solo `WHERE activo=1` (sin filtros complejos)
- **Filtros en Python**: Lógica flexible sin impacto en BD
- **Manejo de errores**: Tipificado y sin interrumpir procesamiento
- **Notificaciones HTML**: Emails visuales con detalles de errores