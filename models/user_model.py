"""
User Model - CRUD Operations
"""

import logging
from typing import List, Dict, Optional
from models.database import DatabaseManager

logger = logging.getLogger(__name__)


class UserModel:
    """User data access layer"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        query = """
            SELECT user_id, email, password_hash, ad_soyad, role, bolum_id, aktif
            FROM users
            WHERE email = %s AND aktif = TRUE
        """
        result = self.db.execute_query(query, (email,))
        return result[0] if result else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        query = """
            SELECT user_id, email, password_hash as sifre, ad_soyad, role, bolum_id, aktif
            FROM users
            WHERE user_id = %s AND aktif = TRUE
        """
        result = self.db.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def get_users_by_role(self, role: str) -> List[Dict]:
        """Get all users with a specific role"""
        query = """
            SELECT user_id, email, ad_soyad, role, bolum_id, aktif
            FROM users
            WHERE role = %s AND aktif = TRUE
            ORDER BY ad_soyad
        """
        return self.db.execute_query(query, (role,))
    
    def insert_user(self, user_data: Dict) -> int:
        """Insert new user"""
        query = """
            INSERT INTO users (email, password_hash, ad_soyad, role, bolum_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id
        """
        params = (
            user_data['email'],
            user_data['password_hash'],
            user_data['ad_soyad'],
            user_data['role'],
            user_data.get('bolum_id')
        )
        
        result = self.db.execute_query(query, params)
        logger.info(f"✅ User created: {user_data['email']}")
        return result[0]['user_id']
    
    def update_user(self, user_id: int, user_data: Dict) -> bool:
        """Update user"""
        query = """
            UPDATE users
            SET email = %s,
                ad_soyad = %s,
                role = %s,
                bolum_id = %s
            WHERE user_id = %s
        """
        params = (
            user_data['email'],
            user_data['ad_soyad'],
            user_data['role'],
            user_data.get('bolum_id'),
            user_id
        )
        
        self.db.execute_query(query, params, fetch=False)
        logger.info(f"✅ User updated: {user_id}")
        return True
    
    def update_password(self, user_id: int, hashed_password: str) -> bool:
        """Update user password"""
        query = """
            UPDATE users
            SET password_hash = %s,
                son_sifre_degisimi = CURRENT_TIMESTAMP
            WHERE user_id = %s
        """
        self.db.execute_query(query, (hashed_password, user_id), fetch=False)
        logger.info(f"✅ Password updated for user: {user_id}")
        return True
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user (soft delete)"""
        query = "UPDATE users SET aktif = FALSE WHERE user_id = %s"
        self.db.execute_query(query, (user_id,), fetch=False)
        logger.info(f"✅ User deleted: {user_id}")
        return True
