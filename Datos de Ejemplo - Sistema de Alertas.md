# Datos de Ejemplo - Sistema de Alertas

# 📊 Datos de Ejemplo - Sistema de Alertas

> Esta página contiene valores de ejemplo para todas las tablas del sistema, cubriendo todos los casos posibles de configuración.
> 

---

## 🏢 Base de Datos Constec (Central)

### 1️⃣ CT_Empresas

| emp_id | emp_Cod | emp_Desc | emp_Conexion | emp_Activo | emp_FechaAlta |
| --- | --- | --- | --- | --- | --- |
| 1 | 000001 | Saphirus | U2VydmVyPTE5Mi4xNjguMS41MDtEYXRhYmFzZT1TQkRBUzs= | 1 | 2025-01-15 10:30:00 |
| 2 | 000002 | Lismar | U2VydmVyPTE5Mi4xNjguMS41MTtEYXRhYmFzZT1MSVNBUTA= | 1 | 2025-02-10 14:20:00 |
| 3 | 000003 | Fusion Pampa | U2VydmVyPTE5Mi4xNjguMS41MjtEYXRhYmFzZT1GVVNJT04= | 1 | 2025-03-05 09:15:00 |
| 4 | 000004 | Horsa | U2VydmVyPTE5Mi4xNjguMS41MztEYXRhYmFzZT1IT1JTQQ== | 0 | 2024-12-01 11:00:00 |

---

### 2️⃣ CT_Alertas_Canales

| can_id | can_Cod | can_Desc | can_Activo |
| --- | --- | --- | --- |
| 1 | 0001 | WhatsApp | 1 |
| 2 | 0002 | Email | 1 |
| 3 | 0003 | SMS | 1 |
| 4 | 0004 | Telegram | 0 |

---

### 3️⃣ CT_Alertas_Webhooks

