"""
Validation Utilities
Input validation and data validation functions
"""

import re
from typing import Tuple
from datetime import datetime


class Validators:
    """Data validation utilities"""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Validate email address
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "E-posta adresi boş olamaz"
        
        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False, "Geçersiz e-posta adresi formatı"
        
        return True, "Geçerli"
    
    @staticmethod
    def validate_student_number(ogrenci_no: str) -> Tuple[bool, str]:
        """
        Validate student number
        
        Args:
            ogrenci_no: Student number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not ogrenci_no:
            return False, "Öğrenci numarası boş olamaz"
        
        # Assume student number is 9-10 digits
        if not ogrenci_no.isdigit():
            return False, "Öğrenci numarası sadece rakam içermelidir"
        
        if len(ogrenci_no) < 9 or len(ogrenci_no) > 10:
            return False, "Öğrenci numarası 9-10 haneli olmalıdır"
        
        return True, "Geçerli"
    
    @staticmethod
    def validate_course_code(ders_kodu: str) -> Tuple[bool, str]:
        """
        Validate course code
        
        Args:
            ders_kodu: Course code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not ders_kodu:
            return False, "Ders kodu boş olamaz"
        
        # Assume course code format: ABC123 or ABC1234
        pattern = r'^[A-Z]{2,4}\d{3,4}$'
        
        if not re.match(pattern, ders_kodu.upper()):
            return False, "Geçersiz ders kodu formatı (örn: BMU101)"
        
        return True, "Geçerli"
    
    @staticmethod
    def validate_classroom_code(derslik_kodu: str) -> Tuple[bool, str]:
        """
        Validate classroom code
        
        Args:
            derslik_kodu: Classroom code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not derslik_kodu:
            return False, "Derslik kodu boş olamaz"
        
        # Allow various formats: A101, B-201, AMF1, etc.
        pattern = r'^[A-Z]{1,4}-?\d{1,4}$'
        
        if not re.match(pattern, derslik_kodu.upper()):
            return False, "Geçersiz derslik kodu formatı (örn: A101)"
        
        return True, "Geçerli"
    
    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime) -> Tuple[bool, str]:
        """
        Validate date range
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if start_date >= end_date:
            return False, "Bitiş tarihi başlangıç tarihinden sonra olmalıdır"
        
        # Check if dates are not too far apart (e.g., more than 1 year)
        delta = end_date - start_date
        if delta.days > 365:
            return False, "Tarih aralığı 1 yıldan fazla olamaz"
        
        return True, "Geçerli"
    
    @staticmethod
    def validate_capacity(capacity: int, max_capacity: int = 500) -> Tuple[bool, str]:
        """
        Validate classroom capacity
        
        Args:
            capacity: Capacity to validate
            max_capacity: Maximum allowed capacity
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if capacity <= 0:
            return False, "Kapasite 0'dan büyük olmalıdır"
        
        if capacity > max_capacity:
            return False, f"Kapasite {max_capacity}'den büyük olamaz"
        
        return True, "Geçerli"
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 255) -> str:
        """
        Sanitize string input
        
        Args:
            text: Text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not text:
            return ""
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
