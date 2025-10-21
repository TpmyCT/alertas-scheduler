# Resultado de las Tablas después de ejecutar insertar_datos_ejemplo_final.sql

## 📋 CT_Alertas_Tipos
| id | codigo  | descripcion                                        | activo | fecha_creacion |
|----|---------|---------------------------------------------------|--------|----------------|
| 1  | BACKUP  | Reportes de que los backups se hicieron bien     | 1      | 2025-10-21     |
| 2  | CUENTAS | Notificación de cuentas a cobrar/pagar de tus empresas | 1 | 2025-10-21     |

## 📧 CT_Alertas_Canales  
| id | codigo   | descripcion                                    | activo |
|----|----------|-----------------------------------------------|--------|
| 1  | EMAIL    | Canal de notificaciones por correo electrónico | 1      |
| 2  | WHATSAPP | Canal de notificaciones por WhatsApp Business  | 1      |

## 🏢 CT_Alertas_Clientes
| id | descripcion | connection_string (base64)                                                                                              | activo | fecha_creacion |
|----|-------------|--------------------------------------------------------------------------------------------------------------------------|--------|----------------|
| 1  | Constec     | U2VydmVyPWNvbnN0ZWMubm8taXAuaW5mbztEYXRhYmFzZT1DVEF1dG9tYXRpemFjaW9uZXM7VXNlciBJZD1jb25zdGVjO1Bhc3N3b3JkPUNvbnN0ZWMuMjUwNDtQb3J0PTY0MDUy | 1 | 2025-10-21 |
| 2  | Saphirus    | U2VydmVyPXNhcGhpcnVzLmRkbnMubmV0O0RhdGFiYXNlPW1hc3RlcjtVc2VyIElkPWJlamVybWFuO1Bhc3N3b3JkPXRpTUNMbXUyN3F0UXdEO1BvcnQ9MTE0NTU= | 1 | 2025-10-21 |

**Connection Strings decodificados:**
- **Constec**: `Server=constec.no-ip.info;Database=CTAutomatizaciones;User Id=constec;Password=Constec.2504;Port=64052`
- **Saphirus**: `Server=saphirus.ddns.net;Database=master;User Id=bejerman;Password=tiMCLmu27qtQwD;Port=11455`

## 👤 CT_Alertas_Destinatarios
| id | cliente_id | nombre | email                   | tel            | activo | fecha_creacion |
|----|------------|--------|-------------------------|----------------|--------|----------------|
| 1  | 1          | Tomy   | tjuarez@constec.com.ar  | 5491126933483  | 1      | 2025-10-21     |

## ⚙️ CT_Alertas_Configuracion (Tabla Principal)
| id | tipo_alerta_id | destinatario_id | canal_id | tipo_disparo | frecuencia | hora_envio | dias_semana | dias_mes | webhook_id | activo | fecha_creacion |
|----|----------------|-----------------|----------|--------------|------------|------------|-------------|----------|------------|--------|----------------|
| 1  | 1              | 1               | 1        | PERIODICO    | DIARIO     | 09:00:00   | NULL        | NULL     | NULL       | 1      | 2025-10-21     |
| 2  | 2              | 1               | 2        | PERIODICO    | SEMANAL    | 08:00:00   | 1           | NULL     | NULL       | 1      | 2025-10-21     |

---

## 🔗 Cómo se relacionan los datos:

### **Configuración 1 (Backup Diario)**
```
CT_Alertas_Configuracion (id=1)
├── tipo_alerta_id=1 → CT_Alertas_Tipos (BACKUP)
├── destinatario_id=1 → CT_Alertas_Destinatarios (Tomy)
│   └── cliente_id=1 → CT_Alertas_Clientes (Constec)
├── canal_id=1 → CT_Alertas_Canales (EMAIL)
└── Programación: DIARIO a las 09:00:00
```

**Resultado:** Tomy recibirá un email diario a las 9:00 AM con reportes de backup de Constec.

### **Configuración 2 (Cuentas Semanal)**
```
CT_Alertas_Configuracion (id=2)
├── tipo_alerta_id=2 → CT_Alertas_Tipos (CUENTAS)
├── destinatario_id=1 → CT_Alertas_Destinatarios (Tomy)
│   └── cliente_id=1 → CT_Alertas_Clientes (Constec)
├── canal_id=2 → CT_Alertas_Canales (WHATSAPP)
└── Programación: SEMANAL los LUNES (dias_semana=1) a las 08:00:00
```

**Resultado:** Tomy recibirá un WhatsApp cada lunes a las 8:00 AM con notificaciones de cuentas a cobrar/pagar de Constec.

---

## 📊 Query del resumen que muestra el script:
```sql
SELECT 
    c.id,                    -- 1, 2
    t.codigo as tipo_alerta, -- BACKUP, CUENTAS
    t.descripcion as desc_tipo,
    d.nombre as destinatario, -- Tomy, Tomy
    can.codigo as canal,     -- EMAIL, WHATSAPP
    c.frecuencia,           -- DIARIO, SEMANAL
    c.hora_envio,           -- 09:00:00, 08:00:00
    c.dias_semana,          -- NULL, 1
    c.dias_mes,             -- NULL, NULL
    CASE WHEN c.activo = 1 THEN 'Activa' ELSE 'Inactiva' END as estado
FROM CT_Alertas_Configuracion c
INNER JOIN CT_Alertas_Tipos t ON c.tipo_alerta_id = t.id
INNER JOIN CT_Alertas_Destinatarios d ON c.destinatario_id = d.id
INNER JOIN CT_Alertas_Canales can ON c.canal_id = can.id
ORDER BY c.id;
```

## 🎯 Resultado esperado del scheduler:
- **Todos los días a las 9:00 AM**: Email a Tomy sobre backups
- **Todos los lunes a las 8:00 AM**: WhatsApp a Tomy sobre cuentas

¿Te parece clara esta estructura?