# 📬 Scheduler de Alertas Multi-Tenant

Sistema de alertas automatizado con arquitectura stateless que:
- Se sincroniza al minuto exacto (segundo 00)
- Consulta alertas desde SQL Server con JOINs a tablas relacionadas
- Aplica filtros en Python: frecuencia/día, ventana horaria (±2 min), anti-duplicados
- Obtiene destinatarios desde bases Bejerman por empresa
- Ejecuta queries dinámicos y procesa plantillas
- Envía webhooks con payload completo por cada destinatario

## ✨ Características

- 🔄 **Polling sincronizado** cada minuto al segundo 00
- 🎯 **Arquitectura multi-tenant** con bases Bejerman por empresa
- 📋 **Tipos de alerta**: PERIODICO (DIARIO/SEMANAL/MENSUAL/ANUAL) y PUNTUAL (fechas específicas)
- 👥 **Modos de destinatarios**: INDIVIDUAL (persona específica) o PERFIL (múltiples por perfil)
- 🔍 **Queries dinámicos** con parámetros y placeholders en plantillas
- 📧 **Notificaciones por email** cuando hay errores con reportes HTML
- 📝 **Logging simplificado** y directo
- 🔁 **Sin estado** - cada iteración es independiente
- ⚡ **Manejo robusto** de errores sin detener el procesamiento

## 🛠️ Tecnologías

- **Python 3.13+**
- **pyodbc** - Conexión a SQL Server
- **requests** - Envío de webhooks HTTP
- **smtplib** - Envío de emails (incluido en Python)
- **python-dotenv** - Variables de entorno

## 🗄️ Base de Datos Requerida

### Tablas Principales

#### CT_Alertas_Config
Configuración de alertas:
- `cfg_Cod` - Código único de alerta
- `cfg_TipoDisparo` - 'PERIODICO' o 'PUNTUAL'
- `cfg_Frecuencia` - 'DIARIO', 'SEMANAL', 'MENSUAL', 'ANUAL' (solo PERIODICO)
- `cfg_HoraEnvio` - Hora de envío formato TIME (solo PERIODICO)
- `cfg_FechasPuntuales` - Fechas/horas separadas por comas (solo PUNTUAL)
- `cfg_DiasSemana` - Días 1-7 separados por comas (SEMANAL)
- `cfg_DiasMes` - Días 1-31 separados por comas (MENSUAL/ANUAL)
- `cfgtip_Cod`, `cfgcan_Cod`, `cfgemp_Cod`, `cfgper_Cod`, `cfgprf_Cod`, `cfgcon_Cod`

#### CT_Alertas_Tipos, CT_Alertas_Canales, CT_Empresas
Tablas de referencia para tipos, canales (WhatsApp/Email/SMS) y empresas con conexiones Bejerman

#### CT_Alertas_Webhooks, CT_Alertas_Queries, CT_Alertas_Plantillas
Webhooks, queries dinámicos y plantillas por tipo de alerta

#### CT_Scheduler_Alertas
Registro de ejecuciones del scheduler:
```sql
CREATE TABLE CT_Scheduler_Alertas (
    sch_id INT IDENTITY PRIMARY KEY,
    sch_Cod VARCHAR(6),
    schcfg_Cod VARCHAR(6),
    sch_Fecha DATE,
    sch_FechaIntento DATETIME,
    sch_Estado VARCHAR(20),
    sch_CantMensajes INT,
    sch_DetalleError VARCHAR(MAX),
    sch_PayloadJson VARCHAR(MAX),
    sch_Activo BIT DEFAULT 1
);
```

#### CT_Alertas_Mensajes
Tracking de mensajes individuales enviados:
```sql
CREATE TABLE CT_Alertas_Mensajes (
    msg_id INT IDENTITY PRIMARY KEY,
    msg_Cod VARCHAR(6),
    msg_Wamid VARCHAR(100),
    msgcfg_Cod VARCHAR(6),
    msgbej_Tel VARCHAR(50),
    msg_Estado VARCHAR(20),
    msg_FechaEnvio DATETIME,
    msg_FechaRespuesta DATETIME
);
```

