#!/usr/bin/env python3
"""
Admin şifresini güncelle
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.password_utils import PasswordUtils
from models.database import db

# Yeni şifre oluştur
new_password = "admin123"
hashed = PasswordUtils.hash_password(new_password)

print(f"Hashed password: {hashed}")

# Veritabanında güncelle
try:
    query = "UPDATE users SET password_hash = %s WHERE email = %s"
    with db.get_cursor(commit=True) as cursor:
        if cursor:
            cursor.execute(query, (hashed, 'admin@kocaeli.edu.tr'))
            print(f"✅ Admin şifresi güncellendi!")
            print(f"Email: admin@kocaeli.edu.tr")
            print(f"Şifre: {new_password}")
        else:
            print("❌ Veritabanı bağlantısı başarısız")
except Exception as e:
    print(f"❌ Hata: {e}")
