"""
Oturma Model - CRUD Operations
"""

import logging
from typing import List, Dict, Optional
from models.database import DatabaseManager

logger = logging.getLogger(__name__)


class OturmaModel:
    """Seating plan data access layer"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_by_sinav(self, sinav_id: int) -> List[Dict]:
        """Get seating plan for an exam"""
        query = """
            SELECT op.oturma_id, op.sinav_id, op.ogrenci_no, op.derslik_id,
                   op.satir_no as satir, op.sutun_no as sutun,
                   o.ad_soyad,
                   d.derslik_kodu, d.derslik_adi
            FROM oturma_planlari op
            JOIN ogrenciler o ON op.ogrenci_no = o.ogrenci_no
            JOIN derslikler d ON op.derslik_id = d.derslik_id
            WHERE op.sinav_id = %s
            ORDER BY d.derslik_kodu, op.satir_no, op.sutun_no
        """
        return self.db.execute_query(query, (sinav_id,))
    
    def get_by_derslik(self, sinav_id: int, derslik_id: int) -> List[Dict]:
        """Get seating plan for a specific classroom in an exam"""
        query = """
            SELECT op.*, o.ad_soyad,
                   op.satir_no as satir, op.sutun_no as sutun
            FROM oturma_planlari op
            JOIN ogrenciler o ON op.ogrenci_no = o.ogrenci_no
            WHERE op.sinav_id = %s AND op.derslik_id = %s
            ORDER BY op.satir_no, op.sutun_no
        """
        return self.db.execute_query(query, (sinav_id, derslik_id))
    
    def insert_oturma(self, oturma_data: Dict) -> int:
        """Insert seating assignment"""
        query = """
            INSERT INTO oturma_planlari
            (sinav_id, ogrenci_no, derslik_id, satir_no, sutun_no)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING oturma_id
        """
        params = (
            oturma_data['sinav_id'],
            oturma_data['ogrenci_no'],
            oturma_data['derslik_id'],
            oturma_data.get('satir', oturma_data.get('satir_no')),
            oturma_data.get('sutun', oturma_data.get('sutun_no'))
        )
        
        result = self.db.execute_query(query, params)
        return result[0]['oturma_id']
    
    def delete_by_sinav(self, sinav_id: int) -> bool:
        """Delete all seating for an exam"""
        query = "DELETE FROM oturma_planlari WHERE sinav_id = %s"
        self.db.execute_query(query, (sinav_id,), fetch=False)
        logger.info(f"✅ Seating plan deleted for exam: {sinav_id}")
        return True
    
    def check_seat_available(self, sinav_id: int, derslik_id: int, satir: int, sutun: int) -> bool:
        """Check if a seat is available"""
        query = """
            SELECT COUNT(*) as count
            FROM oturma_planlari
            WHERE sinav_id = %s AND derslik_id = %s AND satir_no = %s AND sutun_no = %s
        """
        result = self.db.execute_query(query, (sinav_id, derslik_id, satir, sutun))
        return result[0]['count'] == 0
