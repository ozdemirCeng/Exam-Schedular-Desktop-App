"""
Ders (Course) Controller
Business logic for course management
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class DersController:
    """Course business logic controller"""
    
    def __init__(self, ders_model):
        self.ders_model = ders_model
    
    def create_ders(self, ders_data: Dict) -> Dict:
        """Create new course with detailed validation"""
        try:
            import re
            
            # Validate required fields
            if not ders_data.get('ders_kodu'):
                return {'success': False, 'message': "Ders kodu gereklidir"}
            
            if not ders_data.get('ders_adi'):
                return {'success': False, 'message': "Ders adı gereklidir"}
            
            if not ders_data.get('ogretim_elemani'):
                return {'success': False, 'message': "Öğretim elemanı gereklidir"}
            
            # Validate course code format (ABC123)
            ders_kodu = str(ders_data['ders_kodu']).strip().upper()
            if not re.match(r'^[A-Z]{3}\d{3}$', ders_kodu):
                return {
                    'success': False,
                    'message': f"Geçersiz ders kodu formatı: '{ders_kodu}' (Beklenen: ABC123)"
                }
            
            # Normalize the code
            ders_data['ders_kodu'] = ders_kodu
            
            # Check for duplicate
            existing = self.ders_model.get_ders_by_kod(
                ders_data['bolum_id'],
                ders_data['ders_kodu']
            )
            
            if existing:
                return {
                    'success': False,
                    'message': f"Bu ders kodu zaten kayıtlı"
                }
            
            # Create course
            ders_id = self.ders_model.insert_ders(ders_data)
            
            return {
                'success': True,
                'message': f"Ders başarıyla oluşturuldu!",
                'ders_id': ders_id
            }
            
        except Exception as e:
            logger.error(f"Error creating course: {e}", exc_info=True)
            return {'success': False, 'message': f"Veritabanı hatası: {str(e)}"}
    
    def update_ders(self, ders_id: int, ders_data: Dict) -> Dict:
        """Update course"""
        try:
            self.ders_model.update_ders(ders_id, ders_data)
            
            return {
                'success': True,
                'message': f"Ders başarıyla güncellendi!"
            }
            
        except Exception as e:
            logger.error(f"Error updating course: {e}")
            return {'success': False, 'message': str(e)}
    
    def delete_ders(self, ders_id: int) -> Dict:
        """Delete course"""
        try:
            self.ders_model.delete_ders(ders_id)
            
            return {
                'success': True,
                'message': f"Ders başarıyla silindi!"
            }
            
        except Exception as e:
            logger.error(f"Error deleting course: {e}")
            return {'success': False, 'message': str(e)}
    
    def bulk_import_courses(self, courses: List[Dict], bolum_id: int) -> Dict:
        """Bulk import courses"""
        try:
            success_count = 0
            error_count = 0
            errors = []
            
            for course in courses:
                course['bolum_id'] = bolum_id
                result = self.create_ders(course)
                
                if result['success']:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{course['ders_kodu']}: {result['message']}")
            
            return {
                'success': True,
                'message': f"{success_count} ders başarıyla eklendi, {error_count} hata.",
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error bulk importing courses: {e}")
            return {'success': False, 'message': str(e)}
