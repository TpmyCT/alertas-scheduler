"""
Prueba simple de importaciones y sintaxis.
"""

import sys
import traceback

def test_imports():
    """Prueba todas las importaciones necesarias."""
    print("🧪 PROBANDO IMPORTACIONES...")
    print("=" * 40)
    
    modules_to_test = [
        'database_config',
        'webhook_sender', 
        'email_notifier',
        'scheduler'
    ]
    
    success_count = 0
    
    for module_name in modules_to_test:
        try:
            module = __import__(module_name)
            print(f"✅ {module_name} - OK")
            success_count += 1
        except Exception as e:
            print(f"❌ {module_name} - ERROR: {e}")
            traceback.print_exc()
    
    print("=" * 40)
    print(f"📊 RESULTADO: {success_count}/{len(modules_to_test)} módulos OK")
    
    if success_count == len(modules_to_test):
        print("🎉 Todas las importaciones funcionan correctamente!")
        return True
    else:
        print("⚠️ Hay problemas con algunas importaciones")
        return False

def test_basic_functionality():
    """Prueba funcionalidad básica sin BD."""
    print("\n🧪 PROBANDO FUNCIONALIDAD BÁSICA...")
    print("=" * 40)
    
    try:
        from main import AlertScheduler
        scheduler = AlertScheduler()
        
        # Probar generación de código único
        msg_cod = scheduler.generar_msg_cod()
        print(f"✅ Generación msg_cod: {msg_cod}")
        
        # Probar cálculo de tiempo
        segundos = scheduler.calcular_segundos_hasta_proximo_minuto()
        print(f"✅ Cálculo tiempo próximo minuto: {segundos:.1f}s")
        
        print("🎉 Funcionalidad básica OK!")
        return True
        
    except Exception as e:
        print(f"❌ Error en funcionalidad básica: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DEL SCHEDULER")
    print("=" * 50)
    
    # Prueba 1: Importaciones
    imports_ok = test_imports()
    
    # Prueba 2: Funcionalidad básica
    if imports_ok:
        functionality_ok = test_basic_functionality()
    else:
        functionality_ok = False
    
    print("\n" + "=" * 50)
    if imports_ok and functionality_ok:
        print("🎉 TODAS LAS PRUEBAS PASARON")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")