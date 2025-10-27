"""
Módulo de configuración y conexión a la base de datos.
Maneja las credenciales y conexión a SQL Server de forma simple.
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
        """
        Establece una nueva conexión con la base de datos.
        
        Returns:
            pyodbc.Connection: Nueva conexión a la base de datos
        """
        connection_string = self.get_connection_string()
        return pyodbc.connect(connection_string)