#### CT_Alertas_Admin_Emails
Destinatarios de notificaciones de errores:
```sql
CREATE TABLE CT_Alertas_Admin_Emails (
    adm_id INT IDENTITY PRIMARY KEY,
    adm_Email VARCHAR(100),
    adm_Nombre VARCHAR(50),
    adm_Activo BIT DEFAULT 1
);
```

### Tablas Bejerman (por empresa)
- `TgeCTPersonas` - Personas/contactos
- `TgeCTContactos` - Medios de contacto (email, teléfono)
- `TgeCTRel_Persona_Perfil` - Relación personas-perfiles
- `TgeCTPerfiles` - Perfiles para alertas grupales

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

### Producción
```bash
python main.py
```

### Pruebas (sin esperar al minuto)
```bash
python test_ciclo.py
```

## 📊 Flujo de Ejecución

1. **Sincronización**: Se alinea al próximo minuto exacto (segundo 00)
2. **Consulta BD**: Query con JOINs a todas las tablas relacionadas
3. **Fase 1 - Filtrado por día**:
   - ✅ Verifica frecuencia/fechas puntuales
   - 🔁 Descarta ya enviadas hoy (anti-duplicados)
4. **Fase 2 - Filtrado por hora**:
   - ⏱️ Ventana de ±2 minutos
   - 📅 Para PERIODICO: compara `cfg_HoraEnvio`
   - 📅 Para PUNTUAL: compara `cfg_FechasPuntuales`
5. **Fase 3 - Procesamiento y envío**:
   - 🔌 Conecta a Bejerman de la empresa
   - 👥 Obtiene destinatarios (INDIVIDUAL o PERFIL)
   - � Ejecuta query dinámico si corresponde
   - 📝 Procesa plantilla con datos del query
   - 📤 Envía webhook por cada destinatario
   - 💾 Registra en `CT_Scheduler_Alertas` y `CT_Alertas_Mensajes`
6. **Notificación de errores**: Si hay errores → Email HTML a administradores

## 📋 Logging

```
⏰ [12:49:00] Consultando alertas...
📋 Ejecutando query de consulta de alertas...
📊 Encontradas 4 alertas activas
📊 4 alertas en total | 2 pendientes para hoy

� 2 alertas para enviar ahora:
======================================================================
• 000001 (EMAIL) - Hora: 12:49:00
  → Juan Pérez (juan.perez@email.com)
• 000002 (WHATSAPP) - Hora: 12:49:00
  → Juan Pérez (5491112345678)

======================================================================
🚀 Enviando alertas...

✅ 000001 → Juan Pérez
✅ 000002 → Juan Pérez

� Total enviadas: 2 | Errores: 0
⏳ Esperando hasta el próximo minuto... (55.3s)
```

## 🔧 Arquitectura

### Módulos

- **main.py**: Scheduler principal con polling y filtros
- **database_config.py**: Configuración y conexiones SQL Server (Constec + Bejerman)
- **bejerman_queries.py**: Queries a bases Bejerman, destinatarios, plantillas
- **webhook_sender.py**: Envío de webhooks HTTP
- **email_notifier.py**: Notificaciones de errores por email
- **test_ciclo.py**: Script de prueba sin esperar al minuto

### Características de diseño

- **Stateless**: Sin caché ni estado entre iteraciones
- **Multi-tenant**: Conexión dinámica a base Bejerman por empresa
- **Filtros en Python**: Lógica flexible sin impacto en BD
- **Connection strings normalizados**: `TrustServerCertificate=True→yes`, `User Id→UID`
- **Manejo de errores tipificado**: Sin interrumpir procesamiento
- **Notificaciones HTML**: Emails visuales con detalles de errores

## 📝 Notas Importantes

### Formato de Horas
- `cfg_HoraEnvio` usa formato TIME de 24 horas
- `00:49:00` = 12:49 AM (medianoche)
- `12:49:00` = 12:49 PM (mediodía)

### Códigos de Canal
- `0001` = WhatsApp → `Tcon_Celular`
- `0002` = Email → `Tcon_Email`
- `0003` = SMS → `Tcon_Celular`

### Connection Strings Bejerman
Almacenados en Base64 en `CT_Empresas.emp_Conexion`:
```
Server=servidor;Database=bd;User Id=user;Password=pass;TrustServerCertificate=True
```