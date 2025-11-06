"""
Main Window - Professional Dashboard
Kocaeli Üniversitesi Sınav Takvimi Sistemi
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGraphicsOpacityEffect, QProgressBar,
    QApplication, QStackedWidget, QMessageBox
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, Signal
from PySide6.QtGui import QFont, QColor

sys.path.append(str(Path(__file__).parent.parent))

# Import views
from views.koordinator.bolum_secim_view import BolumSecimView
from views.koordinator.derslik_view import DerslikView
from views.koordinator.ders_yukle_view import DersYukleView
from views.koordinator.ogrenci_yukle_view import OgrenciYukleView
from views.koordinator.sinav_olustur_view import SinavOlusturView
from views.koordinator.oturma_plani_view import OturmaPlaniView
from views.koordinator.ayarlar_view import AyarlarView
from views.admin.kullanici_yonetimi_view import KullaniciYonetimiView
from views.admin.bolum_yonetimi_view import BolumYonetimiView
from views.admin.duyuru_yonetimi_view import DuyuruYonetimiView
from styles.theme import KocaeliTheme
from utils.modern_dialogs import ModernMessageBox

logger = logging.getLogger(__name__)


class Theme:
    """Modern Theme - Improved Design"""

    def __init__(self, dark_mode=False):
        self.dark_mode = dark_mode

    @property
    def bg(self):
        return "#0f172a" if self.dark_mode else "#f8fafc"

    @property
    def card(self):
        return "#1e293b" if self.dark_mode else "#ffffff"

    @property
    def border(self):
        return "#334155" if self.dark_mode else "#e2e8f0"

    @property
    def text(self):
        return "#f1f5f9" if self.dark_mode else "#1e293b"

    @property
    def text_muted(self):
        return "#94a3b8" if self.dark_mode else "#64748b"

    @property
    def hover(self):
        return "#334155" if self.dark_mode else "#f1f5f9"

    @property
    def sidebar(self):
        return "#1e293b" if self.dark_mode else "#ffffff"
    
    @property
    def accent(self):
        return "#10b981" if self.dark_mode else "#059669"
    
    @property
    def accent_light(self):
        return "#34d399" if self.dark_mode else "#10b981"

    @property
    def menu_active(self):
        if self.dark_mode:
            return "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669); color: #ffffff; border-left: 4px solid #34d399;"
        return "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ecfdf5, stop:1 #d1fae5); color: #065f46; border-left: 4px solid #10b981;"
    
    @property
    def shadow(self):
        return "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
    
    @property
    def shadow_lg(self):
        return "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"


class StatCard(QFrame):
    """Statistics card"""

    def __init__(self, label, value, total, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.value = value
        self.total = total
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header = QHBoxLayout()

        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 9))
        lbl.setStyleSheet(f"color: {theme.text_muted}; font-weight: 500;")

        val = QLabel(str(value))
        val.setFont(QFont("Segoe UI", 20, QFont.Bold))
        val.setStyleSheet("color: #10b981;")

        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(val)

        # Progress bar
        progress = QProgressBar()
        progress.setMaximum(total)
        progress.setValue(value)
        progress.setTextVisible(False)
        progress.setFixedHeight(8)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background: {"#334155" if theme.dark_mode else "#f3f4f6"};
                border-radius: 4px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #14b8a6);
                border-radius: 4px;
            }}
        """)

        # Total label
        total_lbl = QLabel(f"Toplam: {total}")
        total_lbl.setFont(QFont("Segoe UI", 8))
        total_lbl.setStyleSheet(f"color: {theme.text_muted};")

        layout.addLayout(header)
        layout.addWidget(progress)
        layout.addWidget(total_lbl)

        self.update_style()

    def update_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {self.theme.card};
                border: 1px solid {self.theme.border};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border: 1px solid #10b981;
            }}
        """)


class QuickActionCard(QFrame):
    """Quick action card"""

    clicked = Signal()

    def __init__(self, label, desc, icon, color, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.color = color
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Icon container
        icon_container = QFrame()
        icon_container.setFixedSize(48, 48)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 20))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_label)
        title = QLabel(label)
        title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title.setStyleSheet(f"color: {theme.text};")

        # Description
        description = QLabel(desc)
        description.setFont(QFont("Segoe UI", 9))
        description.setStyleSheet(f"color: {theme.text_muted};")

        layout.addWidget(icon_container)
        layout.addWidget(title)
        layout.addWidget(description)

        self.update_style()

    def update_style(self):
        color_map = {
            'emerald': ('#ecfdf5', '#10b981', '#d1fae5') if not self.theme.dark_mode else ('rgba(16, 185, 129, 0.1)', '#10b981', 'rgba(16, 185, 129, 0.2)'),
            'blue': ('#eff6ff', '#2563eb', '#dbeafe') if not self.theme.dark_mode else ('rgba(37, 99, 235, 0.1)', '#2563eb', 'rgba(37, 99, 235, 0.2)'),
            'indigo': ('#eef2ff', '#4f46e5', '#e0e7ff') if not self.theme.dark_mode else ('rgba(79, 70, 229, 0.1)', '#4f46e5', 'rgba(79, 70, 229, 0.2)'),
            'orange': ('#fff7ed', '#f97316', '#ffedd5') if not self.theme.dark_mode else ('rgba(249, 115, 22, 0.1)', '#f97316', 'rgba(249, 115, 22, 0.2)')
        }

        bg, text, border = color_map.get(self.color, color_map['emerald'])

        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            QFrame:hover {{
                transform: scale(1.05);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
        """)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class MenuButton(QPushButton):
    """Sidebar menu button"""

    def __init__(self, text, icon, theme, parent=None):
        super().__init__(parent)
        self.menu_text = text
        self.icon = icon
        self.theme = theme
        self.is_active = False
        self.is_collapsed = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)

        self.update_style()

    def set_active(self, active):
        self.is_active = active
        self.update_style()

    def set_collapsed(self, collapsed):
        self.is_collapsed = collapsed
        self.update_style()

    def update_style(self):
        if self.is_active:
            bg = self.theme.menu_active
            hover = self.theme.menu_active
        else:
            bg = f"background: transparent; color: {self.theme.text_muted}; border-left: 4px solid transparent;"
            hover = f"background: {self.theme.hover}; border-left: 4px solid {self.theme.border};"

        self.setStyleSheet(f"""
            QPushButton {{
                {bg}
                border: none;
                border-radius: 12px;
                text-align: left;
                padding-left: {"12px" if not self.is_collapsed else "0px"};
                font-size: 14px;
                font-weight: 500;
                min-height: 48px;
                margin: 2px 0px;
                outline: none;
            }}
            QPushButton:hover {{
                {hover}
            }}
            QPushButton:focus {{
                outline: none;
                border: none;
            }}
        """)

        if self.is_collapsed:
            self.setText(self.icon)
            self.setToolTip(self.menu_text)
        else:
            self.setText(f"{self.icon}  {self.menu_text}")


