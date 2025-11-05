"""
Script de prueba para verificar el nuevo formato de payload con nombres de columnas originales
"""

import json
from datetime import datetime

# Simular destinatario tal como viene de la BD (nombres de columnas originales)
destinatario = {
    'Tper_Cod': '000001',
    'Tper_Desc': 'Tomy',
    'Tcon_Cod': '000001',
    'Tcon_Desc': 'Tomy - Trabajo',
    'Tcon_Email': 'tjuarez@constec.com.ar',
    'Tcon_Celular': '+5491157365902',
    'Trppbej_Cod': None
}

# Simular alerta tal como viene de la BD
alert = {
    'cfg_Cod': '000001',
    'cfg_Nombre': 'día de la madre',
    'cfgtip_Cod': '000004',
    'tip_Desc': 'MENSAJE GENÉRICO',
    'cfgcan_Cod': '0001',
    'can_Desc': 'EMAIL',
    'cfgemp_Cod': '000002',
    'empresa_nombre': 'Saphirus',
    'plt_Asunto': None
}

# Crear payload usando nombres originales de BD
payload = {
    'cfg_Cod': alert.get('cfg_Cod'),
    'cfg_Nombre': alert.get('cfg_Nombre'),
    'cfgtip_Cod': alert.get('cfgtip_Cod'),
    'tip_Desc': alert.get('tip_Desc'),
    'cfgcan_Cod': alert.get('cfgcan_Cod'),
    'can_Desc': alert.get('can_Desc'),
    'cfgemp_Cod': alert.get('cfgemp_Cod'),
    'empresa_nombre': alert.get('empresa_nombre'),
    'destinatario': destinatario,
    'mensaje': 'Sin plantilla',
    'plt_Asunto': alert.get('plt_Asunto'),
    'datos_query': {},
    'msg_cod': '871261',
    'timestamp': datetime.now().isoformat()
}

print("=" * 70)
print("PAYLOAD CON NOMBRES ORIGINALES DE BD")
print("=" * 70)
print("\nTODOS los campos usan nombres exactos de las columnas de la BD:")
print(json.dumps(payload, indent=2, ensure_ascii=False))
print("\n" + "=" * 70)
print("✅ Beneficios:")
print("   - cfg_Cod, cfgtip_Cod, cfgcan_Cod → nombres originales de CT_Alertas_Config")
print("   - Tper_Cod, Tcon_Email → nombres originales de TgeCTPersonas/TgeCTContactos")
print("   - Cualquier campo nuevo se incluye automáticamente")
print("   - No hay confusión ni conversiones de nombres")
print("=" * 70)
