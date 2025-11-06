"""
Sınav Model - CRUD Operations
"""

import logging
from typing import List, Dict, Optional
from models.database import DatabaseManager

logger = logging.getLogger(__name__)


class SinavModel:
    """Exam data access layer"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_programs_by_bolum(self, bolum_id: int) -> List[Dict]:
        """Get all exam programs for a department"""
        query = """
            SELECT sp.program_id, sp.bolum_id, sp.program_adi, sp.sinav_tipi, 
                   sp.baslangic_tarihi, sp.bitis_tarihi, b.bolum_adi
            FROM sinav_programi sp
            LEFT JOIN bolumler b ON sp.bolum_id = b.bolum_id
            WHERE sp.bolum_id = %s
            ORDER BY sp.baslangic_tarihi DESC
        """
        return self.db.execute_query(query, (bolum_id,))
    
    def get_sinavlar_by_program(self, program_id: int) -> List[Dict]:
        """Get all exams in a program"""
        query = """
            SELECT s.sinav_id, s.program_id, s.ders_id, s.tarih, 
                   s.baslangic_saati, s.bitis_saati, s.ogrenci_sayisi,
                   d.ders_kodu, d.ders_adi, d.ogretim_elemani,
                   STRING_AGG(dr.derslik_kodu, ', ') as derslik_kodu,
                   STRING_AGG(dr.derslik_adi, ', ') as derslik_adi,
                   (s.tarih || ' ' || s.baslangic_saati) as tarih_saat
            FROM sinavlar s
            JOIN dersler d ON s.ders_id = d.ders_id
            LEFT JOIN sinav_derslikleri sd ON s.sinav_id = sd.sinav_id
            LEFT JOIN derslikler dr ON sd.derslik_id = dr.derslik_id
            WHERE s.program_id = %s
            GROUP BY s.sinav_id, d.ders_kodu, d.ders_adi, d.ogretim_elemani
            ORDER BY s.tarih, s.baslangic_saati
        """
        return self.db.execute_query(query, (program_id,))
    
    def create_program(self, program_data: Dict) -> int:
        """Create exam program"""
        query = """
            INSERT INTO sinav_programi
            (bolum_id, program_adi, sinav_tipi, baslangic_tarihi, bitis_tarihi)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING program_id
        """
        params = (
            program_data['bolum_id'],
            program_data['program_adi'],
            program_data.get('sinav_tipi', 'Final'),
            program_data['baslangic_tarihi'],
            program_data['bitis_tarihi']
        )
        
        result = self.db.execute_query(query, params)
        logger.info(f"✅ Exam program created: {program_data['program_adi']}")
        return result[0]['program_id']
    
    def insert_sinav(self, sinav_data: Dict) -> int:
        """Insert new exam"""
        query = """
            INSERT INTO sinavlar
            (program_id, ders_id, tarih, baslangic_saati, bitis_saati)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING sinav_id
        """
        params = (
            sinav_data['program_id'],
            sinav_data['ders_id'],
            sinav_data['tarih'],
            sinav_data['baslangic_saati'],
            sinav_data['bitis_saati']
        )
        
        result = self.db.execute_query(query, params)
        logger.info(f"✅ Exam created: {sinav_data['ders_id']}")
        return result[0]['sinav_id']
    
    def assign_derslik(self, sinav_id: int, derslik_id: int) -> bool:
        """Assign classroom to exam"""
        query = """
            INSERT INTO sinav_derslikleri (sinav_id, derslik_id)
            VALUES (%s, %s)
            ON CONFLICT (sinav_id, derslik_id) DO NOTHING
        """
        self.db.execute_query(query, (sinav_id, derslik_id), fetch=False)
        logger.info(f"✅ Classroom assigned to exam: {sinav_id}")
        return True

    def insert_exam_with_classrooms(self, sinav_data: Dict, derslik_ids: List[int]) -> int:
        """Insert exam and assign classrooms atomically in a single transaction.

        Rolls back if any assignment violates constraints (e.g., classroom conflicts).
        Returns created sinav_id on success.
        """
        # Ensure unique and valid classroom IDs
        unique_derslik_ids = [did for did in dict.fromkeys(derslik_ids) if isinstance(did, int)]
        if not unique_derslik_ids:
            # Still allow creating the exam without classrooms
            unique_derslik_ids = []

        insert_exam_sql = """
            INSERT INTO sinavlar (program_id, ders_id, tarih, baslangic_saati, bitis_saati)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING sinav_id
        """
        insert_assign_sql = """
            INSERT INTO sinav_derslikleri (sinav_id, derslik_id)
            VALUES (%s, %s)
            ON CONFLICT (sinav_id, derslik_id) DO NOTHING
        """

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    insert_exam_sql,
                    (
                        sinav_data['program_id'],
                        sinav_data['ders_id'],
                        sinav_data['tarih'],
                        sinav_data['baslangic_saati'],
                        sinav_data['bitis_saati'],
                    ),
                )
                row = cursor.fetchone()
                sinav_id = row['sinav_id'] if isinstance(row, dict) else row[0]

                # Assign classrooms
                for derslik_id in unique_derslik_ids:
                    cursor.execute(insert_assign_sql, (sinav_id, derslik_id))

                conn.commit()
                logger.info(
                    f"✅ Exam created with classrooms: sinav_id={sinav_id}, derslik_ids={unique_derslik_ids}"
                )
                return sinav_id
            except Exception as e:
                conn.rollback()
                logger.error(
                    f"❌ Transaction failed for ders_id={sinav_data.get('ders_id')} with classrooms {unique_derslik_ids}: {e}"
                )
                raise
    
    def delete_program(self, program_id: int) -> bool:
        """Delete exam program"""
        query = "DELETE FROM sinav_programi WHERE program_id = %s"
        self.db.execute_query(query, (program_id,), fetch=False)
        logger.info(f"✅ Exam program deleted: {program_id}")
        return True
    
    def get_sinav_by_id(self, sinav_id: int) -> Optional[Dict]:
        """Get exam details by ID"""
        query = """
            SELECT s.sinav_id, s.program_id, s.ders_id, s.tarih, 
                   s.baslangic_saati, s.bitis_saati, s.ogrenci_sayisi,
                   d.ders_kodu, d.ders_adi, d.sinif,
                   (s.tarih || ' ' || s.baslangic_saati) as tarih_saat
            FROM sinavlar s
            JOIN dersler d ON s.ders_id = d.ders_id
            WHERE s.sinav_id = %s
        """
        result = self.db.execute_query(query, (sinav_id,))
        return result[0] if result else None
    
    def get_sinav_derslikleri(self, sinav_id: int) -> List[Dict]:
        """Get all classrooms assigned to an exam"""
        query = """
            SELECT dr.derslik_id, dr.derslik_kodu, dr.derslik_adi,
                   dr.kapasite, dr.satir_sayisi, dr.sutun_sayisi, dr.sira_yapisi
            FROM sinav_derslikleri sd
            JOIN derslikler dr ON sd.derslik_id = dr.derslik_id
            WHERE sd.sinav_id = %s
            ORDER BY dr.derslik_kodu
        """
        return self.db.execute_query(query, (sinav_id,))
def get_program_by_id(self, program_id: int) -> Optional[Dict]:
    """Get program details by ID"""
    query = """
        SELECT program_id, bolum_id, program_adi, sinav_tipi,
               baslangic_tarihi, bitis_tarihi, aktif
        FROM sinav_programi
        WHERE program_id = %s
    """
    result = self.db.execute_query(query, (program_id,))
    return result[0] if result else None