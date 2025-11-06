"""
Login Controller
Authentication and authorization logic
"""

import logging
from typing import Dict, Optional
from models.database import db
from models.user_model import UserModel
from utils.password_utils import PasswordUtils

logger = logging.getLogger(__name__)


class LoginController:
    """Login and authentication controller"""
    
    def __init__(self):
        self.user_model = UserModel(db)
        self.password_utils = PasswordUtils()
    
    def login(self, email: str, password: str) -> Dict:
        """
        Authenticate user with email and password
        
        Args:
            email: User email address
            password: User password (plain text)
            
        Returns:
            Dictionary with success status, message, and user data
        """
        try:
            # Validate input
            if not email or not password:
                return {
                    'success': False,
                    'message': "E-posta ve şifre gereklidir!"
                }
            
            # Get user by email
            user = self.user_model.get_user_by_email(email)
            
            if not user:
                logger.warning(f"Login attempt for non-existent user: {email}")
                return {
                    'success': False,
                    'message': "E-posta veya şifre hatalı!"
                }
            
            # Verify password
            if not self.password_utils.verify_password(password, user['password_hash']):
                logger.warning(f"Failed login attempt for user: {email}")
                return {
                    'success': False,
                    'message': "E-posta veya şifre hatalı!"
                }
            
            # Successful login
            logger.info(f"Successful login for user: {email}")
            
            # Return user data (without password)
            user_data = {
                'user_id': user['user_id'],
                'email': user['email'],
                'ad_soyad': user['ad_soyad'],
                'role': user['role'],
                'bolum_id': user.get('bolum_id')
            }
            
            return {
                'success': True,
                'message': "Giriş başarılı!",
                'user': user_data
            }
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {
                'success': False,
                'message': f"Giriş sırasında hata oluştu: {str(e)}"
            }
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict:
        """Change user password"""
        try:
            # Get user
            user = self.user_model.get_user_by_id(user_id)
            
            if not user:
                return {'success': False, 'message': "Kullanıcı bulunamadı!"}
            
            # Verify old password
            if not self.password_utils.verify_password(old_password, user['password_hash']):
                return {'success': False, 'message': "Mevcut şifre hatalı!"}
            
            # Validate new password
            is_valid, message = self.password_utils.validate_password(new_password)
            if not is_valid:
                return {'success': False, 'message': message}
            
            # Hash new password
            hashed_password = self.password_utils.hash_password(new_password)
            
            # Update password
            self.user_model.update_password(user_id, hashed_password)
            
            logger.info(f"Password changed for user: {user['email']}")
            
            return {
                'success': True,
                'message': "Şifre başarıyla değiştirildi!"
            }
            
        except Exception as e:
            logger.error(f"Password change error: {e}")
            return {'success': False, 'message': str(e)}
    
    def logout(self, user_id: int) -> Dict:
        """Logout user"""
        try:
            # Clear any session data if needed
            logger.info(f"User logged out: {user_id}")
            
            return {
                'success': True,
                'message': "Çıkış yapıldı!"
            }
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return {'success': False, 'message': str(e)}
