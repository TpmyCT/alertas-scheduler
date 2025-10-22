"""
Módulo de configuración y conexión a la base de datos.
Maneja las credenciales, validación de variables de entorno y conexión a SQL Server.
"""

import os
import pyodbc
from dotenv import load_dotenv


class DatabaseConfig:
    """Maneja la configuración y conexión a la base de datos."""
    
    def __init__(self):
        """Inicializa la configuración cargando variables de entorno."""
        load_dotenv()
        self._validate_environment_variables()
        self._connection = None
    
    def _validate_environment_variables(self):
        """Valida que todas las variables de entorno requeridas estén presentes."""
        self.db_driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
        self.db_server = os.getenv('DB_SERVER')
        self.db_database = os.getenv('DB_DATABASE')
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        
        required_vars = ['DB_SERVER', 'DB_DATABASE', 'DB_USER', 'DB_PASSWORD']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print("❌ ERROR: Faltan variables de entorno en el archivo .env:")
            for var in missing_vars:
                print(f"   - {var}")
            print("\n💡 Crea un archivo .env con las credenciales de la base de datos")
            raise ValueError(f"Variables de entorno faltantes: {missing_vars}")
    
    def get_connection_string(self):
        """Construye la cadena de conexión a la base de datos."""
        return (
            f'DRIVER={{{self.db_driver}}};'
            f'SERVER={self.db_server};'
            f'DATABASE={self.db_database};'
            f'UID={self.db_user};'
            f'PWD={self.db_password}'
        )
    
    def connect(self):
        """Establece conexión con la base de datos."""
        try:
            connection_string = self.get_connection_string()
            self._connection = pyodbc.connect(connection_string)
            return self._connection
        except Exception as e:
            print(f"❌ Error al conectar con la base de datos: {e}")
            raise
    
    def get_connection(self):
        """Obtiene la conexión activa o crea una nueva si no existe."""
        if self._connection is None:
            self.connect()
        return self._connection
    
    def close_connection(self):
        """Cierra la conexión a la base de datos."""
        if self._connection:
            self._connection.close()
            self._connection = None