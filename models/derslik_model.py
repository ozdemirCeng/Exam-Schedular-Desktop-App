"""
Derslik Model - CRUD İşlemleri
"""

import logging
from typing import List, Dict, Optional
from models.database import DatabaseManager

logger = logging.getLogger(__name__)


class DerslikModel:
    """Derslik veri erişim katmanı"""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def get_derslikler_by_bolum(self, bolum_id: int) -> List[Dict]:
        """Bölüme ait tüm derslikleri getir"""
        query = """
                SELECT derslik_id, \
                       bolum_id, \
                       derslik_kodu, \
                       derslik_adi, \
                       kapasite, \
                       satir_sayisi, \
                       sutun_sayisi, \
                       sira_yapisi, \
                       aktif
                FROM derslikler
                WHERE bolum_id = %s \
                  AND aktif = TRUE
                ORDER BY derslik_kodu \
                """
        return self.db.execute_query(query, (bolum_id,))

    def get_derslik_by_id(self, derslik_id: int) -> Optional[Dict]:
        """ID'ye göre derslik getir"""
        query = """
                SELECT d.*, \
                       b.bolum_adi
                FROM derslikler d
                         JOIN bolumler b ON d.bolum_id = b.bolum_id
                WHERE d.derslik_id = %s \
                """
        result = self.db.execute_query(query, (derslik_id,))
        return result[0] if result else None

    def get_derslik_by_kod(self, bolum_id: int, derslik_kodu: str) -> Optional[Dict]:
        """Derslik koduna göre ara"""
        query = """
                SELECT * \
                FROM derslikler
                WHERE bolum_id = %s \
                  AND derslik_kodu = %s \
                  AND aktif = TRUE \
                """
        result = self.db.execute_query(query, (bolum_id, derslik_kodu))
        return result[0] if result else None

    def insert_derslik(self, derslik_data: Dict) -> int:
        """Yeni derslik ekle"""
        query = """
                INSERT INTO derslikler
                (bolum_id, derslik_kodu, derslik_adi, kapasite,
                 satir_sayisi, sutun_sayisi, sira_yapisi)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING derslik_id \
                """
        params = (
            derslik_data['bolum_id'],
            derslik_data['derslik_kodu'],
            derslik_data['derslik_adi'],
            derslik_data['kapasite'],
            derslik_data['satir_sayisi'],
            derslik_data['sutun_sayisi'],
            derslik_data['sira_yapisi']
        )

        result = self.db.execute_query(query, params)
        logger.info(f"✅ Derslik eklendi: {derslik_data['derslik_kodu']}")
        return result[0]['derslik_id']

    def update_derslik(self, derslik_id: int, derslik_data: Dict) -> bool:
        """Derslik güncelle"""
        try:
            query = """
                    UPDATE derslikler
                    SET derslik_kodu = %s,
                        derslik_adi  = %s,
                        kapasite     = %s,
                        satir_sayisi = %s,
                        sutun_sayisi = %s,
                        sira_yapisi  = %s
                    WHERE derslik_id = %s
                    RETURNING derslik_id
                    """
            params = (
                derslik_data['derslik_kodu'],
                derslik_data['derslik_adi'],
                derslik_data['kapasite'],
                derslik_data['satir_sayisi'],
                derslik_data['sutun_sayisi'],
                derslik_data['sira_yapisi'],
                derslik_id
            )

            result = self.db.execute_query(query, params)
            if result and len(result) > 0:
                logger.info(f"✅ Derslik güncellendi: {derslik_id} - {derslik_data['derslik_kodu']}")
                return True
            else:
                logger.warning(f"⚠️ Derslik güncellenemedi, ID bulunamadı: {derslik_id}")
                return False
        except Exception as e:
            logger.error(f"❌ Derslik güncelleme hatası: {e}", exc_info=True)
            raise

    def delete_derslik(self, derslik_id: int) -> bool:
        """Derslik sil (soft delete)"""
        try:
            query = """
                UPDATE derslikler 
                SET aktif = FALSE 
                WHERE derslik_id = %s 
                RETURNING derslik_id, derslik_kodu
            """
            result = self.db.execute_query(query, (derslik_id,))
            if result and len(result) > 0:
                logger.info(f"✅ Derslik silindi: {derslik_id} - {result[0].get('derslik_kodu', '')}")
                return True
            else:
                logger.warning(f"⚠️ Derslik silinemedi, ID bulunamadı: {derslik_id}")
                return False
        except Exception as e:
            logger.error(f"❌ Derslik silme hatası: {e}", exc_info=True)
            raise

    def check_derslik_kullanimi(self, derslik_id: int) -> Dict:
        """Dersliğin sınav programında kullanım durumunu kontrol et"""
        query = """
                SELECT COUNT(DISTINCT sd.sinav_id)   as sinav_sayisi, \
                       COUNT(DISTINCT op.ogrenci_no) as ogrenci_sayisi
                FROM sinav_derslikleri sd
                         LEFT JOIN oturma_planlari op ON sd.sinav_id = op.sinav_id
                    AND sd.derslik_id = op.derslik_id
                WHERE sd.derslik_id = %s \
                """
        result = self.db.execute_query(query, (derslik_id,))
        return result[0] if result else {'sinav_sayisi': 0, 'ogrenci_sayisi': 0}

    def validate_derslik_data(self, data: Dict) -> tuple[bool, str]:
        """Derslik verilerini doğrula"""
        # Kapasite kontrolü
        if data['kapasite'] <= 0:
            return False, "Kapasite 0'dan büyük olmalıdır"

        # Satır/sütun kontrolü
        if data['satir_sayisi'] <= 0 or data['sutun_sayisi'] <= 0:
            return False, "Satır ve sütun sayısı 0'dan büyük olmalıdır"

        # Sıra yapısı kontrolü
        if data['sira_yapisi'] <= 0:
            return False, "Sıra yapısı 0'dan büyük olmalıdır"

        # Kapasite hesaplama kontrolü
        hesaplanan_kapasite = data['satir_sayisi'] * data['sutun_sayisi']
        if data['kapasite'] > hesaplanan_kapasite:
            return False, f"Kapasite, satır×sütun ({hesaplanan_kapasite}) değerinden büyük olamaz"

        return True, "OK"
