# Scheduler de Alertas - Versión Refactorizada

## Descripción General

Este sistema de alertas automatizadas ha sido refactorizado para ser más mantenible, entendible y modular. El código original se ha separado en diferentes módulos especializados, cada uno con una responsabilidad específica.

## Arquitectura del Sistema

### Estructura de Archivos

```
scheduler/
├── scheduler.py              # Punto de entrada principal
├── database_config.py        # Configuración y conexión a BD
├── webhook_sender.py         # Envío de webhooks y logging
├── alert_scheduler.py        # Programación de alertas
├── alert_loader.py          # Carga y monitoreo de alertas
├── .env                     # Variables de entorno (no versionado)
└── README_refactorizado.md  # Esta documentación
```

### Módulos y Responsabilidades

#### 1. `database_config.py` - Configuración de Base de Datos
**Responsabilidad**: Maneja toda la configuración y conexión a la base de datos SQL Server.

**Funcionalidades**:
- Carga y valida variables de entorno desde `.env`
- Construye cadenas de conexión
- Establece y mantiene conexiones a la base de datos
- Manejo de errores de conexión

**Clase principal**: `DatabaseConfig`

#### 2. `webhook_sender.py` - Envío de Webhooks
**Responsabilidad**: Maneja el envío de notificaciones HTTP y el registro de resultados.

**Funcionalidades**:
- Envía webhooks a URLs configuradas
- Registra resultados de ejecución en la base de datos
- Manejo de errores HTTP y timeouts
- Logging detallado de cada ejecución

**Clase principal**: `WebhookSender`

#### 3. `alert_scheduler.py` - Programación de Alertas
**Responsabilidad**: Programa trabajos automáticos según diferentes frecuencias.

**Funcionalidades**:
- Valida configuraciones de alertas
- Programa trabajos con APScheduler para diferentes frecuencias:
  - Diario
  - Semanal (días específicos)
  - Mensual (días específicos del mes)
  - Anual (días específicos de enero)
- Conversión de formatos de días entre BD y APScheduler
- Manejo de errores de programación

**Clase principal**: `AlertScheduler`

#### 4. `alert_loader.py` - Carga de Alertas
**Responsabilidad**: Carga alertas desde la base de datos y monitorea cambios.

**Funcionalidades**:
- Obtiene alertas activas desde la base de datos
- Muestra información detallada de cada alerta
- Detecta nuevas alertas y recarga automáticamente
- Genera estadísticas de carga
- Interface de usuario en consola

**Clase principal**: `AlertLoader`

#### 5. `scheduler.py` - Punto de Entrada Principal
**Responsabilidad**: Orquesta todos los módulos y maneja el ciclo de vida del sistema.

**Funcionalidades**:
- Inicializa todos los componentes
- Coordina la carga inicial de alertas
- Ejecuta el ciclo de monitoreo continuo
- Maneja interrupciones y cierre limpio del sistema
- Interface principal de usuario

## Cómo Funciona el Sistema

### Flujo de Ejecución

1. **Inicialización**:
   - `scheduler.py` crea instancia de `DatabaseConfig`
   - Se establece conexión con la base de datos
   - Se inicializan `WebhookSender`, `AlertScheduler` y `AlertLoader`
   - Se inicia el scheduler de trabajos en segundo plano

2. **Carga Inicial**:
   - `AlertLoader` consulta todas las alertas activas en la BD
   - Para cada alerta, valida configuración y la programa con `AlertScheduler`
   - Se muestran estadísticas de carga (programadas/omitidas)

3. **Monitoreo Continuo**:
   - Cada minuto, `AlertLoader` verifica si hay nuevas alertas
   - Si detecta cambios, limpia trabajos existentes y recarga todo
   - El sistema continúa monitoreando hasta ser interrumpido

4. **Ejecución de Alertas**:
   - APScheduler ejecuta alertas según su programación
   - `WebhookSender` envía la notificación HTTP
   - Se registra el resultado en la tabla de logs

### Tipos de Frecuencia Soportados

- **DIARIO**: Se ejecuta todos los días a la hora especificada
- **SEMANAL**: Se ejecuta en días específicos de la semana (1=Lunes, 7=Domingo)
- **MENSUAL**: Se ejecuta en días específicos de cada mes (1-31)
- **ANUAL**: Se ejecuta en días específicos de enero cada año

## Configuración

### Variables de Entorno (.env)

```env
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_SERVER=tu-servidor.database.windows.net
DB_DATABASE=tu-base-de-datos
DB_USER=tu-usuario
DB_PASSWORD=tu-contraseña
```

### Dependencias Requeridas

```bash
pip install pyodbc requests apscheduler python-dotenv
```

## Uso del Sistema

### Iniciar el Sistema

```bash
python scheduler.py
```

### Detener el Sistema

Presiona `Ctrl+C` para detener el sistema de forma limpia.

## Ventajas de la Refactorización

### 1. **Separación de Responsabilidades**
- Cada módulo tiene una función específica y bien definida
- Facilita el mantenimiento y debugging
- Permite modificar un componente sin afectar otros

### 2. **Reutilización de Código**
- Los módulos pueden ser reutilizados en otros proyectos
- Cada clase es independiente y testeable

### 3. **Mantenibilidad**
- Código más organizado y fácil de entender
- Funciones más pequeñas y enfocadas
- Documentación clara de cada componente

### 4. **Escalabilidad**
- Fácil agregar nuevas funcionalidades
- Posibilidad de extender tipos de frecuencia
- Arquitectura preparada para crecimiento

### 5. **Testing**
- Cada módulo puede ser testeado independientemente
- Mocking más sencillo para pruebas unitarias
- Aislamiento de dependencias

## Migración desde la Versión Anterior

El sistema refactorizado mantiene **100% de compatibilidad** con:
- La misma base de datos
- Los mismos webhooks
- El mismo comportamiento de ejecución
- Las mismas variables de entorno

**No se requieren cambios en la configuración existente**.

## Próximos Pasos Sugeridos

1. **Tests Unitarios**: Crear tests para cada módulo
2. **Logging Avanzado**: Implementar logging con archivos y niveles
3. **Configuración Externa**: Mover configuraciones a archivo JSON/YAML
4. **API REST**: Crear endpoints para gestionar alertas sin tocar BD
5. **Dashboard**: Interface web para monitorear el sistema