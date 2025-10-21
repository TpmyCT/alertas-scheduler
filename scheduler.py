import pyodbc
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Variables de configuración de base de datos desde .env
DB_DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
DB_SERVER = os.getenv('DB_SERVER')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Validar que las variables críticas estén definidas
required_vars = ['DB_SERVER', 'DB_DATABASE', 'DB_USER', 'DB_PASSWORD']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print("❌ ERROR: Faltan variables de entorno en el archivo .env:")
    for var in missing_vars:
        print(f"   - {var}")
    print("\n💡 Crea un archivo .env con las credenciales de la base de datos")
    exit(1)

connection_string = (
    f'DRIVER={{{DB_DRIVER}}};'
    f'SERVER={DB_SERVER};'
    f'DATABASE={DB_DATABASE};'
    f'UID={DB_USER};'
    f'PWD={DB_PASSWORD}'
)
conn = pyodbc.connect(connection_string)

scheduler = BackgroundScheduler()
scheduler.start()

ultima_revision = datetime.now()

os.system('cls' if os.name == 'nt' else 'clear')

def ejecutar_alerta(alerta):
    hora_actual = datetime.now().strftime('%H:%M:%S')
    print(f"\n🔔 [{hora_actual}] EJECUTANDO ALERTA #{alerta['id']}")
    
    if not alerta['webhook_id']:
        estado = "ERROR: No hay webhook configurado"
        print(f"   ❌ {estado}")
    else:
        try:
            url = f"https://api.constec.ar/webhook/{alerta['webhook_id']}"
            print(f"   📡 Enviando webhook a: {url}")
            response = requests.post(url, json={"alerta_id": alerta['id']})
            estado = f"OK - Código de respuesta: {response.status_code}"
            print(f"   ✅ Webhook enviado exitosamente (Código: {response.status_code})")
        except Exception as e:
            estado = f"ERROR: {e}"
            print(f"   ❌ Error al enviar webhook: {e}")
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ct_alertas_log (alerta_id, fecha_ejecucion, resultado)
                VALUES (?, GETDATE(), ?)
            """, (alerta['id'], estado))
            conn.commit()
            print(f"   📝 Resultado guardado en el log")
    except Exception as e:
        print(f"   ⚠️  Error al guardar en base de datos: {e}")
    
    print("   ✅ Alerta completada\n")

def programar_alerta(alerta):
    # Validar que los datos necesarios no sean None o vacíos
    if not alerta["hora_envio"] or alerta["hora_envio"] == "None":
        print(f"   ❌ NO SE PUEDE PROGRAMAR - Falta la hora de envío")
        return False
    
    if not alerta["frecuencia"] or alerta["frecuencia"] == "None":
        print(f"   ❌ NO SE PUEDE PROGRAMAR - Falta la frecuencia (diario/semanal/mensual)")
        return False
    
    # Validar campos específicos según frecuencia
    if alerta["frecuencia"] == "SEMANAL" and (not alerta["dias_semana"] or alerta["dias_semana"] == "None"):
        print(f"   ❌ NO SE PUEDE PROGRAMAR - Falta definir los días de la semana")
        return False
    
    if alerta["frecuencia"] in ["MENSUAL", "ANUAL"] and (not alerta["dias_mes"] or alerta["dias_mes"] == "None"):
        print(f"   ❌ NO SE PUEDE PROGRAMAR - Falta definir los días del mes")
        return False
    
    try:
        hora, minuto, *_ = map(int, alerta["hora_envio"].split(":"))
    except (ValueError, AttributeError) as e:
        print(f"   ❌ NO SE PUEDE PROGRAMAR - Formato de hora inválido: '{alerta['hora_envio']}'")
        return False
    
    # Mapeo de días para mostrar nombres más claros
    # Tu BD usa 1-7, APScheduler usa 0-6, así que convertimos
    dias_semana = {
        '1': 'Lunes', '2': 'Martes', '3': 'Miércoles', 
        '4': 'Jueves', '5': 'Viernes', '6': 'Sábado', '7': 'Domingo'
    }
    
    if alerta["frecuencia"] == "SEMANAL":
        try:
            dias = alerta["dias_semana"].split(",")
            dias_nombres = []
            for d in dias:
                d = d.strip()  # Limpiar espacios
                if d:  # Solo agregar si el día no está vacío
                    # Convertir de formato BD (1-7) a formato APScheduler (0-6)
                    dia_scheduler = str(int(d) - 1) if d != '7' else '6'  # 7 (Domingo) -> 6
                    if d == '7':  # Domingo especial
                        dia_scheduler = '6'
                    else:
                        dia_scheduler = str(int(d) - 1)
                    
                    scheduler.add_job(
                        ejecutar_alerta,
                        trigger="cron",
                        day_of_week=dia_scheduler,
                        hour=hora,
                        minute=minuto,
                        args=[alerta],
                        id=f"alerta_{alerta['id']}_{d}",
                        replace_existing=True
                    )
                    dias_nombres.append(dias_semana.get(d, f'Día {d}'))
            
            print(f"   ✅ PROGRAMADA - Cada {', '.join(dias_nombres)} a las {hora:02d}:{minuto:02d}")
        except Exception as e:
            print(f"   ❌ ERROR al programar: {e}")
            return False
    
    elif alerta["frecuencia"] == "DIARIO":
        try:
            scheduler.add_job(
                ejecutar_alerta,
                trigger="cron",
                hour=hora,
                minute=minuto,
                args=[alerta],
                id=f"alerta_{alerta['id']}_diario",
                replace_existing=True
            )
            print(f"   ✅ PROGRAMADA - Todos los días a las {hora:02d}:{minuto:02d}")
        except Exception as e:
            print(f"   ❌ ERROR al programar: {e}")
            return False
    
    elif alerta["frecuencia"] == "MENSUAL":
        try:
            # Para alertas mensuales, usar los dias_mes especificados
            dias = alerta["dias_mes"].split(",")
            dias_nombres = []
            for d in dias:
                d = d.strip()
                if d and d.isdigit() and 1 <= int(d) <= 31:
                    scheduler.add_job(
                        ejecutar_alerta,
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
        except Exception as e:
            print(f"   ❌ ERROR al programar: {e}")
            return False
    
    elif alerta["frecuencia"] == "ANUAL":
        try:
            # Para alertas anuales, ejecutar en enero en los días especificados
            dias = alerta["dias_mes"].split(",")
            dias_nombres = []
            for d in dias:
                d = d.strip()
                if d and d.isdigit() and 1 <= int(d) <= 31:
                    scheduler.add_job(
                        ejecutar_alerta,
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
        except Exception as e:
            print(f"   ❌ ERROR al programar: {e}")
            return False
    
    else:
        print(f"   ❌ FRECUENCIA NO SOPORTADA: '{alerta['frecuencia']}'")
        return False
    
    return True

def cargar_alertas(es_recarga=False):
    if es_recarga:
        # Limpiar la consola cuando es una recarga
        os.system('cls' if os.name == 'nt' else 'clear')
        print("🔄 RECARGANDO CONFIGURACIÓN...")
        print()
    
    print("=" * 60)
    print("📋 CARGANDO ALERTAS DESDE LA BASE DE DATOS")
    print("=" * 60)
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, tipo_alerta_id, destinatario_id, canal_id, tipo_disparo, 
                   frecuencia, hora_envio, dias_semana, dias_mes, webhook_id
            FROM ct_alertas_configuracion
            WHERE activo = 1
        """)
        alertas_cargadas = 0
        alertas_programadas = 0
        alertas_omitidas = 0
        
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
            
            print(f"\n🔍 Revisando Alerta #{alerta['id']}:")
            print(f"   📅 Frecuencia: {alerta['frecuencia'] or 'NO DEFINIDA'}")
            print(f"   ⏰ Hora: {alerta['hora_envio'] or 'NO DEFINIDA'}")
            if alerta['frecuencia'] == 'SEMANAL':
                print(f"   📆 Días: {alerta['dias_semana'] or 'NO DEFINIDOS'}")
            elif alerta['frecuencia'] == 'MENSUAL':
                print(f"   📆 Días del mes: {alerta['dias_mes'] or 'NO DEFINIDOS'}")
            elif alerta['frecuencia'] == 'ANUAL':
                print(f"   📆 Días del mes: {alerta['dias_mes'] or 'NO DEFINIDOS'}")
            
            resultado = programar_alerta(alerta)
            if resultado:
                alertas_programadas += 1
            else:
                alertas_omitidas += 1
            alertas_cargadas += 1
        
        print("\n" + "=" * 60)
        print(f"📊 RESUMEN:")
        print(f"   ✅ Alertas programadas: {alertas_programadas}")
        print(f"   ⚠️  Alertas omitidas: {alertas_omitidas}")
        print(f"   📝 Total procesadas: {alertas_cargadas}")
        print("=" * 60)

