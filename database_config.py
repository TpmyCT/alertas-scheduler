"""
Módulo de configuración y conexión a la base de datos.
Maneja las credenciales y conexión a SQL Server de forma simple.
Soporta conexiones dinámicas a bases Bejerman de clientes.
"""

import os
import base64
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
        """Construye la cadena de conexión a la base de datos Constec (principal)."""
        return (
            f'DRIVER={{{self.db_driver}}};'
            f'SERVER={self.db_server};'
            f'DATABASE={self.db_database};'
            f'UID={self.db_user};'
            f'PWD={self.db_password}'
        )
    
    def connect(self):
        """
        Establece una nueva conexión con la base de datos Constec (principal).
        
        Returns:
            pyodbc.Connection: Nueva conexión a la base de datos
        """
        connection_string = self.get_connection_string()
        return pyodbc.connect(connection_string)
    
    def decode_connection_string(self, encoded_string):
        """
        Decodifica un string de conexión desde Base64.
        
        Args:
            encoded_string (str): String de conexión codificado en Base64
            
        Returns:
            str: String de conexión decodificado
        """
        try:
            decoded_bytes = base64.b64decode(encoded_string)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Error al decodificar string de conexión: {e}")
    
    def connect_bejerman(self, emp_conexion):
        """
        Establece una conexión con una base Bejerman de un cliente.
        
        Args:
            emp_conexion (str): String de conexión codificado en Base64 desde CT_Empresas
            
        Returns:
            pyodbc.Connection: Nueva conexión a la base Bejerman del cliente
        """
        decoded_conn = self.decode_connection_string(emp_conexion)
        
        # Normalizar TrustServerCertificate: pyodbc requiere 'yes'/'no' no 'True'/'False'
        if 'TrustServerCertificate=True' in decoded_conn:
            decoded_conn = decoded_conn.replace('TrustServerCertificate=True', 'TrustServerCertificate=yes')
        elif 'TrustServerCertificate=False' in decoded_conn:
            decoded_conn = decoded_conn.replace('TrustServerCertificate=False', 'TrustServerCertificate=no')
        
        # Normalizar credenciales: 'User Id=' y 'Password=' a 'UID=' y 'PWD='
        # pyodbc acepta ambos, pero es más confiable usar la forma corta
        if 'User Id=' in decoded_conn:
            decoded_conn = decoded_conn.replace('User Id=', 'UID=')
        if 'Password=' in decoded_conn:
            decoded_conn = decoded_conn.replace('Password=', 'PWD=')
        
        # Agregar driver si no está presente
        if 'DRIVER=' not in decoded_conn.upper():
            decoded_conn = f'DRIVER={{{self.db_driver}}};{decoded_conn}'
        
        return pyodbc.connect(decoded_conn)