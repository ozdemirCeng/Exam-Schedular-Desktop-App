"""
Veritabanı Bağlantı Yöneticisi
Thread-safe PostgreSQL connection pooling
"""

import os
import logging
from contextlib import contextmanager
import threading
from typing import Optional, Dict, Any, List
import psycopg2
from psycopg2 import pool, extras
from psycopg2.pool import PoolError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Thread-safe veritabanı bağlantı havuzu yöneticisi"""
    _instance = None
    _pool = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._pool is None:
            self._initialize_pool()

    def _initialize_pool(self):
        """Connection pool'u başlat"""
        try:
            db_config = {
                'minconn': int(os.getenv('DB_POOL_SIZE', 5)),
                'maxconn': int(os.getenv('DB_MAX_OVERFLOW', 20)),
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'database': os.getenv('DB_NAME', 'sinav_takvimi_db'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', ''),
                'cursor_factory': extras.RealDictCursor
            }
            
            logger.info(f"Initializing connection pool: {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
            
            self._pool = psycopg2.pool.ThreadedConnectionPool(**db_config)
            logger.info("✅ Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"❌ Database connection pool initialization failed: {str(e)}", exc_info=True)
            raise

    def _ensure_pool(self):
        """Ensure pool exists and is usable; reinitialize if needed."""
        if self._pool is None:
            with self._lock:
                if self._pool is None:
                    self._initialize_pool()
            return
        try:
            test_conn = self._pool.getconn()
            if test_conn:
                self._pool.putconn(test_conn)
        except PoolError:
            logger.warning("⚠️ Connection pool is closed; reinitializing...")
            with self._lock:
                self._initialize_pool()

    @contextmanager
    def get_connection(self):
        """Context manager ile güvenli bağlantı"""
        conn = None
        try:
            self._ensure_pool()
            try:
                conn = self._pool.getconn()
            except PoolError:
                logger.warning("⚠️ PoolError on getconn; reinitializing and retrying once...")
                self._ensure_pool()
                conn = self._pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Veritabanı işlem hatası: {e}")
            raise
        finally:
            if conn:
                self._pool.putconn(conn)

    @contextmanager
    def get_cursor(self, commit=True):
        """Context manager ile güvenli cursor"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Cursor hatası: {e}")
                raise
            finally:
                cursor.close()

    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Optional[List[Dict]]:
        """SQL sorgusu çalıştır"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            if fetch:
                return cursor.fetchall()
            return None

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Toplu INSERT/UPDATE"""
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount

    def set_user_context(self, user_id: int):
        """RLS (Row Level Security) için kullanıcı context'i ayarla"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT set_current_user_id(%s)", (user_id,))

    def call_function(self, func_name: str, *args) -> Any:
        """PostgreSQL fonksiyonu çağır"""
        placeholders = ','.join(['%s'] * len(args))
        query = f"SELECT {func_name}({placeholders}) as result"
        with self.get_cursor() as cursor:
            cursor.execute(query, args)
            result = cursor.fetchone()
            return result['result'] if result else None

    def test_connection(self) -> bool:
        """Bağlantı testi"""
        try:
            if not self._pool:
                logger.error("Connection pool not initialized")
                return False
                
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                success = result['test'] == 1
                if success:
                    logger.info("✅ Database connection test successful")
                return success
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {str(e)}", exc_info=True)
            return False

    def close_all_connections(self):
        """Tüm bağlantıları kapat"""
        if self._pool:
            self._pool.closeall()
            logger.info("Tüm veritabanı bağlantıları kapatıldı")
            self._pool = None


db = DatabaseManager()
