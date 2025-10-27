"""
Script de diagnóstico para identificar el problema con CT_Alertas_Mensajes
"""

import traceback
from database_config import DatabaseConfig

def diagnosticar_tabla():
    """Diagnostica problemas con la tabla CT_Alertas_Mensajes."""
    print("🔍 DIAGNÓSTICO DE TABLA CT_Alertas_Mensajes")
    print("=" * 50)
    
    try:
        db_config = DatabaseConfig()
        conn = db_config.connect()
        cursor = conn.cursor()
        
        # 1. Verificar si la tabla existe
        print("1️⃣ Verificando si la tabla existe...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'CT_Alertas_Mensajes'
        """)
        tabla_existe = cursor.fetchone()[0] > 0
        
        if tabla_existe:
            print("✅ Tabla CT_Alertas_Mensajes existe")
            
            # 2. Verificar estructura de la tabla
            print("\n2️⃣ Verificando estructura de la tabla...")
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'CT_Alertas_Mensajes'
                ORDER BY ORDINAL_POSITION
            """)
            
            columnas = cursor.fetchall()
            for columna in columnas:
                nombre, tipo, nullable, longitud = columna
                longitud_str = f"({longitud})" if longitud else ""
                nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                print(f"   📋 {nombre}: {tipo}{longitud_str} {nullable_str}")
            
            # 3. Probar INSERT de prueba
            print("\n3️⃣ Probando INSERT de prueba...")
            try:
                cursor.execute("""
                    INSERT INTO CT_Alertas_Mensajes 
                    (msg_Cod, msgcfg_Cod, msg_Estado, msg_FechaEnvio)
                    VALUES (?, ?, 'TEST', GETDATE())
                """, 'TEST01', 'CFG001')
                
                print("✅ INSERT exitoso")
                
                # 4. Verificar que se insertó
                cursor.execute("SELECT TOP 1 * FROM CT_Alertas_Mensajes WHERE msg_Cod = 'TEST01'")
                resultado = cursor.fetchone()
                if resultado:
                    print("✅ Registro encontrado después del INSERT")
                
                # 5. Probar UPDATE
                print("\n4️⃣ Probando UPDATE de prueba...")
                cursor.execute("""
                    UPDATE CT_Alertas_Mensajes 
                    SET msg_Estado = 'ENVIADO', msg_FechaRespuesta = GETDATE()
                    WHERE msg_Cod = 'TEST01'
                """)
                print("✅ UPDATE exitoso")
                
                # 6. Limpiar registro de prueba
                cursor.execute("DELETE FROM CT_Alertas_Mensajes WHERE msg_Cod = 'TEST01'")
                conn.commit()
                print("✅ Registro de prueba eliminado")
                
            except Exception as e:
                print(f"❌ Error en operaciones DML: {e}")
                print(f"📋 Stack trace: {traceback.format_exc()}")
                conn.rollback()
            
        else:
            print("❌ Tabla CT_Alertas_Mensajes NO existe")
            print("\n📋 Script para crear la tabla:")
            print("""
CREATE TABLE CT_Alertas_Mensajes (
    msg_id INT IDENTITY(1,1) PRIMARY KEY,
    msg_Cod VARCHAR(6) NOT NULL,
    msg_Wamid VARCHAR(255) NULL,
    msgcfg_Cod VARCHAR(6) NOT NULL,
    msgbej_Tel VARCHAR(50) NULL,
    msg_FechaEnvio DATETIME DEFAULT GETDATE(),
    msg_FechaRespuesta DATETIME NULL,
    msg_ButtonPayload VARCHAR(100) NULL,
    msg_ButtonText VARCHAR(100) NULL,
    msg_Estado VARCHAR(20) NOT NULL
);
            """)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print(f"📋 Stack trace: {traceback.format_exc()}")

def diagnosticar_permisos():
    """Diagnostica permisos del usuario en la BD."""
    print("\n🔐 DIAGNÓSTICO DE PERMISOS")
    print("=" * 30)
    
    try:
        db_config = DatabaseConfig()
        conn = db_config.connect()
        cursor = conn.cursor()
        
        # Verificar usuario actual
        cursor.execute("SELECT SYSTEM_USER, USER_NAME(), IS_SRVROLEMEMBER('sysadmin')")
        resultado = cursor.fetchone()
        usuario_sistema, usuario_bd, es_admin = resultado
        
        print(f"👤 Usuario sistema: {usuario_sistema}")
        print(f"👤 Usuario BD: {usuario_bd}")
        print(f"🛡️ Es admin: {'Sí' if es_admin == 1 else 'No'}")
        
        # Verificar permisos específicos en la tabla
        try:
            cursor.execute("""
                SELECT 
                    p.permission_name,
                    p.state_desc
                FROM sys.database_permissions p
                JOIN sys.objects o ON p.major_id = o.object_id
                JOIN sys.database_principals pr ON p.grantee_principal_id = pr.principal_id
                WHERE o.name = 'CT_Alertas_Mensajes'
                AND pr.name = USER_NAME()
            """)
            
            permisos = cursor.fetchall()
            if permisos:
                print("\n🔑 Permisos en CT_Alertas_Mensajes:")
                for permiso, estado in permisos:
                    print(f"   {estado}: {permiso}")
            else:
                print("\n⚠️ No se encontraron permisos específicos (puede usar permisos heredados)")
        
        except Exception as e:
            print(f"⚠️ No se pudieron verificar permisos específicos: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error al verificar permisos: {e}")

if __name__ == "__main__":
    diagnosticar_tabla()
    diagnosticar_permisos()
    
    print("\n" + "=" * 50)
    print("🎯 RESUMEN:")
    print("Si ves errores arriba, esa es la causa del DB_INSERT")
    print("Los errores más comunes son:")
    print("  - Tabla no existe")
    print("  - Columnas con nombres diferentes") 
    print("  - Restricciones de longitud (VARCHAR muy corto)")
    print("  - Permisos insuficientes")
    print("  - Constraints o índices únicos")