| wbh_id | wbh_Cod | wbh_Desc | wbh_Url | wbh_Activo | wbh_FechaAlta |
| --- | --- | --- | --- | --- | --- |
| 1 | 000001 | Webhook Cuenta Corriente | [https://n8n.constec.com.ar/webhook/alerta-cc](https://n8n.constec.com.ar/webhook/alerta-cc) | 1 | 2025-01-20 08:00:00 |
| 2 | 000002 | Webhook Comprobantes | [https://n8n.constec.com.ar/webhook/alerta-comp](https://n8n.constec.com.ar/webhook/alerta-comp) | 1 | 2025-01-20 08:05:00 |
| 3 | 000003 | Webhook Pedidos | [https://n8n.constec.com.ar/webhook/alerta-pedidos](https://n8n.constec.com.ar/webhook/alerta-pedidos) | 1 | 2025-02-15 10:30:00 |
| 4 | 000004 | Webhook Genérico (deprecado) | [https://old.constec.com.ar/webhook/generic](https://old.constec.com.ar/webhook/generic) | 0 | 2024-11-10 12:00:00 |

---

### 4️⃣ CT_Alertas_Tipos

| tip_id | tip_Cod | tip_Desc | tipwbh_Cod | tip_RequiereBejCod | tip_Activo | tip_FechaAlta |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 000001 | Cuenta corriente - Saldo deudor | 000001 | 1 | 1 | 2025-01-20 08:10:00 |
| 2 | 000002 | Mensaje genérico | NULL | 0 | 1 | 2025-01-20 08:15:00 |
| 3 | 000003 | Recordatorio de pago | 000001 | 1 | 1 | 2025-02-05 09:00:00 |
| 4 | 000004 | Comprobante emitido | 000002 | 1 | 1 | 2025-02-10 11:30:00 |
| 5 | 000005 | Pedido pendiente de entrega | 000003 | 1 | 1 | 2025-03-01 10:00:00 |
| 6 | 000006 | Resumen mensual de ventas | 000001 | 0 | 1 | 2025-03-15 14:00:00 |

---

### 5️⃣ CT_Alertas_Config

**NOTA:** Esta tabla tiene `cfgcan_Cod` (un solo canal por configuración).

| cfg_Cod | cfg_Nombre | cfgtip_Cod | cfgemp_Cod | cfgper_Cod | cfgprf_Cod | cfgcan_Cod | cfgcon_Cod | cfg_TipoDisparo | cfg_Frecuencia | cfg_HoraEnvio | cfg_DiasSemana | cfg_DiasMes | cfg_FechasPuntuales | cfg_Activo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 000001 | CC deudor Juan - WhatsApp | 000001 | 000001 | 000001 | NULL | 0001 | 000001 | PERIODICO | DIARIO | 09:00:00 | NULL | NULL | NULL | 1 |
| 000002 | CC deudor Juan - Email | 000001 | 000001 | 000001 | NULL | 0002 | 000002 | PERIODICO | DIARIO | 09:00:00 | NULL | NULL | NULL | 1 |
| 000003 | Aviso general clientes | 000002 | 000001 | NULL | 0001 | 0001 | NULL | PERIODICO | SEMANAL | 10:00:00 | 1,3,5 | NULL | NULL | 1 |
| 000004 | Recordatorio Lismar | 000003 | 000002 | 000005 | NULL | 0001 | 000010 | PERIODICO | MENSUAL | 08:30:00 | NULL | 1,15 | NULL | 1 |
| 000005 | Comprobante puntual - WA | 000004 | 000001 | 000002 | NULL | 0001 | 000003 | PUNTUAL | NULL | NULL | NULL | NULL | 2025-11-15 14:00,2025-12-01 09:00 | 1 |
| 000006 | Comprobante puntual - SMS | 000004 | 000001 | 000002 | NULL | 0003 | 000003 | PUNTUAL | NULL | NULL | NULL | NULL | 2025-11-15 14:00,2025-12-01 09:00 | 1 |
| 000007 | Resumen mensual vendedores | 000006 | 000003 | NULL | 0003 | 0002 | NULL | PERIODICO | MENSUAL | 08:00:00 | NULL | 1 | NULL | 1 |
| 000008 | CC anual Fusion | 000001 | 000003 | 000008 | NULL | 0001 | NULL | PERIODICO | ANUAL | 00:01:00 | NULL | 1 | NULL | 1 |
| 000009 | Pedidos proveedores Semanal | 000005 | 000001 | NULL | 0002 | 0001 | NULL | PERIODICO | SEMANAL | 15:00:00 | 2,4 | NULL | NULL | 1 |
| 000010 | Config inactiva test | 000002 | 000001 | 000001 | NULL | 0001 | 000001 | PERIODICO | DIARIO | 12:00:00 | NULL | NULL | NULL | 0 |

**Casos cubiertos:**

- ✅ Modo INDIVIDUAL (cfgper_Cod con valor, cfgprf_Cod NULL)
- ✅ Modo PERFIL (cfgprf_Cod con valor, cfgper_Cod NULL)
- ✅ PERIODICO - DIARIO
- ✅ PERIODICO - SEMANAL (con días específicos)
- ✅ PERIODICO - MENSUAL (con días del mes)
- ✅ PERIODICO - ANUAL
- ✅ PUNTUAL (con fechas puntuales)
- ✅ Múltiples canales (mismo config duplicado por canal)
- ✅ Configuraciones activas e inactivas

---

### 6️⃣ CT_Alertas_Mensajes

| msg_Cod | msg_Wamid | msgcfg_Cod | msgbej_Tel | msg_FechaEnvio | msg_FechaRespuesta | msg_ButtonPayload | msg_ButtonText | msg_Estado |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 000001 | wamid.HBgNNTQ5MTE1NzQwNDQxMhUCABIYFjNFQj | 000001 | +5491127849391 | 2025-10-29 09:00:15 | 2025-10-29 09:05:23 | OK | Entendido | ENVIADO |
| 000002 | wamid.HBgNNTQ5MTE1NzQwNDQxMhUCABIYFjNFQj | 000001 | +5491127849391 | 2025-10-30 09:00:08 | NULL | NULL | NULL | ENVIADO |
| 000003 | wamid.XYZ789ABC456DEF | 000003 | +5491157123456 | 2025-10-28 10:00:12 | NULL | NULL | NULL | ENVIADO |
| 000004 | wamid.QWE456RTY789UIO | 000004 | +5491157404412 | 2025-10-15 08:30:05 | NULL | NULL | NULL | ENVIADO |
| 000005 | wamid.ZXC123VBN456MLK | 000005 | +5491157123456 | 2025-10-20 14:00:00 | NULL | NULL | NULL | PENDIENTE |
| 000006 | wamid.ERROR789 | 000001 | +5491199999999 | 2025-10-28 09:00:00 | NULL | NULL | NULL | ERROR |

**Estados posibles:** PENDIENTE, ENVIADO, ERROR

---

### 7️⃣ CT_Scheduler_Alertas

| sch_Cod | schcfg_Cod | sch_FechaIntento | sch_Fecha | sch_Estado | sch_CantMensajes | sch_DetalleError | sch_Activo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 000001 | 000001 | 2025-10-29 09:00:05 | 2025-10-29 | OK | 1 | NULL | 1 |
| 000002 | 000002 | 2025-10-29 09:00:07 | 2025-10-29 | OK | 1 | NULL | 1 |
| 000003 | 000003 | 2025-10-28 10:00:02 | 2025-10-28 | OK | 5 | NULL | 1 |
| 000004 | 000004 | 2025-10-15 08:30:01 | 2025-10-15 | OK | 1 | NULL | 1 |
| 000005 | 000001 | 2025-10-28 09:00:00 | 2025-10-28 | ERROR | 0 | Connection timeout to webhook | 1 |
| 000006 | 000007 | 2025-10-01 08:00:03 | 2025-10-01 | OK | 3 | NULL | 1 |

**Estados posibles:** OK, ERROR, PENDIENTE

---

### 8️⃣ CT_Alertas_Admin_Emails

| adm_id | adm_Email | adm_Nombre | adm_Activo | adm_FechaAlta |
| --- | --- | --- | --- | --- |
| 1 | [tjuarez@constec.com.ar](mailto:tjuarez@constec.com.ar) | Tomás Juárez | 1 | 2025-01-15 10:00:00 |
| 2 | [fdallago@constec.com.ar](mailto:fdallago@constec.com.ar) | Fabián Dal Lago | 1 | 2025-01-15 10:05:00 |
| 3 | [alertas@constec.com.ar](mailto:alertas@constec.com.ar) | Alertas Sistema | 1 | 2025-01-15 10:10:00 |
| 4 | [old-admin@constec.com.ar](mailto:old-admin@constec.com.ar) | Admin Viejo | 0 | 2024-06-01 08:00:00 |

---

### 9️⃣ CT_Alertas_Queries

| qry_Cod | qrytip_Cod | qryprf_Cod | qry_SQL | qry_RequiereBejCod | qry_Activo |
| --- | --- | --- | --- | --- | --- |
| 000001 | 000001 | 0001 | SELECT cli_Cod, cli_RazSoc, SUM(saldo) FROM Sta_CtaCte_Vtas WHERE cli_Cod = ? GROUP BY cli_Cod, cli_RazSoc | 1 | 1 |
| 000002 | 000003 | 0001 | SELECT TOP 5 fac_Nro, fac_Fecha, fac_Total FROM facturas WHERE cli_Cod = ? AND fac_Pagado = 0 ORDER BY fac_Fecha DESC | 1 | 1 |
| 000003 | 000005 | 0002 | SELECT ped_Nro, ped_Fecha, ped_Estado FROM pedidos WHERE pro_Cod = ? AND ped_Estado = 'PENDIENTE' | 1 | 1 |
| 000004 | 000006 | 0003 | SELECT ven_Cod, ven_Nombre, SUM(vta_Total) AS total_mes FROM ventas WHERE MONTH(vta_Fecha) = MONTH(GETDATE()) GROUP BY ven_Cod, ven_Nombre | 0 | 1 |

---

### 🔟 CT_Alertas_Plantillas

| plt_Cod | plttip_Cod | pltprf_Cod | pltcan_Cod | plt_Asunto | plt_Mensaje | plt_Activo |
| --- | --- | --- | --- | --- | --- | --- |
| 000001 | 000001 | 0001 | 0001 | NULL | 🔔 Hola nombre! Tu saldo deudor es de $saldo. Por favor regularizá tu situación. | 1 |
| 000002 | 000001 | 0001 | 0002 | Aviso de saldo deudor | Estimado nombre, le informamos que su saldo deudor es de $saldo. Por favor regularice su situación a la brevedad. | 1 |
| 000003 | 000003 | 0001 | 0001 | NULL | 📌 Recordatorio: Tenés facturas pendientes de pago. Total: $total. | 1 |
| 000004 | 000004 | 0001 | 0001 | NULL | ✅ Se emitió el comprobante tipo numero por $importe. Gracias por tu compra! | 1 |
| 000005 | 000005 | 0002 | 0001 | NULL | 📦 Hola! Tenés pedidos pendientes de entrega. Revisá el detalle y coordiná la entrega. | 1 |
| 000006 | 000006 | 0003 | 0002 | Resumen mensual de ventas | Hola nombre, este mes vendiste $total. Felicitaciones por tu desempeño! | 1 |

---

## 🗄️ Base de Datos Bejerman (por cada cliente)

### 1️⃣ TgeCTPerfiles

| Tprf_id | Tprf_Cod | Tprf_Desc | Tprf_Activo | Tprf_FechaAlta |
| --- | --- | --- | --- | --- |
| 1 | 0001 | Cliente | 1 | 2025-01-20 10:00:00 |
| 2 | 0002 | Proveedor | 1 | 2025-01-20 10:01:00 |
| 3 | 0003 | Vendedor | 1 | 2025-01-20 10:02:00 |
| 4 | 0004 | Otro | 1 | 2025-01-20 10:03:00 |

---

### 2️⃣ TgeCTPersonas

| Tper_id | Tper_Cod | Tper_Desc | Tper_Activo | Tper_FechaAlta |
| --- | --- | --- | --- | --- |
| 1 | 000001 | Juan Pérez S.A. | 1 | 2025-01-25 11:00:00 |
| 2 | 000002 | María González | 1 | 2025-01-26 09:30:00 |
| 3 | 000003 | Contacto Genérico XYZ | 1 | 2025-02-01 14:00:00 |
| 4 | 000004 | Roberto Martínez | 1 | 2025-02-05 10:15:00 |
| 5 | 000005 | Laura Fernández | 1 | 2025-02-10 16:20:00 |
| 6 | 000006 | Carlos Rodríguez (inactivo) | 0 | 2024-12-01 08:00:00 |
| 7 | 000007 | Ana López | 1 | 2025-03-01 11:45:00 |
| 8 | 000008 | Diego Sánchez | 1 | 2025-03-10 13:30:00 |

---

### 3️⃣ TgeCTRel_Persona_Perfil

| Trpp_id | Trpp_Cod | Trppper_Cod | Trppprf_Cod | Trppbej_Cod | Trpp_Activo | Descripción |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 000001 | 000001 | 0001 | 000011 | 1 | Juan como Cliente |
| 2 | 000002 | 000001 | 0003 | 000045 | 1 | Juan como Vendedor |
| 3 | 000003 | 000002 | 0001 | 000035 | 1 | María como Cliente |
| 4 | 000004 | 000003 | 0004 | NULL | 1 | Contacto Genérico (sin Bejerman) |
| 5 | 000005 | 000004 | 0002 | 000078 | 1 | Roberto como Proveedor |
| 6 | 000006 | 000005 | 0001 | 000092 | 1 | Laura como Cliente |
| 7 | 000007 | 000007 | 0003 | 000015 | 1 | Ana como Vendedor |
| 8 | 000008 | 000008 | 0001 | 000123 | 1 | Diego como Cliente |
| 9 | 000009 | 000002 | 0002 | 000056 | 1 | María como Proveedor |

**Nota:** Una persona puede tener múltiples perfiles (como Juan que es Cliente y Vendedor).

---

### 4️⃣ TgeCTContactos

| Tcon_id | Tcon_Cod | Tconper_Cod | Tcon_Desc | Tcon_Celular | Tcon_Email | Tcon_EsPrincipal | Tcon_Activo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 000001 | 000001 | Juan - Celular | +5491127849391 | [juan@example.com](mailto:juan@example.com) | 1 | 1 |
| 2 | 000002 | 000001 | Secretaria de Juan | +5491127849392 | [secretaria@example.com](mailto:secretaria@example.com) | 0 | 1 |
| 3 | 000003 | 000001 | Juan - WhatsApp Trabajo | +5491157123456 | NULL | 0 | 1 |
| 4 | 000004 | 000002 | María - Principal | +5491187654321 | [maria@example.com](mailto:maria@example.com) | 1 | 1 |
| 5 | 000005 | 000003 | Contacto XYZ - Tel1 | +5491127849393 | NULL | 1 | 1 |
| 6 | 000006 | 000004 | Roberto - Celular | +5491198765432 | [roberto@proveedor.com](mailto:roberto@proveedor.com) | 1 | 1 |
| 7 | 000007 | 000004 | Roberto - Oficina | NULL | [oficina@proveedor.com](mailto:oficina@proveedor.com) | 0 | 1 |
| 8 | 000008 | 000005 | Laura - WhatsApp | +5491157404412 | NULL | 1 | 1 |
| 9 | 000009 | 000005 | Laura - Email corporativo | NULL | [laura.f@empresa.com.ar](mailto:laura.f@empresa.com.ar) | 0 | 1 |
| 10 | 000010 | 000005 | Asistente de Laura | +5491123456789 | [asistente@empresa.com.ar](mailto:asistente@empresa.com.ar) | 0 | 1 |
| 11 | 000011 | 000007 | Ana - Principal | +5491134567890 | [ana.vendedor@constec.com.ar](mailto:ana.vendedor@constec.com.ar) | 1 | 1 |
| 12 | 000012 | 000008 | Diego - Celular | +5491145678901 | [diego@cliente.com](mailto:diego@cliente.com) | 1 | 1 |
| 13 | 000013 | 000001 | Juan - Viejo (inactivo) | +5491199999999 | [old@example.com](mailto:old@example.com) | 0 | 0 |

**Nota:** Una persona puede tener múltiples contactos (WhatsApp, email, etc.).

---

## 🔍 Resumen de Casos Cubiertos

### ✅ Tipos de Disparo

- **PERIODICO** con frecuencia DIARIO
- **PERIODICO** con frecuencia SEMANAL (días específicos)
- **PERIODICO** con frecuencia MENSUAL (días del mes)
- **PERIODICO** con frecuencia ANUAL
- **PUNTUAL** con fechas específicas

### ✅ Modos de Envío

- **Modo INDIVIDUAL:** Persona específica con contacto seleccionado
- **Modo PERFIL:** Todas las personas de uno o más perfiles

### ✅ Canales

- WhatsApp (0001)
- Email (0002)
- SMS (0003)
- Telegram (0004) - inactivo

### ✅ Estados

- Configuraciones activas e inactivas
- Mensajes: PENDIENTE, ENVIADO, ERROR
- Scheduler: OK, ERROR, PENDIENTE

### ✅ Relaciones

- Personas con múltiples perfiles (ej: Juan es Cliente y Vendedor)
- Personas con múltiples contactos
- Configuraciones duplicadas por canal (mismo horario, distinto canal)
- Webhooks asociados a tipos de alerta

---

**Fecha de creación:** 30/10/2025

**Propósito:** Documentación de referencia para desarrollo y testing del scheduler