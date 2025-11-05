# Reglas de Desarrollo - Sistema de Alertas

## ⚠️ REGLAS CRÍTICAS - SIEMPRE RESPETAR

### 1. Nombres de campos en queries
**NUNCA hardcodear nombres de campos en el SELECT**

❌ **INCORRECTO:**
```sql
SELECT emp.emp_Cod, emp.emp_Desc AS empresa_nombre, emp.emp_Conexion
```

✅ **CORRECTO:**
```sql
SELECT emp.*
```

**Razón:** Los nombres de los campos deben extraerse dinámicamente de la base de datos usando `cursor.description`, tal como se hace en todo el proyecto. Esto garantiza que los nombres coincidan exactamente con la estructura de la tabla.

### 2. Extracción dinámica de columnas
Siempre usar este patrón:
```python
cursor.execute(query)
columnas = [desc[0] for desc in cursor.description]
resultados = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
```

### 3. Consistencia en payloads
Los datos en el webhook deben organizarse por tabla de origen, con los nombres exactos de los campos de la base de datos, sin alias ni modificaciones.

---

## Aplicar estos cambios

El `alert_fetcher.py` debe traer TODOS los campos de cada tabla usando `tabla.*` y dejar que `cursor.description` extraiga los nombres reales.
