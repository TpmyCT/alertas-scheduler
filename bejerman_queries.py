"""
Módulo para consultar datos desde bases Bejerman de clientes.
Maneja queries dinámicos, obtención de personas, perfiles y contactos.
"""

import re


class BejermanQueries:
    """Maneja consultas a bases Bejerman de clientes."""
    
    def __init__(self, db_config):
        """
        Inicializa el módulo de queries Bejerman.
        
        Args:
            db_config (DatabaseConfig): Configuración de base de datos
        """
        self.db_config = db_config
    
    def obtener_destinatarios_individual(self, emp_conexion, cfgper_cod, cfgcon_cod, cfgcan_cod):
        """
        Obtiene destinatarios para modo INDIVIDUAL.
        - Si cfgcon_cod está especificado: devuelve solo ese contacto
        - Si cfgcon_cod es NULL: devuelve TODOS los contactos activos de la persona
        
        Args:
            emp_conexion (str): String de conexión a Bejerman (Base64)
            cfgper_cod (str): Código de persona
            cfgcon_cod (str): Código de contacto específico (o NULL para todos)
            cfgcan_cod (str): Código de canal (0001=WhatsApp, 0002=Email, 0003=SMS)
            
        Returns:
            list: Lista de diccionarios con destinatarios
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            conn = self.db_config.connect_bejerman(emp_conexion)
            cursor = conn.cursor()
            
            if cfgcon_cod:
                # Contacto específico
                query = """
                SELECT 
                    p.Tper_Cod, p.Tper_Desc,
                    c.Tcon_Cod, c.Tcon_Desc, 
                    c.Tcon_Email, c.Tcon_Celular,
                    rpp.Trppbej_Cod,
                    prf.Tprf_Cod, prf.Tprf_Desc
                FROM CTPersonas p
                INNER JOIN CTContactos c ON c.Tconper_Cod = p.Tper_Cod
                LEFT JOIN CTRel_Persona_Perfil rpp ON rpp.Trppper_Cod = p.Tper_Cod
                LEFT JOIN CTPerfiles prf ON prf.Tprf_Cod = rpp.Trppprf_Cod
                WHERE p.Tper_Cod = ? AND c.Tcon_Cod = ? 
                    AND p.Tper_Activo = 1 AND c.Tcon_Activo = 1
                """
                cursor.execute(query, cfgper_cod, cfgcon_cod)
            else:
                # TODOS los contactos activos de la persona
                query = """
                SELECT 
                    p.Tper_Cod, p.Tper_Desc,
                    c.Tcon_Cod, c.Tcon_Desc, 
                    c.Tcon_Email, c.Tcon_Celular,
                    rpp.Trppbej_Cod,
                    prf.Tprf_Cod, prf.Tprf_Desc
                FROM CTPersonas p
                INNER JOIN CTContactos c ON c.Tconper_Cod = p.Tper_Cod
                LEFT JOIN CTRel_Persona_Perfil rpp ON rpp.Trppper_Cod = p.Tper_Cod
                LEFT JOIN CTPerfiles prf ON prf.Tprf_Cod = rpp.Trppprf_Cod
                WHERE p.Tper_Cod = ?
                    AND p.Tper_Activo = 1 AND c.Tcon_Activo = 1
                """
                cursor.execute(query, cfgper_cod)
            
            # Obtener nombres de columnas directamente de la BD
            columnas = [desc[0] for desc in cursor.description]
            
            # Construir lista de diccionarios automáticamente
            destinatarios = []
            for row in cursor.fetchall():
                destinatarios.append(dict(zip(columnas, row)))
            
            cursor.close()
            conn.close()
            return destinatarios
            
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            return []
    
    def obtener_destinatarios_perfil(self, emp_conexion, cfgprf_cod, cfgcan_cod):
        """
        Obtiene todos los destinatarios para modo PERFIL.
        Devuelve TODOS los contactos activos de cada persona en el perfil.
        
        Args:
            emp_conexion (str): String de conexión a Bejerman (Base64)
            cfgprf_cod (str): Código de perfil
            cfgcan_cod (str): Código de canal (0001=WhatsApp, 0002=Email, 0003=SMS)
            
        Returns:
            list: Lista de diccionarios con destinatarios
        """
        try:
            conn = self.db_config.connect_bejerman(emp_conexion)
            cursor = conn.cursor()
            
            # Obtener TODOS los contactos activos de las personas en el perfil
            query = """
            SELECT DISTINCT
                p.Tper_Cod, p.Tper_Desc,
                c.Tcon_Cod, c.Tcon_Desc, 
                c.Tcon_Email, c.Tcon_Celular,
                rpp.Trppbej_Cod,
                prf.Tprf_Cod, prf.Tprf_Desc
            FROM CTRel_Persona_Perfil rpp
            INNER JOIN CTPersonas p ON p.Tper_Cod = rpp.Trppper_Cod
            INNER JOIN CTContactos c ON c.Tconper_Cod = p.Tper_Cod
            LEFT JOIN CTPerfiles prf ON prf.Tprf_Cod = rpp.Trppprf_Cod
            WHERE rpp.Trppprf_Cod = ? 
                AND p.Tper_Activo = 1 
                AND rpp.Trpp_Activo = 1
                AND c.Tcon_Activo = 1
            """
            
            cursor.execute(query, cfgprf_cod)
            
            # Obtener nombres de columnas directamente de la BD
            columnas = [desc[0] for desc in cursor.description]
            
            # Construir lista de diccionarios automáticamente
            destinatarios = []
            for row in cursor.fetchall():
                destinatarios.append(dict(zip(columnas, row)))
            
            cursor.close()
            conn.close()
            
            return destinatarios
            
        except Exception as e:
            raise Exception(f"Error al obtener destinatarios por perfil: {e}")
    
    def ejecutar_query_dinamico(self, emp_conexion, query_sql, bej_cod=None):
        """
        Ejecuta un query SQL dinámico en la base Bejerman.
        
        Args:
            emp_conexion (str): String de conexión a Bejerman (Base64)
            query_sql (str): Query SQL a ejecutar (puede contener ? para parámetro bej_cod)
            bej_cod (str): Código Bejerman del cliente (opcional)
            
        Returns:
            list: Lista de diccionarios con resultados del query
        """
        try:
            conn = self.db_config.connect_bejerman(emp_conexion)
            cursor = conn.cursor()
            
            # Ejecutar query con o sin parámetro
            if bej_cod and '?' in query_sql:
                cursor.execute(query_sql, bej_cod)
            else:
                cursor.execute(query_sql)
            
            # Obtener nombres de columnas
            columnas = [description[0] for description in cursor.description]
            
            # Convertir resultados a lista de diccionarios
            resultados = []
            for fila in cursor.fetchall():
                resultado = dict(zip(columnas, fila))
                resultados.append(resultado)
            
            cursor.close()
            conn.close()
            
            return resultados
            
        except Exception as e:
            raise Exception(f"Error al ejecutar query dinámico: {e}")
    
    def procesar_plantilla(self, plantilla_mensaje, datos_query):
        """
        Reemplaza placeholders en una plantilla con datos del query.
        
        Args:
            plantilla_mensaje (str): Mensaje con placeholders como $nombre, $saldo, etc.
            datos_query (dict): Diccionario con datos del query ejecutado
            
        Returns:
            str: Mensaje procesado con placeholders reemplazados
        """
        if not plantilla_mensaje or not datos_query:
            return plantilla_mensaje
        
        mensaje_procesado = plantilla_mensaje
        
        # Reemplazar cada placeholder $columna con su valor
        for columna, valor in datos_query.items():
            placeholder = f'${columna}'
            # Convertir valor a string, manejar None
            valor_str = str(valor) if valor is not None else ''
            mensaje_procesado = mensaje_procesado.replace(placeholder, valor_str)
        
        return mensaje_procesado
