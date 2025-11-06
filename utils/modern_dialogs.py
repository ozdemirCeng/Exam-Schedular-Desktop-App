"""
Modern Dialog Utilities
Özelleştirilmiş, modern ve esnek dialog'lar
"""

import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollArea, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


def sanitize_filename(filename):
    """
    Dosya adını temizle - Türkçe karakterleri dönüştür ve geçersiz karakterleri kaldır
    
    Args:
        filename: Temizlenecek dosya adı
        
    Returns:
        Temizlenmiş dosya adı
    """
    # Türkçe karakterleri İngilizce karşılıklarına çevir
    turkish_map = {
        'ç': 'c', 'Ç': 'C',
        'ğ': 'g', 'Ğ': 'G',
        'ı': 'i', 'İ': 'I',
        'ö': 'o', 'Ö': 'O',
        'ş': 's', 'Ş': 'S',
        'ü': 'u', 'Ü': 'U'
    }
    
    for turkish, english in turkish_map.items():
        filename = filename.replace(turkish, english)
    
    # Windows'ta geçersiz karakterleri temizle: < > : " / \ | ? *
    # Boşlukları alt çizgi ile değiştir
    filename = filename.replace(' ', '_')
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Çoklu alt çizgileri tek alt çizgiye çevir
    filename = re.sub(r'_+', '_', filename)
    
    # Başta ve sonda alt çizgi varsa temizle
    filename = filename.strip('_')
    
    return filename


