"""
Derslik (Classroom) Controller
Business logic for classroom management
"""

import logging

logger = logging.getLogger(__name__)


class DerslikController:
    """Classroom business logic controller"""
    
    def __init__(self, derslik_model):
        self.derslik_model = derslik_model
    
    def create_derslik(self, derslik_data: dict) -> dict:
        """Create new classroom"""
        try:
            derslik_id = self.derslik_model.insert_derslik(derslik_data)
            
            if derslik_id:
                return {
                    'success': True,
                    'message': f"✅ Derslik başarıyla eklendi!",
                    'derslik_id': derslik_id
                }
            else:
                return {
                    'success': False,
                    'message': "❌ Derslik eklenirken hata oluştu!"
                }
                
        except Exception as e:
            logger.error(f"Error creating derslik: {e}")
            return {
                'success': False,
                'message': f"❌ Hata: {str(e)}"
            }
    
    def update_derslik(self, derslik_id: int, derslik_data: dict) -> dict:
        """Update existing classroom"""
        try:
            success = self.derslik_model.update_derslik(derslik_id, derslik_data)
            
            if success:
                return {
                    'success': True,
                    'message': "✅ Derslik başarıyla güncellendi!"
                }
            else:
                return {
                    'success': False,
                    'message': "❌ Derslik güncellenirken hata oluştu!"
                }
                
        except Exception as e:
            logger.error(f"Error updating derslik: {e}")
            return {
                'success': False,
                'message': f"❌ Hata: {str(e)}"
            }
    
    def delete_derslik(self, derslik_id: int) -> dict:
        """Delete classroom"""
        try:
            success = self.derslik_model.delete_derslik(derslik_id)
            
            if success:
                return {
                    'success': True,
                    'message': "✅ Derslik başarıyla silindi!"
                }
            else:
                return {
                    'success': False,
                    'message': "❌ Derslik silinirken hata oluştu!"
                }
                
        except Exception as e:
            logger.error(f"Error deleting derslik: {e}")
            return {
                'success': False,
                'message': f"❌ Hata: {str(e)}"
            }
