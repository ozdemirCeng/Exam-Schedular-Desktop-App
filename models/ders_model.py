"""
Ders Model - CRUD Operations
"""

import logging
from typing import List, Dict, Optional
from models.database import DatabaseManager

logger = logging.getLogger(__name__)


class DersModel:
    """Course data access layer"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_dersler_by_bolum(self, bolum_id: int) -> List[Dict]:
        """Get all courses for a department"""
        query = """
            SELECT ders_id, bolum_id, ders_kodu, ders_adi, ogretim_elemani, sinif, ders_yapisi, aktif
            FROM dersler
            WHERE bolum_id = %s AND aktif = TRUE
            ORDER BY sinif, ders_kodu
        """
        return self.db.execute_query(query, (bolum_id,))
    
    def get_ders_by_id(self, ders_id: int) -> Optional[Dict]:
        """Get course by ID"""
        query = """
            SELECT d.*, b.bolum_adi
            FROM dersler d
            JOIN bolumler b ON d.bolum_id = b.bolum_id
            WHERE d.ders_id = %s
        """
        result = self.db.execute_query(query, (ders_id,))
        return result[0] if result else None
    
    def get_ders_by_kod(self, bolum_id: int, ders_kodu: str) -> Optional[Dict]:
        """Get course by code"""
        query = """
            SELECT * FROM dersler
            WHERE bolum_id = %s AND ders_kodu = %s AND aktif = TRUE
        """
        result = self.db.execute_query(query, (bolum_id, ders_kodu))
        return result[0] if result else None
    
    def insert_ders(self, ders_data: Dict) -> int:
        """Insert new course"""
        query = """
            INSERT INTO dersler
            (bolum_id, ders_kodu, ders_adi, ogretim_elemani, sinif, ders_yapisi)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING ders_id
        """
        params = (
            ders_data['bolum_id'],
            ders_data['ders_kodu'],
            ders_data['ders_adi'],
            ders_data.get('ogretim_elemani', ''),
            ders_data.get('sinif', 1),
            ders_data.get('ders_yapisi', 'Zorunlu')
        )
        
        result = self.db.execute_query(query, params)
        logger.info(f"✅ Course created: {ders_data['ders_kodu']}")
        return result[0]['ders_id']
    
    def update_ders(self, ders_id: int, ders_data: Dict) -> bool:
        """Update course - ders_kodu is NOT updatable (read-only)"""
        query = """
            UPDATE dersler
            SET ders_adi = %s,
                ogretim_elemani = %s,
                sinif = %s,
                ders_yapisi = %s
            WHERE ders_id = %s
        """
        params = (
            ders_data['ders_adi'],
            ders_data.get('ogretim_elemani', ''),
            ders_data.get('sinif', 1),
            ders_data.get('ders_yapisi', 'Zorunlu'),
            ders_id
        )
        
        self.db.execute_query(query, params, fetch=False)
        logger.info(f"✅ Course updated: {ders_id}")
        return True
    
    def delete_ders(self, ders_id: int) -> bool:
        """Delete course (hard delete)"""
        # First delete course registrations
        query1 = "DELETE FROM ders_kayitlari WHERE ders_id = %s"
        self.db.execute_query(query1, (ders_id,), fetch=False)
        
        # Then delete course
        query2 = "DELETE FROM dersler WHERE ders_id = %s"
        self.db.execute_query(query2, (ders_id,), fetch=False)
        logger.info(f"Course deleted: {ders_id}")
        return True
