"""
Modern Login View - Kocaeli Üniversitesi Sınav Takvimi Sistemi
Professional, production-ready login interface with PySide6
"""

import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox, QGraphicsOpacityEffect,
    QApplication
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal, Property
from PySide6.QtGui import QFont, QColor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from styles.theme import KocaeliTheme
from controllers.login_controller import LoginController
from models.database import db
import logging

logger = logging.getLogger(__name__)


class AnimatedBackground(QWidget):
    """Animated gradient background with floating particles"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []
        self.gradient_offset = 0

        # Create particles (lightweight - fewer particles, slower update)
        import random
        for _ in range(10):
            self.particles.append({
                'x': random.randint(0, 800),
                'y': random.randint(0, 600),
                'size': random.randint(2, 6),
                'speed': random.uniform(0.3, 1.5),
                'opacity': random.uniform(0.1, 0.25)
            })

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(100)  # 100ms instead of 50ms for better performance

    def update_particles(self):
        self.gradient_offset = (self.gradient_offset + 0.5) % 360
        for p in self.particles:
            p['y'] -= p['speed']
            if p['y'] < -10:
                p['y'] = self.height() + 10
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QLinearGradient, QBrush
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Animated gradient
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(0, 166, 81))
        gradient.setColorAt(0.5, QColor(0, 143, 71))
        gradient.setColorAt(1, QColor(0, 122, 61))
        painter.fillRect(self.rect(), gradient)

        # Draw particles
        for p in self.particles:
            painter.setOpacity(p['opacity'])
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(int(p['x']), int(p['y']), p['size'], p['size'])


class LoadingSpinner(QWidget):
    """Modern loading spinner with smooth animation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self._angle = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)

    def get_angle(self):
        return self._angle

    def set_angle(self, angle):
        self._angle = angle
        self.update()

    angle = Property(int, get_angle, set_angle)

    def start(self):
        self.timer.start(30)  # 30ms instead of 20ms
        self.show()

    def stop(self):
        self.timer.stop()
        self.hide()

    def rotate(self):
        self._angle = (self._angle + 10) % 360
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QPen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.rect().center())
        painter.rotate(self._angle)

        pen = QPen(QColor("#00A651"))
        pen.setWidth(4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        for i in range(8):
            opacity = 1.0 - (i * 0.12)
            painter.setOpacity(opacity)
            painter.drawLine(0, -15, 0, -8)
            painter.rotate(45)


class SimpleInput(QWidget):
    """Simple, clean input field without complex animations"""

    textChanged = Signal(str)
    returnPressed = Signal()

    def __init__(self, label_text, placeholder="", is_password=False, parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.placeholder = placeholder or label_text
        self.is_password = is_password
        self.password_visible = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Label
        self.label = QLabel(self.label_text)
        self.label.setObjectName("inputLabel")
        self.label.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        layout.addWidget(self.label)

        # Input container
        self.container = QFrame()
        self.container.setObjectName("inputContainer")
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(16, 14, 16, 14)
        container_layout.setSpacing(12)

        # Input field
        self.input = QLineEdit()
        self.input.setObjectName("simpleInput")
        self.input.setFont(QFont("Segoe UI", 14))
        self.input.setPlaceholderText(self.placeholder)
        self.input.setMinimumHeight(24)

        if self.is_password:
            self.input.setEchoMode(QLineEdit.Password)

        self.input.textChanged.connect(self.textChanged.emit)
        self.input.returnPressed.connect(self.returnPressed.emit)
        self.input.focusInEvent = self.on_focus_in
        self.input.focusOutEvent = self.on_focus_out

        container_layout.addWidget(self.input)

        # Show password button for password inputs
        if self.is_password:
            self.show_pass_btn = QPushButton("👁️")
            self.show_pass_btn.setObjectName("showPassBtn")
            self.show_pass_btn.setCheckable(True)
            self.show_pass_btn.setFixedSize(36, 36)
            self.show_pass_btn.setCursor(Qt.PointingHandCursor)
            self.show_pass_btn.setToolTip("Şifreyi göster/gizle")
            self.show_pass_btn.clicked.connect(self.toggle_password_visibility)
            container_layout.addWidget(self.show_pass_btn)

        layout.addWidget(self.container)

    def on_focus_in(self, event):
        self.container.setProperty("focused", True)
        self.container.style().unpolish(self.container)
        self.container.style().polish(self.container)
        QLineEdit.focusInEvent(self.input, event)

    def on_focus_out(self, event):
        self.container.setProperty("focused", False)
        self.container.style().unpolish(self.container)
        self.container.style().polish(self.container)
        QLineEdit.focusOutEvent(self.input, event)

    def text(self):
        return self.input.text()

    def clear(self):
        self.input.clear()

    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.password_visible:
            self.input.setEchoMode(QLineEdit.Password)
            self.show_pass_btn.setText("👁️")
            self.password_visible = False
        else:
            self.input.setEchoMode(QLineEdit.Normal)
            self.show_pass_btn.setText("🙈")
            self.password_visible = True


class ModernButton(QPushButton):
    """Modern button with ripple effect and smooth transitions"""

    def __init__(self, text, primary=True, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setObjectName("primaryBtn" if primary else "secondaryBtn")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(54)
        self.setFont(QFont("Segoe UI", 11, QFont.DemiBold))


class LoginView(QWidget):
    """Professional login screen with database authentication"""

    login_success = Signal(dict)  # User data

    def __init__(self, login_controller=None):
        super().__init__()
        self.login_controller = login_controller or LoginController()
        self.password_visible = False

        self.setWindowTitle("Kocaeli Üniversitesi - Sınav Takvimi Sistemi")
        self.setMinimumSize(1200, 700)
        self.resize(1200, 700)

        # Center window
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left panel - Branding
        left_panel = self.create_branding_panel()
        main_layout.addWidget(left_panel, 11)

        # Right panel - Login form
        right_panel = self.create_login_panel()
        main_layout.addWidget(right_panel, 9)

    def create_branding_panel(self):
        """Left panel - Animated branding"""
        panel = QFrame()
        panel.setObjectName("brandingPanel")

        # Animated background
        self.bg_animation = AnimatedBackground(panel)
        self.bg_animation.setGeometry(panel.rect())

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(80, 80, 80, 80)
        layout.setAlignment(Qt.AlignCenter)

        content = QWidget()
        content.setObjectName("brandingContent")
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)
        content_layout.setAlignment(Qt.AlignCenter)

        # University logo/icon
        logo_label = QLabel("🎓")
        logo_label.setObjectName("brandLogo")
        logo_label.setFont(QFont("Segoe UI Emoji", 80))
        logo_label.setAlignment(Qt.AlignCenter)

        # University name
        uni_name = QLabel("KOCAELİ ÜNİVERSİTESİ")
        uni_name.setObjectName("uniName")
        uni_name.setFont(QFont("Segoe UI", 14, QFont.Bold))
        uni_name.setAlignment(Qt.AlignCenter)

        # Main title
        title = QLabel("Sınav Takvimi\nYönetim Sistemi")
        title.setObjectName("brandTitle")
        title.setFont(QFont("Segoe UI", 42, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        # Announcements card
        features_card = QFrame()
        features_card.setObjectName("featuresCard")
        features_layout = QVBoxLayout(features_card)
        features_layout.setContentsMargins(32, 28, 32, 28)
        features_layout.setSpacing(18)
        
        # Load announcements asynchronously (don't block UI)
        QTimer.singleShot(100, lambda: self._load_announcements(features_layout))

        content_layout.addWidget(logo_label)
        content_layout.addWidget(uni_name)
        content_layout.addSpacing(10)
        content_layout.addWidget(title)
        content_layout.addSpacing(30)
        content_layout.addWidget(features_card)

        layout.addStretch()
        layout.addWidget(content)
        layout.addStretch()

        return panel

    def create_login_panel(self):
        """Right panel - Modern login form"""
        panel = QFrame()
        panel.setObjectName("loginPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        # Form container with shadow
        form_container = QFrame()
        form_container.setObjectName("formContainer")
        form_container.setMaximumWidth(480)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(48, 48, 48, 48)
        form_layout.setSpacing(24)

        # Header section
        header = QLabel("Hoş Geldiniz")
        header.setObjectName("formHeader")
        header.setFont(QFont("Segoe UI", 28, QFont.Bold))

        subheader = QLabel("Sisteme giriş yapmak için bilgilerinizi girin")
        subheader.setObjectName("formSubheader")
        subheader.setFont(QFont("Segoe UI", 13))
        subheader.setWordWrap(True)

        # Input fields
        self.email_input = SimpleInput("E-posta Adresi", "ornek@kocaeli.edu.tr")
        self.password_input = SimpleInput("Şifre", "••••••••", is_password=True)
        self.password_input.returnPressed.connect(self.handle_login)

        # Remember me and forgot password
        options_layout = QHBoxLayout()
        options_layout.setSpacing(15)

        self.remember_check = QCheckBox("Beni hatırla")
        self.remember_check.setObjectName("rememberCheck")
        self.remember_check.setFont(QFont("Segoe UI", 10))
        self.remember_check.setCursor(Qt.PointingHandCursor)

        forgot_btn = QPushButton("Şifremi unuttum")
        forgot_btn.setObjectName("linkBtn")
        forgot_btn.setCursor(Qt.PointingHandCursor)
        forgot_btn.clicked.connect(self.handle_forgot_password)

        options_layout.addWidget(self.remember_check)
        options_layout.addStretch()
        options_layout.addWidget(forgot_btn)

        # Message label (error/success)
        self.message_label = QLabel()
        self.message_label.setObjectName("messageLabel")
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.hide()

        # Login button with spinner
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)

        self.login_btn = ModernButton("Giriş Yap →", primary=True)
        self.login_btn.clicked.connect(self.handle_login)

        self.spinner = LoadingSpinner()
        self.spinner.hide()

        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.spinner)
        button_layout.setAlignment(self.spinner, Qt.AlignCenter)

        # Footer info
        footer = QLabel("© 2025 Kocaeli Üniversitesi - Tüm hakları saklıdır")
        footer.setObjectName("footerLabel")
        footer.setFont(QFont("Segoe UI", 9))
        footer.setAlignment(Qt.AlignCenter)

        # Assembly
        form_layout.addWidget(header)
        form_layout.addWidget(subheader)
        form_layout.addSpacing(20)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.password_input)
        form_layout.addLayout(options_layout)
        form_layout.addWidget(self.message_label)
        form_layout.addSpacing(8)
        form_layout.addWidget(button_container)
        form_layout.addSpacing(24)
        form_layout.addWidget(footer)

        layout.addWidget(form_container)
        return panel

    def handle_login(self):
        """Real login process - Controller call"""
        # Prevent double login attempts
        if hasattr(self, '_logging_in') and self._logging_in:
            return
            
        email = self.email_input.text().strip()
        password = self.password_input.text()

        # Validation
        if not email:
            self.show_message("Lütfen e-posta adresinizi girin", "error")
            self.email_input.input.setFocus()
            return

        if not password:
            self.show_message("Lütfen şifrenizi girin", "error")
            self.password_input.input.setFocus()
            return

        if '@' not in email or '.' not in email:
            self.show_message("Geçerli bir e-posta adresi girin", "error")
            self.email_input.input.setFocus()
            return

        # Set login flag
        self._logging_in = True
        
        # Loading state
        self.set_loading_state(True)

        # Button animation
        self.animate_button_click()

        # Real controller call (faster response)
        QTimer.singleShot(200, lambda: self.authenticate(email, password))

    def authenticate(self, email, password):
        """Real database authentication"""
        try:
            # Controller login check
            result = self.login_controller.login(email, password)

            if result['success']:
                self.show_message(f"Hoş geldiniz, {result['user']['ad_soyad']}!", "success")
                QTimer.singleShot(400, lambda: self.login_success.emit(result['user']))
            else:
                self.show_message(result['message'], "error")
                self.set_loading_state(False)
                self._logging_in = False

        except Exception as e:
            self.show_message(f"Bağlantı hatası: {str(e)}", "error")
            self.set_loading_state(False)
            self._logging_in = False

    def set_loading_state(self, loading):
        """Set loading state"""
        if loading:
            self.login_btn.setEnabled(False)
            self.login_btn.setText("Giriş yapılıyor...")
            self.spinner.start()
            self.email_input.input.setEnabled(False)
            self.password_input.input.setEnabled(False)
        else:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Giriş Yap →")
            self.spinner.stop()
            self.email_input.input.setEnabled(True)
            self.password_input.input.setEnabled(True)

    def handle_forgot_password(self):
        """Forgot password process - Generate new password and send via email"""
        email = self.email_input.text().strip()
        
        if not email or '@' not in email:
            self.show_message("Lütfen geçerli bir e-posta adresi girin", "error")
            self.email_input.input.setFocus()
            return
        
        try:
            from models.database import DatabaseManager
            from utils.email_utils import EmailService, reset_user_password
            
            db = DatabaseManager()
            
            # Kullanıcıyı bul
            result = db.execute_query("""
                SELECT user_id, ad_soyad, email 
                FROM users 
                WHERE email = %s AND aktif = TRUE
            """, (email,), fetch=True)
            
            if not result:
                # Güvenlik için aynı mesajı göster (e-posta var mı yok mu belli olmasın)
                self.show_message(
                    "Eğer bu e-posta kayıtlıysa, yeni şifre gönderildi", 
                    "success"
                )
                return
            
            user = result[0]  # İlk satır (dict)
            user_id = user['user_id']  # Dict key ile erişim
            user_name = user['ad_soyad']  # Dict key ile erişim
            
            # Yeni şifre oluştur ve kaydet
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Şifre sıfırlama çağrılıyor: User ID {user_id}")
            
            new_password = reset_user_password(db, user_id)
            
            logger.info(f"reset_user_password sonucu: {new_password}")
            
            if not new_password:
                logger.error(f"Şifre oluşturulamadı, new_password = {new_password}")
                self.show_message("Şifre oluşturulamadı. Lütfen tekrar deneyin", "error")
                return
            
            # E-posta gönder
            email_service = EmailService()
            success = email_service.send_new_password_email(email, new_password, user_name)
            
            if success:
                self.show_message(
                    f"✅ Yeni şifreniz {email} adresine gönderildi\n"
                    f"E-postanızı kontrol edin", 
                    "success"
                )
            else:
                self.show_message(
                    "E-posta gönderilemedi. Lütfen daha sonra tekrar deneyin\n"
                    "veya sistem yöneticisi ile iletişime geçin", 
                    "error"
                )
            
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Şifre sıfırlama hatası - Tip: {type(e).__name__}, Mesaj: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.show_message(f"Bir hata oluştu: {str(e)}", "error")

    def animate_button_click(self):
        """Login button click animation"""
        try:
            original_style = self.login_btn.styleSheet()
            self.login_btn.setStyleSheet(original_style + """
                QPushButton {
                    transform: scale(0.95);
                }
            """)
            QTimer.singleShot(100, lambda: self.login_btn.setStyleSheet(original_style))
        except Exception as e:
            print(f"Animation error: {e}")

    def show_message(self, text, msg_type="info"):
        """Show message"""
        icons = {
            "error": "❌",
            "success": "✅",
            "info": "ℹ️"
        }
        icon = icons.get(msg_type, "ℹ️")

        self.message_label.setText(f"{icon} {text}")

        # Simple style
        if msg_type == "error":
            self.message_label.setStyleSheet("""
                QLabel {
                    color: #dc2626 !important;
                    background: #fef2f2 !important;
                    border: 2px solid #fca5a5 !important;
                    border-radius: 10px;
                    padding: 14px 18px;
                    font-size: 13px;
                    font-weight: 600;
                }
            """)
        elif msg_type == "success":
            self.message_label.setStyleSheet("""
                QLabel {
                    color: #16a34a !important;
                    background: #f0fdf4 !important;
                    border: 2px solid #86efac !important;
                    border-radius: 10px;
                    padding: 14px 18px;
                    font-size: 13px;
                    font-weight: 600;
                }
            """)
        else:
            self.message_label.setStyleSheet("""
                QLabel {
                    color: #2563eb !important;
                    background: #eff6ff !important;
                    border: 2px solid #93c5fd !important;
                    border-radius: 10px;
                    padding: 14px 18px;
                    font-size: 13px;
                    font-weight: 600;
                }
            """)

        self.message_label.show()
        self.message_label.setVisible(True)

        # Auto hide (faster)
        if msg_type != "error":
            QTimer.singleShot(2500, self.hide_message)

    def hide_message(self):
        """Hide message"""
        self.message_label.hide()
    
    def _load_announcements(self, layout):
        """Load active announcements from database"""
        try:
            # Try to load active announcements (with timeout)
            query = """
                SELECT metin 
                FROM duyurular 
                WHERE aktif = TRUE 
                ORDER BY olusturulma_tarihi DESC
                LIMIT 5
            """
            try:
                results = db.execute_query(query)
            except Exception as query_error:
                logger.debug(f"Query failed (table might not exist): {query_error}")
                results = None
            
            if results and len(results) > 0:
                # Add title
                title_label = QLabel("📢 Duyurular")
                title_label.setObjectName("featureText")
                title_label.setFont(QFont("Segoe UI", 15, QFont.Bold))
                title_label.setAlignment(Qt.AlignLeft)
                title_label.setStyleSheet("color: white; background: transparent;")
                layout.addWidget(title_label)
                
                # Add separator
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setStyleSheet("background: rgba(255, 255, 255, 0.3); max-height: 2px;")
                layout.addWidget(separator)
                
                # Add announcements
                for row in results:
                    announcement_item = QWidget()
                    announcement_item.setStyleSheet("background: transparent;")
                    announcement_layout = QHBoxLayout(announcement_item)
                    announcement_layout.setContentsMargins(0, 0, 0, 0)
                    announcement_layout.setSpacing(12)
                    
                    icon_label = QLabel("•")
                    icon_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
                    icon_label.setStyleSheet("color: white; background: transparent;")
                    
                    text_label = QLabel(row['metin'])
                    text_label.setObjectName("featureText")
                    text_label.setFont(QFont("Segoe UI", 13))
                    text_label.setWordWrap(True)
                    text_label.setStyleSheet("color: white; background: transparent;")
                    
                    announcement_layout.addWidget(icon_label)
                    announcement_layout.addWidget(text_label, 1)
                    layout.addWidget(announcement_item)
            else:
                # No announcements in DB, show default announcement
                self._show_default_features(layout)
                
        except Exception as e:
            logger.error(f"Error loading announcements: {e}")
            # Show default announcement on error
            self._show_default_features(layout)
    
    def _show_default_features(self, layout):
        """Show default announcement when no custom announcements"""
        # Add title
        title_label = QLabel("📢 Hoş Geldiniz")
        title_label.setObjectName("featureText")
        title_label.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title_label.setAlignment(Qt.AlignLeft)
        title_label.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(title_label)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background: rgba(255, 255, 255, 0.3); max-height: 2px;")
        layout.addWidget(separator)
        
        # Default announcement
        default_text = """Kocaeli Üniversitesi Sınav Takvimi Yönetim Sistemine hoş geldiniz. 

Bu sistem ile sınav programlarınızı kolayca oluşturabilir, derslik atamalarını otomatik yapabilir ve öğrenci oturma planlarını düzenleyebilirsiniz.

Giriş yaptıktan sonra ilgili bölüm için tüm sınav süreçlerini yönetebileceksiniz."""
        
        announcement_item = QWidget()
        announcement_item.setStyleSheet("background: transparent;")
        announcement_layout = QVBoxLayout(announcement_item)
        announcement_layout.setContentsMargins(0, 0, 0, 0)
        announcement_layout.setSpacing(8)
        
        text_label = QLabel(default_text)
        text_label.setObjectName("featureText")
        text_label.setFont(QFont("Segoe UI", 13))
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignLeft)
        text_label.setStyleSheet("color: white; background: transparent;")
        
        announcement_layout.addWidget(text_label)
        layout.addWidget(announcement_item)

    def resizeEvent(self, event):
        """Update background when window is resized"""
        super().resizeEvent(event)
        if hasattr(self, 'bg_animation'):
            for child in self.findChildren(QFrame):
                if child.objectName() == "brandingPanel":
                    self.bg_animation.setGeometry(child.rect())
                    break

    def apply_styles(self):
        """Apply ultra-modern theme styles"""
        self.setStyleSheet("""
            /* Global Styles */
            * {
                font-family: 'Segoe UI', 'San Francisco', 'Helvetica Neue', Arial, sans-serif;
                border: none;
                outline: none;
            }

            QWidget {
                background: #f8fafc;
            }

            /* Branding Panel */
            #brandingPanel {
                background: transparent;
            }

            #brandingContent {
                background: transparent;
            }

            #brandLogo {
                color: white !important;
                margin: 0;
                padding: 0;
                background: transparent !important;
                opacity: 1 !important;
            }

            #uniName {
                color: white !important;
                letter-spacing: 3px;
                background: transparent !important;
                opacity: 1 !important;
                font-weight: bold;
            }

            #brandTitle {
                color: white !important;
                line-height: 1.2;
                letter-spacing: -0.5px;
                background: transparent !important;
                opacity: 1 !important;
                font-weight: bold;
            }

            #featuresCard {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                opacity: 1 !important;
            }

            #featureText {
                color: white !important;
                font-weight: 600;
                background: transparent !important;
                opacity: 1 !important;
            }

            /* Login Panel */
            #loginPanel {
                background: #f8fafc;
            }

            #formContainer {
                background: white;
                border-radius: 20px;
                border: 1px solid #e5e7eb;
            }

            #formHeader {
                color: #111827;
                margin: 0;
                padding: 0;
                font-weight: 700;
                background: transparent;
            }

            #formSubheader {
                color: #6b7280;
                line-height: 1.6;
                font-weight: 400;
                background: transparent;
            }

            /* Input Label */
            #inputLabel {
                color: #1e293b;
                background: transparent;
                padding-left: 4px;
            }

            /* Simple Input Container */
            #inputContainer {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
            }

            #inputContainer:hover {
                border-color: #cbd5e1;
            }

            #inputContainer[focused="true"] {
                border: 2px solid #00A651;
            }

            /* Simple Input Field */
            #simpleInput {
                background: transparent;
                border: none;
                color: #1e293b;
                padding: 0px;
                selection-background-color: #00A651;
                selection-color: white;
                font-weight: 500;
            }

            #simpleInput::placeholder {
                color: #94a3b8;
            }

            /* Show Password Button */
            #showPassBtn {
                background: transparent;
                border: none;
                border-radius: 8px;
                font-size: 18px;
            }

            #showPassBtn:hover {
                background: #f1f5f9;
            }

            #showPassBtn:checked {
                background: #f0fdf4;
            }

            #showPassBtn:pressed {
                background: #e2e8f0;
            }

            /* Remember Me Checkbox */
            QCheckBox#rememberCheck {
                color: #475569;
                spacing: 8px;
            }

            QCheckBox#rememberCheck::indicator {
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid #cbd5e0;
                background: white;
            }

            QCheckBox#rememberCheck::indicator:hover {
                border: 2px solid #00A651;
            }

            QCheckBox#rememberCheck::indicator:checked {
                background: #00A651;
                border: 2px solid #00A651;
            }

            /* Buttons */
            #primaryBtn {
                background: #00A651;
                color: white;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 600;
                padding: 16px 32px;
                letter-spacing: 0.3px;
            }

            #primaryBtn:hover {
                background: #008F47;
            }

            #primaryBtn:pressed {
                background: #007A3D;
            }

            #primaryBtn:disabled {
                background: #cbd5e1;
                color: #94a3b8;
            }

            #linkBtn {
                color: #64748b;
                background: transparent;
                border: none;
                text-decoration: none;
                font-size: 11px;
                font-weight: 500;
                padding: 8px 12px;
                border-radius: 6px;
            }

            #linkBtn:hover {
                color: #00A651;
                background: rgba(0, 166, 81, 0.05);
            }

            #linkBtn:pressed {
                color: #007A3D;
            }

            /* Footer */
            #footerLabel {
                color: #94a3b8;
                letter-spacing: 0.3px;
                background: transparent;
            }
        """)

    def keyPressEvent(self, event):
        """Handle key press events"""
        # Enter key is handled by returnPressed signal on password field
        super().keyPressEvent(event)

    def clear(self):
        """Clear login fields"""
        self.email_input.clear()
        self.password_input.clear()
        self.set_loading_state(False)