def verificar_cambios():
    global ultima_revision
    try:
        with conn.cursor() as cur:
            # Verificar solo por fecha_creacion ya que fecha_modificacion no existe
            cur.execute("""
                SELECT COUNT(*) FROM ct_alertas_configuracion
                WHERE fecha_creacion > ?
            """, (ultima_revision,))
            count = cur.fetchone()[0]
        if count > 0:
            print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] ¡NUEVAS ALERTAS DETECTADAS!")
            print(f"    Se encontraron {count} alertas nuevas en la base de datos")
            print("    Recargando configuración...")
            scheduler.remove_all_jobs()
            cargar_alertas(es_recarga=True)
            ultima_revision = datetime.now()
            
            print("\n🔄 MODO MONITOREO REACTIVADO")
            print("   El sistema sigue revisando nuevas alertas cada minuto...")
            print("   Presiona Ctrl+C para detener\n")
    except Exception as e:
        print(f"⚠️  Error al verificar cambios: {e}")
        # Continuar funcionando sin verificación de cambios

print("🚀 INICIANDO SCHEDULER DE ALERTAS")
print("💫 Conectado a la base de datos")
print("⚡ Programador automático activado")

# Cargar alertas iniciales
cargar_alertas()

print("\n🔄 MODO MONITOREO ACTIVADO")
print("   El sistema revisa nuevas alertas cada minuto...")
print("   Presiona Ctrl+C para detener\n")

# Bucle de revisión cada minuto
try:
    while True:
        verificar_cambios()
        time.sleep(60)
except KeyboardInterrupt:
    print("\n\n🛑 SCHEDULER DETENIDO")
    print("   ¡Hasta luego!")
    scheduler.shutdown()
