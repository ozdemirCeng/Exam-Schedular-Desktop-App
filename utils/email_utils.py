"""
E-posta Gönderme Utility
SMTP ile e-posta gönderme işlemleri
"""

import smtplib
import secrets
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """E-posta gönderme servisi"""
    
    def __init__(self):
        """E-posta ayarlarını yükle"""
        self._load_email_config()
    
    def _load_email_config(self):
        """System settings'den e-posta ayarlarını yükle"""
        try:
            with open('config/system_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                email_config = settings.get('email', {})
                
                self.smtp_host = email_config.get('host', 'smtp.gmail.com')
                self.smtp_port = email_config.get('port', 587)
                self.smtp_user = email_config.get('user', 'ozdmromer24@gmail.com')
                self.smtp_password = email_config.get('password', 'tjtlvaduflkwacxq')
                self.from_email = email_config.get('from', 'noreply@kocaeli.edu.tr')
                
                logger.info(f"E-posta ayarları yüklendi: {self.smtp_host}:{self.smtp_port}")
        except Exception as e:
            logger.error(f"E-posta ayarları yüklenemedi: {e}")
            # Varsayılan değerler
            self.smtp_host = 'smtp.gmail.com'
            self.smtp_port = 587
            self.smtp_user = 'ozdmromer24@gmail.com'
            self.smtp_password = 'tjtlvaduflkwacxq'
            self.from_email = 'noreply@kocaeli.edu.tr'
    
    def send_email(self, to_email: str, subject: str, body_html: str, body_text: Optional[str] = None) -> bool:
        """
        E-posta gönder
        
        Args:
            to_email: Alıcı e-posta adresi
            subject: E-posta konusu
            body_html: HTML formatında e-posta içeriği
            body_text: Düz metin formatında e-posta içeriği (opsiyonel)
        
        Returns:
            bool: Başarılı ise True
        """
        if not self.smtp_user or not self.smtp_password:
            logger.error("E-posta ayarları yapılmamış")
            return False
        
        try:
            # E-posta mesajı oluştur
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Düz metin varsa ekle
            if body_text:
                part1 = MIMEText(body_text, 'plain', 'utf-8')
                msg.attach(part1)
            
            # HTML içerik ekle
            part2 = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(part2)
            
            # SMTP bağlantısı kur ve gönder
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"E-posta başarıyla gönderildi: {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("E-posta kimlik doğrulama hatası - Kullanıcı adı veya şifre yanlış")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP hatası: {e}")
            return False
        except Exception as e:
            logger.error(f"E-posta gönderme hatası: {e}")
            return False
    
    def send_new_password_email(self, to_email: str, new_password: str, user_name: str) -> bool:
        """
        Yeni şifre e-postası gönder
        
        Args:
            to_email: Kullanıcı e-posta adresi
            new_password: Yeni oluşturulan şifre
            user_name: Kullanıcı adı
        
        Returns:
            bool: Başarılı ise True
        """
        subject = "🔐 Yeni Şifreniz - Kocaeli Üniversitesi"
        
        # HTML içerik
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #00A651 0%, #007A3D 100%);
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 600;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .content h2 {{
                    color: #1e293b;
                    margin-top: 0;
                    font-size: 22px;
                }}
                .token-box {{
                    background-color: #f8fafc;
                    border: 2px dashed #00A651;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                    text-align: center;
                }}
                .token {{
                    font-size: 32px;
                    font-weight: 700;
                    color: #00A651;
                    letter-spacing: 4px;
                    font-family: 'Courier New', monospace;
                }}
                .warning {{
                    background-color: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    margin: 25px 0;
                    border-radius: 4px;
                }}
                .warning p {{
                    margin: 0;
                    color: #92400e;
                    font-size: 14px;
                }}
                .footer {{
                    background-color: #f8fafc;
                    padding: 25px 30px;
                    text-align: center;
                    color: #64748b;
                    font-size: 13px;
                    border-top: 1px solid #e2e8f0;
                }}
                .info {{
                    color: #64748b;
                    font-size: 14px;
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Şifre Sıfırlama</h1>
                </div>
                <div class="content">
                    <h2>Merhaba {user_name},</h2>
                    <p>Sınav Takvimi Yönetim Sistemi hesabınız için şifre sıfırlama talebinde bulundunuz.</p>
                    
                    <p>Yeni şifreniz aşağıdadır:</p>
                    
                    <div class="token-box">
                        <div class="token">{new_password}</div>
                        <p class="info">Bu şifreyle giriş yapabilirsiniz</p>
                    </div>
                    
                    <div class="warning">
                        <p><strong>⚠️ Önemli:</strong> Güvenliğiniz için <strong>ilk girişte şifrenizi değiştirmeniz</strong> önerilir. Ayarlar bölümünden şifrenizi değiştirebilirsiniz.</p>
                    </div>
                    
                    <p class="info">
                        Eğer bu talebi siz yapmadıysanız, lütfen derhal sistem yöneticisi ile iletişime geçin.
                    </p>
                </div>
                <div class="footer">
                    <p><strong>Kocaeli Üniversitesi</strong><br>
                    Sınav Takvimi Yönetim Sistemi<br>
                    © 2025 - Tüm hakları saklıdır</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Düz metin versiyonu
        body_text = f"""
        Yeni Şifreniz - Kocaeli Üniversitesi
        
        Merhaba {user_name},
        
        Sınav Takvimi Yönetim Sistemi hesabınız için şifre sıfırlama talebinde bulundunuz.
        
        Yeni Şifreniz: {new_password}
        
        Bu şifreyle giriş yapabilirsiniz.
        
        ÖNEMLİ: Güvenliğiniz için ilk girişte şifrenizi değiştirmeniz önerilir. 
        Ayarlar bölümünden şifrenizi değiştirebilirsiniz.
        
        Eğer bu talebi siz yapmadıysanız, lütfen derhal sistem yöneticisi ile iletişime geçin.
        
        Kocaeli Üniversitesi
        Sınav Takvimi Yönetim Sistemi
        © 2025
        """
        
        return self.send_email(to_email, subject, body_html, body_text)


def generate_secure_password(length: int = 12) -> str:
    """
    Güvenli rastgele şifre oluştur
    
    Args:
        length: Şifre uzunluğu (varsayılan 12)
    
    Returns:
        str: Güvenli şifre
    """
    import string
    
    # Şifre karakterleri: büyük harf, küçük harf, rakam
    chars = string.ascii_letters + string.digits
    
    # Güvenli rastgele şifre oluştur
    password = ''.join(secrets.choice(chars) for _ in range(length))
    
    return password


def reset_user_password(db, user_id: int) -> Optional[str]:
    """
    Kullanıcı şifresini sıfırla ve yeni şifre oluştur
    
    Args:
        db: DatabaseManager instance
        user_id: Kullanıcı ID
    
    Returns:
        str: Yeni şifre veya None
    """
    import bcrypt
    
    try:
        logger.info(f"Şifre sıfırlama başlıyor: User ID {user_id}")
        
        new_password = generate_secure_password(12)
        logger.info(f"Yeni şifre oluşturuldu: {len(new_password)} karakter")
        
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        hashed_str = hashed_password.decode('utf-8')
        logger.info(f"Şifre hashlendi: {len(hashed_str)} karakter")
        
        # Veritabanında güncelle - context manager ile doğru kullanım
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET password_hash = %s
                WHERE user_id = %s
            """, (hashed_str, user_id))
            
            affected_rows = cursor.rowcount
            logger.info(f"Güncellenen satır sayısı: {affected_rows}")
            
            if affected_rows == 0:
                logger.error(f"Kullanıcı bulunamadı: User ID {user_id}")
                return None
        
        logger.info(f"Şifre başarıyla sıfırlandı: User ID {user_id}")
        return new_password
        
    except Exception as e:
        logger.error(f"Şifre sıfırlama hatası - Tip: {type(e).__name__}, Mesaj: {str(e)}", exc_info=True)
        return None