class ModernMessageBox(QDialog):
    """Modern, esnek message box"""
    
    # Dialog türleri
    INFORMATION = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    QUESTION = "question"
    
    def __init__(self, parent=None, title="", message="", details="", dialog_type=INFORMATION):
        super().__init__(parent)
        self.dialog_type = dialog_type
        self.result_value = False
        
        # Normalize details - None'ı empty string'e çevir
        if details is None:
            details = ""
        
        self.setWindowTitle(title)
        self.setModal(True)
        
        # Dinamik boyut - mesaja göre büyüsün/küçülsün
        message_length = len(message) + len(details)
        
        if message_length < 100:
            # Küçük mesaj
            self.setMinimumWidth(400)
            self.setMaximumWidth(550)
        elif message_length < 300:
            # Orta boyut mesaj
            self.setMinimumWidth(500)
            self.setMaximumWidth(700)
        else:
            # Büyük mesaj
            self.setMinimumWidth(600)
            self.setMaximumWidth(900)
        
        self.setup_ui(title, message, details)
        
    def setup_ui(self, title, message, details):
        """Setup modern UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self._create_header(title)
        layout.addWidget(header)
        
        # Content
        content = QFrame()
        content.setStyleSheet("QFrame { background: white; border: none; }")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 24, 32, 24)
        content_layout.setSpacing(16)
        
        # Message (auto-sizing)
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setFont(QFont("Segoe UI", 11))
        msg_label.setStyleSheet("color: #1e293b; line-height: 1.6;")
        msg_label.setTextFormat(Qt.PlainText)
        
        # Mesaj uzunluğuna göre scroll ekle
        if len(message) > 500 or message.count('\n') > 10:
            scroll = QScrollArea()
            scroll.setWidget(msg_label)
            scroll.setWidgetResizable(True)
            scroll.setMaximumHeight(300)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
            content_layout.addWidget(scroll)
        else:
            content_layout.addWidget(msg_label)
        
        # Details (opsiyonel,접기/açılabilir)
        if details:
            details_frame = QFrame()
            details_frame.setStyleSheet("""
                QFrame {
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 16px;
                }
            """)
            details_layout = QVBoxLayout(details_frame)
            
            details_label = QLabel("📋 Detaylar:")
            details_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            details_label.setStyleSheet("color: #64748b;")
            details_layout.addWidget(details_label)
            
            details_text = QTextEdit()
            details_text.setPlainText(details)
            details_text.setReadOnly(True)
            details_text.setMaximumHeight(200)
            details_text.setFont(QFont("Consolas", 9))
            details_text.setStyleSheet("""
                QTextEdit {
                    background: white;
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                    padding: 8px;
                    color: #475569;
                }
            """)
            details_layout.addWidget(details_text)
            content_layout.addWidget(details_frame)
        
        layout.addWidget(content)
        
        # Footer buttons
        footer = self._create_footer()
        layout.addWidget(footer)
        
        # Oval kenarlıklar
        self.setStyleSheet("""
            QDialog {
                background: white;
                border-radius: 16px;
            }
        """)
    
    def _create_header(self, title):
        """Create colored header based on type"""
        header = QFrame()
        
        # Renkler ve ikonlar
        type_config = {
            self.INFORMATION: ("ℹ️", "#00A651", "#ecfdf5"),
            self.SUCCESS: ("✅", "#10b981", "#ecfdf5"),
            self.WARNING: ("⚠️", "#f59e0b", "#fffbeb"),
            self.ERROR: ("❌", "#ef4444", "#fef2f2"),
            self.QUESTION: ("❓", "#00A651", "#ecfdf5")
        }
        
        icon, color, bg = type_config.get(self.dialog_type, type_config[self.INFORMATION])
        
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {bg}, stop:1 {color}15);
                border: none;
                border-radius: 16px 16px 0 0;
                padding: 24px 32px;
            }}
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setSpacing(16)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 32))
        header_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet(f"color: {color}; background: transparent;")
        header_layout.addWidget(title_label, 1)
        
        return header
    
    def _create_footer(self):
        """Create footer with buttons"""
        footer = QFrame()
        footer.setStyleSheet("QFrame { background: #f8fafc; border: none; border-radius: 0 0 16px 16px; }")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(32, 16, 32, 16)
        footer_layout.addStretch()
        
        if self.dialog_type == self.QUESTION:
            # Yes/No buttons
            no_btn = QPushButton("Hayır")
            no_btn.setFixedHeight(40)
            no_btn.setFixedWidth(100)
            no_btn.setCursor(Qt.PointingHandCursor)
            no_btn.setStyleSheet("""
                QPushButton {
                    background: white;
                    border: 2px solid #e2e8f0;
                    border-radius: 12px;
                    color: #64748b;
                    font-weight: 600;
                    font-size: 13px;
                    outline: none;
                }
                QPushButton:hover {
                    background: #f8fafc;
                    border-color: #cbd5e1;
                }
                QPushButton:focus {
                    outline: none;
                }
            """)
            no_btn.clicked.connect(self.reject)
            footer_layout.addWidget(no_btn)
            
            yes_btn = QPushButton("Evet")
            yes_btn.setFixedHeight(40)
            yes_btn.setFixedWidth(100)
            yes_btn.setCursor(Qt.PointingHandCursor)
            yes_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #00A651, stop:1 #10b981);
                    border: none;
                    border-radius: 12px;
                    color: white;
                    font-weight: 600;
                    font-size: 13px;
                    outline: none;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #008F46, stop:1 #00A651);
                }
                QPushButton:focus {
                    outline: none;
                }
            """)
            yes_btn.clicked.connect(self.accept)
            footer_layout.addWidget(yes_btn)
        else:
            # Single OK button
            ok_btn = QPushButton("Tamam")
            ok_btn.setFixedHeight(40)
            ok_btn.setFixedWidth(120)
            ok_btn.setCursor(Qt.PointingHandCursor)
            
            # Buton rengi dialog türüne göre
            if self.dialog_type == self.SUCCESS:
                btn_color = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #14b8a6)"
                btn_hover = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #0d9488)"
            elif self.dialog_type == self.ERROR:
                btn_color = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #f87171)"
                btn_hover = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dc2626, stop:1 #ef4444)"
            elif self.dialog_type == self.WARNING:
                btn_color = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f59e0b, stop:1 #fbbf24)"
                btn_hover = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #f59e0b)"
            else:
                btn_color = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00A651, stop:1 #10b981)"
                btn_hover = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #008F46, stop:1 #00A651)"
            
            ok_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {btn_color};
                    border: none;
                    border-radius: 12px;
                    color: white;
                    font-weight: 600;
                    font-size: 13px;
                    outline: none;
                }}
                QPushButton:hover {{
                    background: {btn_hover};
                }}
                QPushButton:focus {{
                    outline: none;
                }}
            """)
            ok_btn.clicked.connect(self.accept)
            footer_layout.addWidget(ok_btn)
        
        return footer
    
    @staticmethod
    def information(parent, title, message, details=""):
        """Show information dialog"""
        dialog = ModernMessageBox(parent, title, message, details, ModernMessageBox.INFORMATION)
        dialog.exec()
    
    @staticmethod
    def success(parent, title, message, details=""):
        """Show success dialog"""
        dialog = ModernMessageBox(parent, title, message, details, ModernMessageBox.SUCCESS)
        dialog.exec()
    
    @staticmethod
    def warning(parent, title, message, details=""):
        """Show warning dialog"""
        dialog = ModernMessageBox(parent, title, message, details, ModernMessageBox.WARNING)
        dialog.exec()
    
    @staticmethod
    def error(parent, title, message, details=""):
        """Show error dialog"""
        dialog = ModernMessageBox(parent, title, message, details, ModernMessageBox.ERROR)
        dialog.exec()
    
    @staticmethod
    def question(parent, title, message, details=""):
        """Show question dialog - returns True if Yes, False if No"""
        dialog = ModernMessageBox(parent, title, message, details, ModernMessageBox.QUESTION)
        return dialog.exec() == QDialog.Accepted

