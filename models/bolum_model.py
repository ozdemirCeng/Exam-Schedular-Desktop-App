"""
Bolum Model - CRUD Operations
"""

import logging
from typing import List, Dict, Optional
from models.database import DatabaseManager

logger = logging.getLogger(__name__)


class BolumModel:
    """Department data access layer"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_all(self) -> List[Dict]:
        """Get all departments"""
        query = """
            SELECT bolum_id, bolum_kodu, bolum_adi, aktif
            FROM bolumler
            WHERE aktif = TRUE
            ORDER BY bolum_adi
        """
        return self.db.execute_query(query)
    
    def get_all_bolumler(self) -> List[Dict]:
        """Get all departments (alias for compatibility)"""
        return self.get_all()
    
    def get_bolum_by_id(self, bolum_id: int) -> Optional[Dict]:
        """Get department by ID"""
        query = """
            SELECT * FROM bolumler
            WHERE bolum_id = %s AND aktif = TRUE
        """
        result = self.db.execute_query(query, (bolum_id,))
        return result[0] if result else None
    
    def get_bolum_by_kod(self, bolum_kodu: str) -> Optional[Dict]:
        """Get department by code"""
        query = """
            SELECT * FROM bolumler
            WHERE bolum_kodu = %s AND aktif = TRUE
        """
        result = self.db.execute_query(query, (bolum_kodu,))
        return result[0] if result else None
    
    def insert_bolum(self, bolum_data: Dict) -> int:
        """Insert new department"""
        query = """
            INSERT INTO bolumler (bolum_kodu, bolum_adi)
            VALUES (%s, %s)
            RETURNING bolum_id
        """
        params = (
            bolum_data['bolum_kodu'],
            bolum_data['bolum_adi']
        )
        
        result = self.db.execute_query(query, params)
        logger.info(f"Department created: {bolum_data['bolum_adi']}")
        return result[0]['bolum_id']
    
    def update_bolum(self, bolum_id: int, bolum_data: Dict) -> bool:
        """Update department"""
        query = """
            UPDATE bolumler
            SET bolum_kodu = %s,
                bolum_adi = %s
            WHERE bolum_id = %s
        """
        params = (
            bolum_data['bolum_kodu'],
            bolum_data['bolum_adi'],
            bolum_id
        )
        
        self.db.execute_query(query, params, fetch=False)
        logger.info(f"Department updated: {bolum_id}")
        return True
    
    def delete_bolum(self, bolum_id: int) -> bool:
        """Delete department (soft delete)"""
        query = "UPDATE bolumler SET aktif = FALSE WHERE bolum_id = %s"
        self.db.execute_query(query, (bolum_id,), fetch=False)
        logger.info(f"Department deleted: {bolum_id}")
        return True


