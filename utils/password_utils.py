"""
Password Utilities
Secure password hashing and validation
"""

import re
import bcrypt
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class PasswordUtils:
    """Password hashing and validation utilities"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Şifre en az 8 karakter olmalıdır"
        
        if not re.search(r'[A-Z]', password):
            return False, "Şifre en az 1 büyük harf içermelidir"
        
        if not re.search(r'[a-z]', password):
            return False, "Şifre en az 1 küçük harf içermelidir"
        
        if not re.search(r'[0-9]', password):
            return False, "Şifre en az 1 rakam içermelidir"
        
        return True, "Şifre geçerli"
    
    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """
        Generate random secure password
        
        Args:
            length: Password length (default: 12)
            
        Returns:
            Random password string
        """
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Ensure password meets requirements
        while True:
            is_valid, _ = PasswordUtils.validate_password(password)
            if is_valid:
                break
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        return password
