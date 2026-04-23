import oracledb
import os
import logging

logger = logging.getLogger(__name__)

# Configuración vía variables de entorno
ORACLE_USER = os.getenv("ORACLE_USER")
ORACLE_PASS = os.getenv("ORACLE_PASS")
ORACLE_DSN = os.getenv("ORACLE_DSN")
ORACLE_CLIENT_PATH = os.getenv("ORACLE_CLIENT_PATH")

def get_oracle_connection(thick_mode=False):
    """
    Retorna una conexión a la base de datos Oracle.
    Por defecto intenta modo Thin. Si thick_mode es True, intenta inicializar el Instant Client.
    """
    try:
        if thick_mode:
            try:
                # Inicializar modo thick si no se ha hecho
                oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_PATH)
                logger.info(f"Modo Thick inicializado con {ORACLE_CLIENT_PATH}")
            except oracledb.ProgrammingError as e:
                # Ya inicializado o error de configuración
                logger.warning(f"Aviso al inicializar Thick mode: {e}")
        
        conn = oracledb.connect(
            user=ORACLE_USER,
            password=ORACLE_PASS,
            dsn=ORACLE_DSN
        )
        logger.info(f"Conexión exitosa a Oracle: {ORACLE_DSN}")
        return conn
    except Exception as e:
        logger.error(f"Error conectando a Oracle: {e}")
        raise

def execute_query(query, params=None, fetch_all=True):
    """Ejecuta una consulta y retorna los resultados."""
    conn = get_oracle_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch_all:
            # Obtener nombres de columnas
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
        return None
    finally:
        conn.close()
