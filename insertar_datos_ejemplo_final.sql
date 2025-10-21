-- Script para insertar datos de ejemplo en el sistema de alertas (estructura real)
USE CTAutomatizaciones;
GO

PRINT 'Insertando datos de ejemplo con estructura correcta...';

-- 1. Insertar Tipos de Alerta
INSERT INTO CT_Alertas_Tipos (codigo, descripcion) VALUES
('BACKUP', 'Reportes de que los backups se hicieron bien'),
('CUENTAS', 'Notificación de cuentas a cobrar/pagar de tus empresas');

-- 2. Insertar Canales
INSERT INTO CT_Alertas_Canales (codigo, descripcion) VALUES
('EMAIL', 'Canal de notificaciones por correo electrónico'),
('WHATSAPP', 'Canal de notificaciones por WhatsApp Business');

-- 3. Insertar Clientes
INSERT INTO CT_Alertas_Clientes (descripcion, connection_string) VALUES
('Constec', 'U2VydmVyPWNvbnN0ZWMubm8taXAuaW5mbztEYXRhYmFzZT1DVEF1dG9tYXRpemFjaW9uZXM7VXNlciBJZD1jb25zdGVjO1Bhc3N3b3JkPUNvbnN0ZWMuMjUwNDtQb3J0PTY0MDUy'),
('Saphirus', 'U2VydmVyPXNhcGhpcnVzLmRkbnMubmV0O0RhdGFiYXNlPW1hc3RlcjtVc2VyIElkPWJlamVybWFuO1Bhc3N3b3JkPXRpTUNMbXUyN3F0UXdEO1BvcnQ9MTE0NTU=');

-- 4. Insertar Destinatarios
INSERT INTO CT_Alertas_Destinatarios (cliente_id, nombre, email, tel) VALUES
(1, 'Tomy', 'tjuarez@constec.com.ar', '5491126933483');

-- 5. Insertar Configuraciones de Alerta
INSERT INTO CT_Alertas_Configuracion (tipo_alerta_id, destinatario_id, canal_id, tipo_disparo, frecuencia, hora_envio, dias_semana, dias_mes, webhook_id) VALUES
-- Alerta de backup de lunes a viernes a las 9:00 AM
(1, 1, 1, 'PERIODICO', 'SEMANAL', '09:00:00', '1,2,3,4,5', NULL, NULL),

-- Alerta mensual de cuentas el primer día del mes a las 8:00 AM por WhatsApp
(2, 1, 2, 'PERIODICO', 'MENSUAL', '08:00:00', NULL, '1', NULL);

PRINT 'Datos de ejemplo insertados correctamente!';
PRINT '✅ 2 tipos de alerta (BACKUP, CUENTAS)';
PRINT '✅ 2 canales (EMAIL, WHATSAPP)';
PRINT '✅ 2 clientes (Constec, Saphirus)';
PRINT '✅ 1 destinatario (Tomy)';
PRINT '✅ 2 configuraciones de alerta';

-- Mostrar resumen de alertas configuradas
SELECT 
    c.id,
    t.codigo as tipo_alerta,
    t.descripcion as desc_tipo,
    d.nombre as destinatario,
    can.codigo as canal,
    c.frecuencia,
    c.hora_envio,
    c.dias_semana,
    c.dias_mes,
    CASE WHEN c.activo = 1 THEN 'Activa' ELSE 'Inactiva' END as estado
FROM CT_Alertas_Configuracion c
INNER JOIN CT_Alertas_Tipos t ON c.tipo_alerta_id = t.id
INNER JOIN CT_Alertas_Destinatarios d ON c.destinatario_id = d.id
INNER JOIN CT_Alertas_Canales can ON c.canal_id = can.id
ORDER BY c.id;

GO