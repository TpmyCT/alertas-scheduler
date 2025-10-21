# Estructura Real de las Tablas del Sistema de Alertas

## CT_Alertas_Canales
- id (int, PK)
- codigo (nvarchar(100), NOT NULL)
- descripcion (nvarchar(400), NOT NULL)
- activo (bit, NOT NULL, DEFAULT 1)

## CT_Alertas_Clientes
- id (int, PK)
- descripcion (nvarchar(200), NOT NULL)
- activo (bit, NOT NULL, DEFAULT 1)
- fecha_creacion (datetime, NOT NULL, DEFAULT getdate())
- connection_string (nvarchar(2000), NOT NULL)

## CT_Alertas_Config_Empresas
- id (int, PK)
- config_id (int, NOT NULL)
- nombre_empresa (nvarchar(200), NOT NULL)
- database_empresa (nvarchar(200), NOT NULL)
- tipo_cuenta (nvarchar(40), NOT NULL)
- query_plantilla_id (int, NOT NULL)
- activo (bit, NOT NULL, DEFAULT 1)
- fecha_creacion (datetime, NOT NULL, DEFAULT getdate())
- cliente_id (int, NULL)

## CT_Alertas_Configuracion
- id (int, PK)
- tipo_alerta_id (int, NOT NULL)
- destinatario_id (int, NOT NULL)
- canal_id (int, NOT NULL)
- tipo_disparo (nvarchar(100), NOT NULL)
- frecuencia (nvarchar(40), NOT NULL)
- hora_envio (time, NULL)
- dias_semana (nvarchar(40), NULL)
- dias_mes (nvarchar(40), NULL)
- webhook_id (int, NULL)
- activo (bit, NOT NULL, DEFAULT 1)
- fecha_creacion (datetime, NOT NULL, DEFAULT getdate())

## CT_Alertas_Contexto
- id (int, PK)
- mensaje_id (nvarchar(510), NOT NULL)
- tipo_alerta (nvarchar(100), NOT NULL)
- destinatario_tel (nvarchar(100), NOT NULL)
- fecha_envio (datetime, NOT NULL, DEFAULT getdate())
- procesado (bit, NOT NULL, DEFAULT 0)

## CT_Alertas_Destinatarios
- id (int, PK)
- cliente_id (int, NOT NULL)
- nombre (nvarchar(200), NOT NULL)
- email (nvarchar(400), NULL)
- tel (nvarchar(100), NULL)
- activo (bit, NOT NULL, DEFAULT 1)
- fecha_creacion (datetime, NOT NULL, DEFAULT getdate())

## CT_Alertas_Log
- id (int, PK)
- alerta_id (int, NOT NULL)
- fecha_ejecucion (datetime, NOT NULL, DEFAULT getdate())
- resultado (nvarchar(1000), NULL)

## CT_Alertas_Query_Plantillas
- id (int, PK)
- nombre (nvarchar(200), NOT NULL)
- tipo_cuenta (nvarchar(40), NOT NULL)
- query (nvarchar(MAX), NOT NULL)
- activo (bit, NOT NULL, DEFAULT 1)
- fecha_creacion (datetime, NOT NULL, DEFAULT getdate())

## CT_Alertas_Tipos
- id (int, PK)
- codigo (nvarchar(100), NOT NULL)
- descripcion (nvarchar(1000), NOT NULL)
- activo (bit, NOT NULL, DEFAULT 1)
- fecha_creacion (datetime, NOT NULL, DEFAULT getdate())

## CT_Alertas_Webhooks
- id (int, PK)
- codigo (nvarchar(100), NOT NULL)
- nombre (nvarchar(200), NOT NULL)
- descripcion (nvarchar(1000), NULL)
- url (nvarchar(400), NOT NULL)
- activo (bit, NOT NULL, DEFAULT 1)
- fecha_creacion (datetime, NOT NULL, DEFAULT getdate())