class MainWindow(QMainWindow):
    """Main window - Professional Dashboard"""

    module_opened = Signal(str)
    logout_requested = Signal()

    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.selected_bolum = None  # Seçilen bölüm bilgisi
        self.theme = Theme(dark_mode=False)
        self.sidebar_collapsed = False
        self.active_menu = 'dashboard'
        self.pages = {}  # Page cache
        self.is_impersonating = False
        self._original_user_data = None
        self.impersonated_user_data = None
        
        # Admin için bölüm kontrolü
        self.is_admin = user_data.get('role') == 'Admin'
        self.needs_bolum_selection = self.is_admin and not user_data.get('bolum_id')

        self.setWindowTitle(f"KOÜ Sınav Takvimi - {user_data.get('ad_soyad')}")
        self.setMinimumSize(1400, 800)

        self.setup_ui()
        self.apply_styles()

        self.showMaximized()

    def setup_ui(self):
        """UI setup"""
        central = QWidget()
        self.setCentralWidget(central)

        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Top bar
        self.top_bar = self.create_top_bar()
        self.main_layout.addWidget(self.top_bar)

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.sidebar = self.create_sidebar()
        content_layout.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()

        self.dashboard_page = self.create_dashboard_page()
        self.content_stack.addWidget(self.dashboard_page)
        self.pages['dashboard'] = self.dashboard_page

        content_layout.addWidget(self.content_stack, 1)

        self.main_layout.addWidget(content)

    def get_effective_user_data(self):
        """Return impersonated user data if in impersonation mode, else real user."""
        return self.impersonated_user_data if self.is_impersonating and self.impersonated_user_data else self.user_data

    def create_top_bar(self):
        """Create and return the top navigation bar"""
        bar = QFrame()
        bar.setFixedHeight(73)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 24, 0)

        # Logo + Title
        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setSpacing(16)
        logo = QLabel("🎓")
        logo.setFont(QFont("Segoe UI", 24))
        logo.setFixedSize(44, 44)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #10b981, stop:1 #14b8a6);
            border-radius: 11px;
        """)
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setSpacing(2)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Sınav Takvimi Yönetim Sistemi")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))

        subtitle = QLabel("Kocaeli Üniversitesi")
        subtitle.setFont(QFont("Segoe UI", 10))

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        logo_layout.addWidget(logo)
        logo_layout.addWidget(title_widget)

        layout.addWidget(logo_container)
        layout.addStretch()

        # Theme toggle
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setFixedSize(40, 40)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self.toggle_theme)

        # User info
        user_widget = QFrame()
        user_layout = QHBoxLayout(user_widget)
        user_layout.setSpacing(12)

        avatar = QLabel("👤")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFont(QFont("Segoe UI Emoji", 18))
        avatar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #10b981, stop:1 #14b8a6);
            border-radius: 9px;
        """)

        user_info = QWidget()
        user_info_layout = QVBoxLayout(user_info)
        user_info_layout.setSpacing(0)
        user_info_layout.setContentsMargins(0, 0, 0, 0)

        eff_user = self.get_effective_user_data()
        self.topbar_name_label = QLabel(eff_user.get('ad_soyad', 'Kullanıcı'))
        self.topbar_name_label.setFont(QFont("Segoe UI", 10, QFont.Bold))

        self.topbar_role_label = QLabel(eff_user.get('role', 'Admin'))
        self.topbar_role_label.setFont(QFont("Segoe UI", 8))

        user_info_layout.addWidget(self.topbar_name_label)
        user_info_layout.addWidget(self.topbar_role_label)

        user_layout.addWidget(avatar)
        user_layout.addWidget(user_info)

        # Impersonation badge (no exit button in top bar - use sidebar)
        if getattr(self, 'is_impersonating', False):
            imp_badge = QLabel("🟢 Bölüm Modu")
            imp_badge.setStyleSheet("color: #10b981; font-weight: bold; padding: 6px 10px; border: 1px solid #10b981; border-radius: 8px;")
            layout.addWidget(imp_badge)

        # Logout button
        logout_btn = QPushButton("↪")
        logout_btn.setFixedSize(40, 40)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.handle_logout)
        logout_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 10px;
                color: #ef4444;
                font-size: 18px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.2);
            }
        """)

        layout.addWidget(self.theme_btn)
        layout.addWidget(user_widget)
        layout.addWidget(logout_btn)

        return bar

    def create_sidebar(self):
        """Create sidebar based on user role"""
        sidebar = QFrame()
        sidebar.setFixedWidth(288)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)

        # Menu items based on role and bolum selection
        user_role = self.user_data.get('role', 'Bölüm Koordinatörü')
        is_impersonating = getattr(self, 'is_impersonating', False)
        
        # Check hierarchical data requirements for coordinator
        has_classrooms = self._check_classrooms_exist
        has_courses = self._check_courses_exist
        has_students = self._check_students_exist
        
        if user_role == 'Admin' and not is_impersonating and self.needs_bolum_selection:
            # Admin bölüm seçmemiş - Yönetim paneli
            menu_items = [
                ('🏠', 'Ana Sayfa', 'dashboard'),
                ('👥', 'Kullanıcı Yönetimi', 'users'),
                ('🏢', 'Bölüm Yönetimi', 'bolumler'),
                ('📢', 'Duyuru Yönetimi', 'admin_ayarlar'),
                ('👤', 'Profil Ayarları', 'ayarlar'),
                ('🎓', 'Bölüm Seçimi', 'bolum_secim')
            ]
        elif user_role == 'Admin' and is_impersonating:
            # Admin impersonation modunda - Hiyerarşik kontrol uygula
            if not has_classrooms:
                # Derslik yoksa sadece derslik yönetimi
                menu_items = [
                    ('🏠', 'Ana Sayfa', 'dashboard'),
                    ('⬅️', 'Geri Dön (Admin)', 'exit_imp'),
                    ('', '───────────', 'divider'),
                    ('🏛', 'Derslikler', 'derslikler'),
                    ('⚙', 'Ayarlar', 'ayarlar')
                ]
            elif not has_courses:
                # Derslik var ama ders yoksa - ders yükleme ekle
                menu_items = [
                    ('🏠', 'Ana Sayfa', 'dashboard'),
                    ('⬅️', 'Geri Dön (Admin)', 'exit_imp'),
                    ('', '───────────', 'divider'),
                    ('🏛', 'Derslikler', 'derslikler'),
                    ('📚', 'Ders Listesi', 'dersler'),
                    ('⚙', 'Ayarlar', 'ayarlar')
                ]
            elif not has_students:
                # Ders var ama öğrenci yoksa - öğrenci yükleme ekle
                menu_items = [
                    ('🏠', 'Ana Sayfa', 'dashboard'),
                    ('⬅️', 'Geri Dön (Admin)', 'exit_imp'),
                    ('', '───────────', 'divider'),
                    ('🏛', 'Derslikler', 'derslikler'),
                    ('📚', 'Ders Listesi', 'dersler'),
                    ('👥', 'Öğrenci Listesi', 'ogrenciler'),
                    ('⚙', 'Ayarlar', 'ayarlar')
                ]
            else:
                # Hepsi var - tam menü
                menu_items = [
                    ('🏠', 'Ana Sayfa', 'dashboard'),
                    ('⬅️', 'Geri Dön (Admin)', 'exit_imp'),
                    ('', '───────────', 'divider'),
                    ('🏛', 'Derslikler', 'derslikler'),
                    ('📚', 'Ders Listesi', 'dersler'),
                    ('👥', 'Öğrenci Listesi', 'ogrenciler'),
                    ('📅', 'Sınav Programı', 'sinavlar'),
                ]
                
                # Oturma Planı sadece sınav programı varsa görünsün
                has_exam_programs = self._check_exam_programs_exist
                if has_exam_programs:
                    menu_items.append(('📝', 'Oturma Planı', 'oturma'))
                
                menu_items.append(('⚙', 'Ayarlar', 'ayarlar'))
        else:
            # Bölüm Koordinatörü: Hiyerarşik kontrol uygula
            if not has_classrooms:
                # Derslik yoksa sadece derslik yönetimini göster
                menu_items = [
                    ('🏠', 'Ana Sayfa', 'dashboard'),
                    ('🏛', 'Derslikler', 'derslikler'),
                    ('⚙', 'Ayarlar', 'ayarlar')
                ]
            elif not has_courses:
                # Derslik var ama ders yoksa - ders yükleme ekle
                menu_items = [
                    ('🏠', 'Ana Sayfa', 'dashboard'),
                    ('🏛', 'Derslikler', 'derslikler'),
                    ('📚', 'Ders Listesi', 'dersler'),
                    ('⚙', 'Ayarlar', 'ayarlar')
                ]
            elif not has_students:
                # Ders var ama öğrenci yoksa - öğrenci yükleme ekle
                menu_items = [
                    ('🏠', 'Ana Sayfa', 'dashboard'),
                    ('🏛', 'Derslikler', 'derslikler'),
                    ('📚', 'Ders Listesi', 'dersler'),
                    ('👥', 'Öğrenci Listesi', 'ogrenciler'),
                    ('⚙', 'Ayarlar', 'ayarlar')
                ]
            else:
                # Hepsi var - tam menü
                menu_items = [
                    ('🏠', 'Ana Sayfa', 'dashboard'),
                    ('🏛', 'Derslikler', 'derslikler'),
                    ('📚', 'Ders Listesi', 'dersler'),
                    ('👥', 'Öğrenci Listesi', 'ogrenciler'),
                    ('📅', 'Sınav Programı', 'sinavlar'),
                ]
                
                # Oturma Planı sadece sınav programı varsa görünsün
                has_exam_programs = self._check_exam_programs_exist
                if has_exam_programs:
                    menu_items.append(('📝', 'Oturma Planı', 'oturma'))
                
                menu_items.append(('⚙', 'Ayarlar', 'ayarlar'))

        self.menu_buttons = []
        for icon, text, menu_id in menu_items:
            if menu_id == 'divider':
                # Add divider
                divider = QLabel(text)
                divider.setAlignment(Qt.AlignCenter)
                divider.setStyleSheet(f"color: {self.theme.text_muted}; font-size: 10px; padding: 8px 0;")
                layout.addWidget(divider)
            else:
                btn = MenuButton(text, icon, self.theme)
                # Special action: exit impersonation
                if menu_id == 'exit_imp':
                    btn.clicked.connect(lambda checked=False: self.exit_impersonation())
                else:
                    # Fix lambda capture issue
                    btn.clicked.connect(lambda checked=False, mid=menu_id: self.switch_menu(mid))
                layout.addWidget(btn)
                self.menu_buttons.append((btn, menu_id))

        # Collapse button
        layout.addStretch()

        collapse_btn = QPushButton("◀")
        collapse_btn.setFixedHeight(32)
        collapse_btn.setCursor(Qt.PointingHandCursor)
        collapse_btn.clicked.connect(self.toggle_sidebar)
        layout.addWidget(collapse_btn)

        self.collapse_btn = collapse_btn
        if self.menu_buttons:
            self.menu_buttons[0][0].set_active(True)
        
        # Seçilen bölüm bilgisi (sadece admin için)
        if self.is_admin and self.selected_bolum:
            layout.insertSpacing(0, 8)
            bolum_info = QFrame()
            bolum_info_layout = QVBoxLayout(bolum_info)
            bolum_info_layout.setContentsMargins(12, 12, 12, 12)
            bolum_info_layout.setSpacing(4)
            
            bolum_label = QLabel("Seçili Bölüm:")
            bolum_label.setFont(QFont("Segoe UI", 9))
            bolum_label.setStyleSheet(f"color: {self.theme.text_muted};")
            
            bolum_name = QLabel(self.selected_bolum.get('bolum_adi', ''))
            bolum_name.setFont(QFont("Segoe UI", 10, QFont.Bold))
            bolum_name.setStyleSheet("color: #10b981;")
            bolum_name.setWordWrap(True)
            
            bolum_info_layout.addWidget(bolum_label)
            bolum_info_layout.addWidget(bolum_name)
            
            bolum_info.setStyleSheet("""
                QFrame {
                    background: rgba(16, 185, 129, 0.1);
                    border: 1px solid rgba(16, 185, 129, 0.2);
                    border-radius: 8px;
                }
            """)
            
            layout.insertWidget(0, bolum_info)

        return sidebar

    def create_dashboard_page(self):
        """Dashboard page"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # Welcome card with quick actions
        welcome_card = self.create_welcome_card()
        layout.addWidget(welcome_card)

        # Statistics and recent activity cards
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)
        
        # Stats card (real data, no demo)
        stats_card = self.create_stats_card()
        bottom_row.addWidget(stats_card, 1)
        
        # Recent activity or upcoming exams
        activity_card = self.create_activity_card()
        bottom_row.addWidget(activity_card, 1)
        
        layout.addLayout(bottom_row)

        return content

    def create_welcome_card(self):
        """Welcome card"""
        card = QFrame()

        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        header = QHBoxLayout()

        header_text = QWidget()
        header_layout = QVBoxLayout(header_text)
        header_layout.setSpacing(4)

        title = QLabel(f"Hoş Geldiniz, {self.user_data.get('ad_soyad')} 👋")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))

        subtitle = QLabel("Bugün ne yapmak istersiniz?")
        subtitle.setFont(QFont("Segoe UI", 11))

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        header.addWidget(header_text)
        header.addStretch()

        layout.addLayout(header)

        # Quick actions
        actions_container = QWidget()
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setSpacing(16)

        # Admin: management-oriented quick actions; Coordinator: operational actions
        is_impersonating = getattr(self, 'is_impersonating', False)
        
        if self.is_admin and not is_impersonating:
            # Pure admin mode - management actions
            actions = [
                ("Kullanıcı Ekle", "Yeni yönetici/koordinatör", "👥", "emerald", "users"),
                ("Bölüm Ekle", "Yeni bölüm tanımla", "🏢", "blue", "bolumler"),
                ("Duyuru Yönetimi", "Login ekranı duyurularını yönet", "📢", "orange", "admin_ayarlar"),
                ("Bölüm Seç", "Operasyonel ekrana geç", "🎓", "indigo", "bolum_secim")
            ]
        else:
            # Coordinator mode (or admin in impersonation) - hierarchical shortcuts
            has_classrooms = self._check_classrooms_exist
            has_courses = self._check_courses_exist
            has_students = self._check_students_exist
            
            if not has_classrooms:
                # Derslik yoksa sadece derslik ekleme
                actions = [
                    ("Derslik Ekle", "Önce derslik tanımlayın", "🏛", "emerald", "derslikler")
                ]
            elif not has_courses:
                # Derslik var ama ders yoksa - ders yükleme
                actions = [
                    ("Derslik Yönetimi", "Derslikleri yönetin", "🏛", "blue", "derslikler"),
                    ("Ders Yükle", "Excel'den ders yükleyin", "📚", "emerald", "dersler")
                ]
            elif not has_students:
                # Ders var ama öğrenci yoksa - öğrenci yükleme
                actions = [
                    ("Ders Yönetimi", "Dersleri yönetin", "📚", "blue", "dersler"),
                    ("Öğrenci Yükle", "Excel'den öğrenci yükleyin", "👥", "emerald", "ogrenciler")
                ]
            else:
                # Hepsi var - operasyonel kısayollar
                actions = [
                    ("Derslik Yönetimi", "Derslikleri yönetin", "🏛", "emerald", "derslikler"),
                    ("Sınav Programı", "Sınav takvimi oluşturun", "📅", "indigo", "sinavlar"),
                ]
                
                # Oturma Planı sadece sınav programı varsa görünsün
                has_exam_programs = self._check_exam_programs_exist
                if has_exam_programs:
                    actions.append(("Oturma Planı", "Oturma düzeni yapın", "📝", "orange", "oturma"))

        for label, desc, icon, color, page_id in actions:
            action_card = QuickActionCard(label, desc, icon, color, self.theme)
            action_card.clicked.connect(lambda pid=page_id: self.switch_menu(pid))
            actions_layout.addWidget(action_card)

        layout.addWidget(actions_container)

        return card

    def create_stats_card(self):
        """Statistics card with real data"""
        card = QFrame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("📊 İstatistikler")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)

        # Get real statistics
        stats_list = QWidget()
        stats_layout = QVBoxLayout(stats_list)
        stats_layout.setSpacing(12)

        try:
            from models.database import db
            is_impersonating = getattr(self, 'is_impersonating', False)
            eff_user = self.get_effective_user_data()
            
            if self.is_admin and not is_impersonating:
                # Admin stats
                users_count = db.execute_query("SELECT COUNT(*) AS c FROM users WHERE aktif = TRUE")[0]['c']
                bolum_count = db.execute_query("SELECT COUNT(*) AS c FROM bolumler WHERE aktif = TRUE")[0]['c']
                koor_count = db.execute_query("SELECT COUNT(*) AS c FROM users WHERE aktif = TRUE AND role = 'Bölüm Koordinatörü'")[0]['c']
                
                stats_data = [
                    ("👥 Aktif Kullanıcılar", users_count),
                    ("🏢 Bölümler", bolum_count),
                    ("👨‍🏫 Koordinatörler", koor_count),
                ]
            else:
                # Department stats
                from models.sinav_model import SinavModel
                from models.ders_model import DersModel
                from models.derslik_model import DerslikModel
                from models.ogrenci_model import OgrenciModel
                
                bolum_id = eff_user.get('bolum_id')
                sinav_model = SinavModel(db)
                ders_model = DersModel(db)
                derslik_model = DerslikModel(db)
                ogrenci_model = OgrenciModel(db)
                
                programlar = sinav_model.get_programs_by_bolum(bolum_id)
                program_count = len([p for p in programlar if p.get('aktif', True)])
                ders_count = len(ders_model.get_dersler_by_bolum(bolum_id))
                derslik_count = len(derslik_model.get_derslikler_by_bolum(bolum_id))
                ogrenci_count = len(ogrenci_model.get_ogrenciler_by_bolum(bolum_id))
                
                stats_data = [
                    ("📅 Sınav Programları", program_count),
                    ("📚 Dersler", ders_count),
                    ("🏛 Derslikler", derslik_count),
                    ("👨‍🎓 Öğrenciler", ogrenci_count),
                ]
        except Exception as e:
            logger.error(f"Stats error: {e}")
            stats_data = [("⚠️ Veri yüklenemedi", 0)]

        for label, value in stats_data:
            item = QWidget()
            item_layout = QHBoxLayout(item)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(12)

            lbl = QLabel(label)
            lbl.setFont(QFont("Segoe UI", 11))
            item_layout.addWidget(lbl)
            
            item_layout.addStretch()

            val = QLabel(str(value))
            val.setFont(QFont("Segoe UI", 14, QFont.Bold))
            val.setStyleSheet("color: #10b981;")
            item_layout.addWidget(val)

            stats_layout.addWidget(item)

        layout.addWidget(stats_list)
        layout.addStretch()

        return card
    
    def create_activity_card(self):
        """Recent activity or upcoming events card"""
        card = QFrame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("📌 Son Aktiviteler")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)

        # Activity list
        activity_list = QWidget()
        activity_layout = QVBoxLayout(activity_list)
        activity_layout.setSpacing(12)

        try:
            from models.database import db
            is_impersonating = getattr(self, 'is_impersonating', False)
            eff_user = self.get_effective_user_data()
            
            if self.is_admin and not is_impersonating:
                # Admin: show recent system activities
                recent_users = db.execute_query("""
                    SELECT ad_soyad, son_giris 
                    FROM users 
                    WHERE aktif = TRUE AND son_giris IS NOT NULL
                    ORDER BY son_giris DESC 
                    LIMIT 5
                """)
                
                if recent_users:
                    for user in recent_users:
                        activity_item = QLabel(f"• {user['ad_soyad']} - Son giriş")
                        activity_item.setFont(QFont("Segoe UI", 10))
                        activity_layout.addWidget(activity_item)
                else:
                    no_data = QLabel("Henüz aktivite yok")
                    no_data.setFont(QFont("Segoe UI", 10))
                    no_data.setStyleSheet("color: #9ca3af;")
                    activity_layout.addWidget(no_data)
            else:
                # Department: show recent exam programs
                from models.sinav_model import SinavModel
                bolum_id = eff_user.get('bolum_id')
                sinav_model = SinavModel(db)
                programlar = sinav_model.get_programs_by_bolum(bolum_id)
                
                if programlar:
                    for prog in programlar[:5]:
                        prog_item = QLabel(f"• {prog.get('program_adi', 'Program')}")
                        prog_item.setFont(QFont("Segoe UI", 10))
                        activity_layout.addWidget(prog_item)
                else:
                    no_data = QLabel("Henüz sınav programı yok")
                    no_data.setFont(QFont("Segoe UI", 10))
                    no_data.setStyleSheet("color: #9ca3af;")
                    activity_layout.addWidget(no_data)
        except Exception as e:
            logger.error(f"Activity error: {e}")
            error_label = QLabel("⚠️ Veri yüklenemedi")
            error_label.setFont(QFont("Segoe UI", 10))
            activity_layout.addWidget(error_label)

        layout.addWidget(activity_list)
        layout.addStretch()

        return card

    def toggle_theme(self):
        """Toggle theme"""
        self.theme.dark_mode = not self.theme.dark_mode
        self.theme_btn.setText("☀" if self.theme.dark_mode else "🌙")
        self.apply_styles()
        for btn, _ in self.menu_buttons:
            btn.theme = self.theme
            btn.update_style()

    def toggle_sidebar(self):
        """Toggle sidebar"""
        self.sidebar_collapsed = not self.sidebar_collapsed

        if self.sidebar_collapsed:
            self.sidebar.setFixedWidth(80)
            self.collapse_btn.setText("▶")
        else:
            self.sidebar.setFixedWidth(288)
            self.collapse_btn.setText("◀")

        for btn, _ in self.menu_buttons:
            btn.set_collapsed(self.sidebar_collapsed)

    def switch_menu(self, menu_id):
        """Switch menu and go to page"""
        self.active_menu = menu_id

        for btn, mid in self.menu_buttons:
            btn.set_active(mid == menu_id)

        # Page transition
        self.show_page(menu_id)

    def show_page(self, page_id):
        """Show page (animated transition)"""
        # If page not in cache, create it
        if page_id not in self.pages:
            try:
                logger.info(f"Creating page: {page_id}")
                page_widget = self.create_page(page_id)
                if page_widget:
                    self.content_stack.addWidget(page_widget)
                    self.pages[page_id] = page_widget
                    logger.info(f"Page created successfully: {page_id}")
                else:
                    logger.warning(f"Page widget is None for: {page_id}")
                    return
            except Exception as e:
                logger.error(f"Error creating page {page_id}: {e}", exc_info=True)
                ModernMessageBox.error(
                    self, "Sayfa Yükleme Hatası", "'{page_id}' sayfası yüklenirken oluştu", f"\n{str(e)}"
                )
                return

        # Switch to page
        if page_id in self.pages:
            target_page = self.pages[page_id]
            self.content_stack.setCurrentWidget(target_page)
            logger.info(f"✅ Switched to page: {page_id}")
        else:
            logger.error(f"Page {page_id} not found in pages dict")

    def on_bolum_selected(self, bolum_data):
        """Handle department selection"""
        logger.info(f"✅ Department selected: {bolum_data['bolum_adi']}")
        
        # Update selected bolum
        self.selected_bolum = bolum_data
        
        # Update user_data with bolum_id
        self.user_data['bolum_id'] = bolum_data['bolum_id']
        
        # Enter impersonation as coordinator for selected department
        if not getattr(self, 'is_impersonating', False):
            import copy
            self._original_user_data = copy.deepcopy(self.user_data)
        self.is_impersonating = True
        
        # Use real coordinator data from bolum_data
        koordinatorler = bolum_data.get('koordinatorler', [])
        if koordinatorler:
            # Use first coordinator's data
            first_koor = koordinatorler[0]
            self.impersonated_user_data = {
                'user_id': first_koor.get('user_id'),
                'email': first_koor.get('email', ''),
                'role': 'Bölüm Koordinatörü',
                'ad_soyad': first_koor.get('ad_soyad', ''),
                'bolum_id': bolum_data.get('bolum_id')
            }
        else:
            # Fallback to synthetic data
            self.impersonated_user_data = {
                'user_id': None,
                'email': '',
                'role': 'Bölüm Koordinatörü',
                'ad_soyad': f"{bolum_data.get('bolum_adi', 'Bölüm')} Koordinatörü",
                'bolum_id': bolum_data.get('bolum_id')
            }

        # No longer needs bolum selection
        self.needs_bolum_selection = False
        
        # Clear pages cache (except bolum_secim)
        pages_to_remove = [k for k in self.pages.keys() if k != 'bolum_secim']
        for page_id in pages_to_remove:
            if page_id in self.pages:
                widget = self.pages[page_id]
                self.content_stack.removeWidget(widget)
                widget.deleteLater()
                del self.pages[page_id]
        
        # Create dashboard
        self.dashboard_page = self.create_dashboard_page()
        self.content_stack.addWidget(self.dashboard_page)
        self.pages['dashboard'] = self.dashboard_page
        
        # Recreate sidebar with new menu
        self.recreate_sidebar()
        
        # Switch to dashboard
        self.switch_menu('dashboard')
        
        logger.info("✅ UI updated with department context")

        # Refresh top bar to reflect impersonation
        self.refresh_top_bar()

    def exit_impersonation(self):
        """Exit impersonation and restore admin context"""
        if not getattr(self, 'is_impersonating', False):
            return
        
        # Restore original admin data
        if hasattr(self, '_original_user_data') and self._original_user_data:
            self.user_data = self._original_user_data.copy()
        
        self.is_impersonating = False
        self.impersonated_user_data = None
        
        # Clear selected bolum context
        self.selected_bolum = None
        
        # Admin should return to needs_bolum_selection state if they don't have a permanent bolum_id
        # Remove temporary bolum_id from user_data if it was added during impersonation
        if self.user_data.get('role') == 'Admin':
            # Admin typically doesn't have a bolum_id, so remove it
            if 'bolum_id' in self.user_data:
                del self.user_data['bolum_id']
            self.needs_bolum_selection = True

        # Reset pages and sidebar
        for page_id, widget in list(self.pages.items()):
            self.content_stack.removeWidget(widget)
            widget.deleteLater()
        self.pages.clear()

        # Recreate dashboard and sidebar
        self.dashboard_page = self.create_dashboard_page()
        self.content_stack.addWidget(self.dashboard_page)
        self.pages['dashboard'] = self.dashboard_page
        self.recreate_sidebar()
        self.switch_menu('dashboard')

        # Refresh top bar back to admin
        self.refresh_top_bar()
        
        logger.info("✅ Exited impersonation, returned to admin mode")

    def start_impersonation(self, target_user: dict):
        """Start impersonation for a specific user (from Users page)."""
        import copy
        if not getattr(self, 'is_impersonating', False):
            self._original_user_data = copy.deepcopy(self.user_data)
        self.is_impersonating = True
        self.impersonated_user_data = copy.deepcopy(target_user)
        # Ensure coordinator role menus
        self.selected_bolum = {'bolum_id': target_user.get('bolum_id'), 'bolum_adi': ''}
        # Reset pages and sidebar
        for page_id, widget in list(self.pages.items()):
            self.content_stack.removeWidget(widget)
            widget.deleteLater()
        self.pages.clear()
        self.dashboard_page = self.create_dashboard_page()
        self.content_stack.addWidget(self.dashboard_page)
        self.pages['dashboard'] = self.dashboard_page
        self.recreate_sidebar()
        self.switch_menu('dashboard')
        # Refresh top bar
        self.refresh_top_bar()
    
    def recreate_sidebar(self):
        """Recreate sidebar with updated menu"""
        # Remove old sidebar
        old_sidebar = self.sidebar
        content = self.centralWidget().layout().itemAt(1).widget()
        content_layout = content.layout()
        content_layout.removeWidget(old_sidebar)
        old_sidebar.deleteLater()
        
        # Create new sidebar
        self.sidebar = self.create_sidebar()
        content_layout.insertWidget(0, self.sidebar)
    
    def refresh_ui_for_data_change(self):
        """Refresh UI after data changes (classroom/course/student added)"""
        # Recreate sidebar to update menu items based on new data
        self.recreate_sidebar()
        
        # Refresh dashboard if it's the current page
        if self.active_menu == 'dashboard':
            # Remove old dashboard
            if 'dashboard' in self.pages:
                old_dashboard = self.pages['dashboard']
                self.content_stack.removeWidget(old_dashboard)
                old_dashboard.deleteLater()
                del self.pages['dashboard']
            
            # Create new dashboard
            self.dashboard_page = self.create_dashboard_page()
            self.content_stack.addWidget(self.dashboard_page)
            self.pages['dashboard'] = self.dashboard_page
            self.content_stack.setCurrentWidget(self.dashboard_page)

    def refresh_top_bar(self):
        """Recreate top bar to reflect impersonation state and user info"""
        if hasattr(self, 'top_bar') and self.top_bar:
            self.main_layout.removeWidget(self.top_bar)
            self.top_bar.deleteLater()
        self.top_bar = self.create_top_bar()
        self.main_layout.insertWidget(0, self.top_bar)
    
    def create_page(self, page_id):
        """Create page widget based on role and page_id"""
        user_role = self.user_data.get('role', 'Bölüm Koordinatörü')
        
        # Dashboard is pre-created (if exists)
        if page_id == 'dashboard':
            if hasattr(self, 'dashboard_page') and self.dashboard_page:
                return self.dashboard_page
            else:
                # Create dashboard if not exists
                self.dashboard_page = self.create_dashboard_page()
                return self.dashboard_page
        
        # Bölüm seçim sayfası - always recreate to get fresh data
        if page_id == 'bolum_secim':
            # Remove old instance if exists
            if 'bolum_secim' in self.pages:
                old_widget = self.pages['bolum_secim']
                self.content_stack.removeWidget(old_widget)
                old_widget.deleteLater()
                del self.pages['bolum_secim']
            
            bolum_secim = BolumSecimView(self.user_data)
            bolum_secim.bolum_selected.connect(self.on_bolum_selected)
            return bolum_secim
        
        # Create page based on role
        try:
            # Get effective user for all pages
            eff_user = self.get_effective_user_data()
            
            # Admin-only pages
            if user_role == 'Admin' and not self.is_impersonating:
                if page_id == 'users':
                    return KullaniciYonetimiView(self.user_data)
                elif page_id == 'bolumler':
                    return self.create_bolum_yonetimi_page()
                elif page_id == 'admin_ayarlar':
                    return DuyuruYonetimiView(self.user_data)
                elif page_id == 'ayarlar':
                    # Admin's own profile settings
                    return AyarlarView(self.user_data)
            
            # Shared pages (both admin in impersonation mode and coordinator)
            if page_id == 'derslikler':
                return DerslikView(eff_user)
            elif page_id == 'dersler':
                return DersYukleView(eff_user)
            elif page_id == 'ogrenciler':
                return OgrenciYukleView(eff_user)
            elif page_id == 'sinavlar':
                return SinavOlusturView(eff_user)
            elif page_id == 'oturma':
                return OturmaPlaniView(eff_user)
            elif page_id == 'ayarlar':
                # Coordinator or impersonated user settings
                return AyarlarView(eff_user)
            
            logger.warning(f"Unknown page_id: {page_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error creating page {page_id}: {e}", exc_info=True)
            raise
    
    @property
    def _check_classrooms_exist(self) -> bool:
        """Check if classrooms exist for current user/bolum"""
        try:
            from models.database import db
            from models.derslik_model import DerslikModel
            
            # Get effective user (handle impersonation)
            eff_user = self.get_effective_user_data()
            eff_bolum_id = eff_user.get('bolum_id')
            
            if not eff_bolum_id:
                return True  # Admin without bolum - allow all
            
            derslik_model = DerslikModel(db)
            derslikler = derslik_model.get_derslikler_by_bolum(eff_bolum_id)
            return len(derslikler) > 0
            
        except Exception as e:
            logger.error(f"Error checking classrooms: {e}", exc_info=True)
            return True  # On error, don't block
    
    @property
    def _check_courses_exist(self) -> bool:
        """Check if courses exist for current user/bolum"""
        try:
            from models.database import db
            from models.ders_model import DersModel
            
            # Get effective user (handle impersonation)
            eff_user = self.get_effective_user_data()
            eff_bolum_id = eff_user.get('bolum_id')
            
            if not eff_bolum_id:
                return True  # Admin without bolum - allow all
            
            ders_model = DersModel(db)
            dersler = ders_model.get_dersler_by_bolum(eff_bolum_id)
            return len(dersler) > 0
            
        except Exception as e:
            logger.error(f"Error checking courses: {e}", exc_info=True)
            return True  # On error, don't block
    
    @property
    def _check_exam_programs_exist(self) -> bool:
        """Check if exam programs exist for current user/bolum"""
        try:
            from models.database import db
            from models.sinav_model import SinavModel
            
            # Get effective user (handle impersonation)
            eff_user = self.get_effective_user_data()
            eff_bolum_id = eff_user.get('bolum_id')
            
            if not eff_bolum_id:
                return True  # Admin without bolum - allow all
            
            sinav_model = SinavModel(db)
            programs = sinav_model.get_programs_by_bolum(eff_bolum_id)
            return len(programs) > 0
            
        except Exception as e:
            logger.error(f"Error checking exam programs: {e}", exc_info=True)
            return False  # On error, hide oturma menu
    
    @property
    def _check_students_exist(self) -> bool:
        """Check if students exist for current user/bolum"""
        try:
            from models.database import db
            from models.ogrenci_model import OgrenciModel
            
            # Get effective user (handle impersonation)
            eff_user = self.get_effective_user_data()
            eff_bolum_id = eff_user.get('bolum_id')
            
            if not eff_bolum_id:
                return True  # Admin without bolum - allow all
            
            ogrenci_model = OgrenciModel(db)
            ogrenciler = ogrenci_model.get_ogrenciler_by_bolum(eff_bolum_id)
            return len(ogrenciler) > 0
            
        except Exception as e:
            logger.error(f"Error checking students: {e}", exc_info=True)
            return True  # On error, don't block
    
    def create_bolum_yonetimi_page(self):
        """Create department management page"""
        return BolumYonetimiView(self.user_data)
    
    

    def animate_page_transition(self, target_widget):
        """Page transition animation"""
        # Fade in effect
        effect = QGraphicsOpacityEffect(target_widget)
        target_widget.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(300)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start(QPropertyAnimation.DeleteWhenStopped)

    def handle_logout(self):
        """Logout"""
        # Emit signal - main.py will handle
        self.logout_requested.emit()

    def apply_styles(self):
        """Apply styles"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {self.theme.bg};
            }}
            QFrame {{
                background: {self.theme.card};
                border: 1px solid {self.theme.border};
                border-radius: 16px;
            }}
            QLabel {{
                color: {self.theme.text};
                background: transparent;
                border: none;
            }}
            QPushButton {{
                background: {self.theme.card};
                border: 1px solid {self.theme.border};
                border-radius: 10px;
                color: {self.theme.text};
            }}
            QPushButton:hover {{
                background: {self.theme.hover};
            }}
        """)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    app = QApplication(sys.argv)

    user_data = {
        'user_id': 1,
        'email': 'admin@kocaeli.edu.tr',
        'role': 'Admin',
        'ad_soyad': 'Admin User',
        'bolum_id': 1
    }

    window = MainWindow(user_data)
    window.show()

    sys.exit(app.exec())
