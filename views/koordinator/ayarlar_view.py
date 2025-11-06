"""
Koordinatör Ayarları View
Sadece koordinatöre özel kullanıcı tercihleri ve profil ayarları
"""

import logging
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QCheckBox, QMessageBox,
    QGroupBox, QFormLayout, QComboBox, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from models.user_model import UserModel
from models.database import db
from utils.password_utils import PasswordUtils
from utils.modern_dialogs import ModernMessageBox

logger = logging.getLogger(__name__)

# Ayarlar dosyası yolu
SETTINGS_FILE = Path(__file__).parent.parent.parent / 'config' / 'user_preferences.json'


class AyarlarView(QWidget):
    """Koordinatör ayarları - Kullanıcı tercihleri ve profil"""
    
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.user_model = UserModel(db)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup UI with scroll"""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Set scroll widget
        scroll.setWidget(scroll_content)
        
        # Add scroll to main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Ayarlar")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        
        subtitle = QLabel("Kullanıcı tercihleri ve profil ayarları")
        subtitle.setStyleSheet("color: #666; font-size: 13px;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        layout.addWidget(header)
        layout.addWidget(subtitle)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #e0e0e0; max-height: 1px;")
        layout.addWidget(divider)
        
        # User Profile Card
        profile_card = QGroupBox("Profil Bilgileri")
        profile_card.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        profile_layout = QFormLayout(profile_card)
        profile_layout.setSpacing(16)
        profile_layout.setContentsMargins(20, 20, 20, 20)
        
        # Read-only user info
        name_label = QLabel(self.user_data.get('ad_soyad', 'Kullanıcı'))
        name_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        name_label.setStyleSheet("color: #2c3e50; padding: 4px;")
        profile_layout.addRow("Ad Soyad:", name_label)
        
        email_label = QLabel(self.user_data.get('email', ''))
        email_label.setStyleSheet("color: #34495e; padding: 4px;")
        profile_layout.addRow("E-posta:", email_label)
        
        role_label = QLabel(self.user_data.get('role', ''))
        role_label.setStyleSheet("color: #16a085; font-weight: bold; padding: 4px;")
        profile_layout.addRow("Rol:", role_label)
        
        layout.addWidget(profile_card)
        
        # Appearance Settings Card
        appearance_card = QGroupBox("Görünüm Tercihleri")
        appearance_card.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        appearance_layout = QFormLayout(appearance_card)
        appearance_layout.setSpacing(16)
        appearance_layout.setContentsMargins(20, 20, 20, 20)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Açık Tema", "Koyu Tema", "Sistem Teması"])
        self.theme_combo.setFixedHeight(36)
        self.theme_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
            }
            QComboBox:hover {
                border-color: #3498db;
            }
        """)
        appearance_layout.addRow("Tema:", self.theme_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Türkçe", "English"])
        self.language_combo.setFixedHeight(36)
        self.language_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
            }
            QComboBox:hover {
                border-color: #3498db;
            }
        """)
        appearance_layout.addRow("Dil:", self.language_combo)
        
        self.notifications_check = QCheckBox("Bildirimler aktif")
        self.notifications_check.setChecked(True)
        self.notifications_check.setStyleSheet("padding: 4px; font-size: 13px;")
        appearance_layout.addRow("", self.notifications_check)
        
        self.auto_save_check = QCheckBox("Otomatik kaydetme")
        self.auto_save_check.setChecked(True)
        self.auto_save_check.setStyleSheet("padding: 4px; font-size: 13px;")
        appearance_layout.addRow("", self.auto_save_check)
        
        layout.addWidget(appearance_card)
        
        # Password Change Card
        password_card = QGroupBox("Şifre Değiştir")
        password_card.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        password_layout = QFormLayout(password_card)
        password_layout.setSpacing(16)
        password_layout.setContentsMargins(20, 20, 20, 20)
        
        self.current_password = QLineEdit()
        self.current_password.setEchoMode(QLineEdit.Password)
        self.current_password.setPlaceholderText("Mevcut şifrenizi girin")
        self.current_password.setFixedHeight(36)
        self.current_password.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        password_layout.addRow("Mevcut Şifre:", self.current_password)
        
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setPlaceholderText("Yeni şifrenizi girin (min. 6 karakter)")
        self.new_password.setFixedHeight(36)
        self.new_password.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        password_layout.addRow("Yeni Şifre:", self.new_password)
        
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setPlaceholderText("Yeni şifrenizi tekrar girin")
        self.confirm_password.setFixedHeight(36)
        self.confirm_password.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        password_layout.addRow("Şifre Tekrar:", self.confirm_password)
        
        change_password_btn = QPushButton("Şifreyi Değiştir")
        change_password_btn.setFixedHeight(40)
        change_password_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:pressed {
                background-color: #c0392b;
            }
        """)
        change_password_btn.setCursor(Qt.PointingHandCursor)
        change_password_btn.clicked.connect(self.change_password)
        password_layout.addRow("", change_password_btn)
        
        layout.addWidget(password_card)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        reset_btn = QPushButton("↺ Varsayılana Dön")
        reset_btn.setFixedHeight(44)
        reset_btn.setFixedWidth(160)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.clicked.connect(self.reset_settings)
        
        save_btn = QPushButton("💾 Ayarları Kaydet")
        save_btn.setObjectName("primaryBtn")
        save_btn.setFixedHeight(44)
        save_btn.setFixedWidth(160)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.save_settings)
        
        button_layout.addStretch()
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
    
    def load_settings(self):
        """Load user preferences from file"""
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    user_id = str(self.user_data.get('user_id', ''))
                    
                    if user_id in settings:
                        prefs = settings[user_id]
                        
                        # Load theme
                        theme_idx = prefs.get('theme', 0)
                        self.theme_combo.setCurrentIndex(theme_idx)
                        
                        # Load language
                        lang_idx = prefs.get('language', 0)
                        self.language_combo.setCurrentIndex(lang_idx)
                        
                        # Load checkboxes
                        self.notifications_check.setChecked(prefs.get('notifications', True))
                        self.auto_save_check.setChecked(prefs.get('auto_save', True))
                        
                        logger.info(f"User preferences loaded for user {user_id}")
        except Exception as e:
            logger.warning(f"Could not load user preferences: {e}")
    
    def save_settings(self):
        """Save user preferences to file"""
        try:
            # Load existing settings
            settings = {}
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            # Update current user's settings
            user_id = str(self.user_data.get('user_id', ''))
            settings[user_id] = {
                'theme': self.theme_combo.currentIndex(),
                'language': self.language_combo.currentIndex(),
                'notifications': self.notifications_check.isChecked(),
                'auto_save': self.auto_save_check.isChecked()
            }
            
            # Ensure config directory exists
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to file
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            logger.info(f"User preferences saved for user {user_id}")
            
            QMessageBox.information(
                self,
                "Başarılı",
                "✅ Tercihleriniz başarıyla kaydedildi!\n\n"
                "Bazı değişiklikler uygulamayı yeniden başlattığınızda aktif olacaktır."
            )
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            ModernMessageBox.error(
                self, "Hata", "Ayarlar kaydedilirken oluştu", f"{str(e)}"
            )
    
    def reset_settings(self):
        """Reset settings to default"""
        confirmed = ModernMessageBox.question(
            self,
            "Ayarları Sıfırla",
            "Tüm tercihleri varsayılan değerlere döndürmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirmed:
            # Reset to defaults
            self.theme_combo.setCurrentIndex(0)
            self.language_combo.setCurrentIndex(0)
            self.auto_save_check.setChecked(True)
            self.notifications_check.setChecked(True)
            
            QMessageBox.information(
                self,
                "Başarılı",
                "✅ Tercihler varsayılan değerlere sıfırlandı!"
            )
    
    def change_password(self):
        """Change user password"""
        current_pwd = self.current_password.text().strip()
        new_pwd = self.new_password.text().strip()
        confirm_pwd = self.confirm_password.text().strip()
        
        # Validation
        if not current_pwd:
            ModernMessageBox.warning(self, "Uyarı", "⚠️ Mevcut şifrenizi girin!")
            return
        
        if not new_pwd:
            ModernMessageBox.warning(self, "Uyarı", "⚠️ Yeni şifrenizi girin!")
            return
        
        if len(new_pwd) < 6:
            ModernMessageBox.warning(self, "Uyarı", "⚠️ Yeni şifre en az 6 karakter olmalıdır!")
            return
        
        if new_pwd != confirm_pwd:
            ModernMessageBox.warning(self, "Uyarı", "⚠️ Yeni şifreler eşleşmiyor!")
            return
        
        try:
            # Verify current password
            user_id = self.user_data.get('user_id')
            user = self.user_model.get_by_id(user_id)
            
            if not user:
                ModernMessageBox.error(self, "Hata", "❌ Kullanıcı bulunamadı!")
                return
            
            # Check current password
            if not PasswordUtils.verify_password(current_pwd, user['sifre']):
                ModernMessageBox.warning(self, "Hata", "❌ Mevcut şifre yanlış!")
                return
            
            # Update password
            hashed_password = PasswordUtils.hash_password(new_pwd)
            success = self.user_model.update_password(user_id, hashed_password)
            
            if success:
                # Clear fields
                self.current_password.clear()
                self.new_password.clear()
                self.confirm_password.clear()
                
                QMessageBox.information(
                    self,
                    "Başarılı",
                    "✅ Şifreniz başarıyla değiştirildi!"
                )
                logger.info(f"Password changed for user {user_id}")
            else:
                ModernMessageBox.error(self, "Hata", "❌ Şifre değiştirilemedi!")
                
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            ModernMessageBox.error(
                self, "Hata", "Şifre değiştirilirken oluştu", f"{str(e)}"
            )
