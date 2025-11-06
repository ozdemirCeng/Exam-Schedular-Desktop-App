"""
Bolum Secim View - Department Selection
Admin kullanicilari icin bolum secim ekrani
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from models.database import db
from models.bolum_model import BolumModel
from utils.modern_dialogs import ModernMessageBox
from styles.kou_theme import KOUTheme  # Modern KOÜ yeşil tema

logger = logging.getLogger(__name__)


class BolumCard(QFrame):
    """Department selection card"""
    
    clicked = Signal(dict)
    
    def __init__(self, bolum_data, parent=None):
        super().__init__(parent)
        self.bolum_data = bolum_data
        self.setCursor(Qt.PointingHandCursor)
        
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        
        # Icon
        icon = QLabel("🎓")
        icon.setFont(QFont("Segoe UI Emoji", 48))
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        # Department code
        kod = QLabel(self.bolum_data.get('bolum_kodu', ''))
        kod.setFont(QFont("Segoe UI", 14, QFont.Bold))
        kod.setAlignment(Qt.AlignCenter)
        kod.setStyleSheet("color: #10b981;")
        layout.addWidget(kod)
        
        # Department name
        ad = QLabel(self.bolum_data.get('bolum_adi', ''))
        ad.setFont(QFont("Segoe UI", 12))
        ad.setAlignment(Qt.AlignCenter)
        ad.setWordWrap(True)
        ad.setStyleSheet("color: #64748b;")
        layout.addWidget(ad)
        
        # Coordinator info
        koordinatorler = self.bolum_data.get('koordinatorler', [])
        if koordinatorler:
            koor_label = QLabel(f"👤 {koordinatorler[0]['ad_soyad']}")
            koor_label.setFont(QFont("Segoe UI", 9))
            koor_label.setAlignment(Qt.AlignCenter)
            koor_label.setStyleSheet("color: #94a3b8; padding: 4px;")
            layout.addWidget(koor_label)
            
            if len(koordinatorler) > 1:
                extra = QLabel(f"+{len(koordinatorler)-1} daha")
                extra.setFont(QFont("Segoe UI", 8))
                extra.setAlignment(Qt.AlignCenter)
                extra.setStyleSheet("color: #cbd5e1;")
                layout.addWidget(extra)
        
        # Select button
        btn = QPushButton("Seç")
        btn.setObjectName("primaryBtn")
        btn.setFixedHeight(36)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self.clicked.emit(self.bolum_data))
        layout.addWidget(btn)
    
    def apply_styles(self):
        """Apply modern KOÜ theme styles"""
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 2px solid {KOUTheme.BORDER_LIGHT};
                border-radius: 16px;
            }}
            QFrame:hover {{
                background: {KOUTheme.PRIMARY_LIGHTER};
                border-color: {KOUTheme.PRIMARY};
            }}
            QPushButton#primaryBtn {{
                background: {KOUTheme.PRIMARY};
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: 600;
                font-size: 13px;
                padding: 10px 20px;
            }}
            QPushButton#primaryBtn:hover {{
                background: {KOUTheme.PRIMARY_DARK};
            }}
            QPushButton#primaryBtn:pressed {{
                background: {KOUTheme.PRIMARY_DARK};
                padding: 11px 19px 9px 21px;
            }}
        """)


class BolumSecimView(QWidget):
    """Department selection view for Admin users"""
    
    bolum_selected = Signal(dict)
    
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.bolum_model = BolumModel(db)
        
        self.setup_ui()
        self.load_bolumler()
    
    def setup_ui(self):
        """Setup modern KOÜ themed UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Modern gradient header with KOÜ green
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {KOUTheme.PRIMARY}, stop:1 {KOUTheme.PRIMARY_DARK});
                border: none;
            }}
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(48, 48, 48, 48)
        header_layout.setSpacing(12)
        
        title = QLabel("🎓 Bölüm Seçimi")
        title.setFont(QFont("Segoe UI", 32, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel(
            "Lütfen çalışmak istediğiniz bölümü seçiniz.\n"
            "Seçtiğiniz bölüm için ders, öğrenci ve sınav yönetimi yapabileceksiniz."
        )
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.95); background: transparent;")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
        
        # Content area with modern styling
        content = QWidget()
        content.setStyleSheet(f"""
            QWidget {{
                background: {KOUTheme.BG_LIGHT};
                border: none;
            }}
        """)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(48, 48, 48, 48)
        
        # Scroll area for departments
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(KOUTheme.scroll_area())
        
        self.bolum_container = QWidget()
        self.bolum_container.setStyleSheet("QWidget { border: none; background: transparent; }")
        self.bolum_layout = QHBoxLayout(self.bolum_container)
        self.bolum_layout.setSpacing(24)
        self.bolum_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(self.bolum_container)
        content_layout.addWidget(scroll)
        
        layout.addWidget(content, 1)
    
    def load_bolumler(self):
        """Load departments with assigned coordinators only"""
        try:
            # Get departments with assigned coordinators only
            query = """
                SELECT b.bolum_id, b.bolum_kodu, b.bolum_adi,
                       u.user_id, u.ad_soyad, u.email
                FROM bolumler b
                INNER JOIN users u ON b.bolum_id = u.bolum_id
                  AND u.aktif = TRUE 
                  AND u.role = 'Bölüm Koordinatörü'
                WHERE b.aktif = TRUE 
                ORDER BY b.bolum_adi
            """
            results = db.execute_query(query)
            
            if not results:
                self.show_no_departments()
                return
            
            # Group by department (in case multiple coordinators per department)
            bolumler_dict = {}
            for row in results:
                bolum_id = row['bolum_id']
                if bolum_id not in bolumler_dict:
                    bolumler_dict[bolum_id] = {
                        'bolum_id': row['bolum_id'],
                        'bolum_kodu': row['bolum_kodu'],
                        'bolum_adi': row['bolum_adi'],
                        'koordinatorler': []
                    }
                bolumler_dict[bolum_id]['koordinatorler'].append({
                    'user_id': row['user_id'],
                    'ad_soyad': row['ad_soyad'],
                    'email': row['email']
                })
            
            bolumler = list(bolumler_dict.values())
            
            # Clear existing
            while self.bolum_layout.count():
                item = self.bolum_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Add department cards
            self.bolum_layout.addStretch()
            for bolum in bolumler:
                card = BolumCard(bolum)
                card.clicked.connect(self.on_bolum_selected)
                card.setFixedWidth(280)
                card.setFixedHeight(320)
                self.bolum_layout.addWidget(card)
            self.bolum_layout.addStretch()
            
            logger.info(f"Loaded {len(bolumler)} departments with coordinators")
            
        except Exception as e:
            logger.error(f"Error loading departments: {e}")
            ModernMessageBox.error(
                self,
                "Yükleme Hatası",
                "Bölümler yüklenirken bir hata oluştu.",
                f"Hata detayı:\n{str(e)}"
            )
    
    def show_no_departments(self):
        """Show message when no departments available"""
        self.bolum_layout.addStretch()
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(16)
        
        icon = QLabel("⚠️")
        icon.setFont(QFont("Segoe UI Emoji", 48))
        icon.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(icon)
        
        msg = QLabel("Koordinatörü Atanmış Bölüm Bulunamadı")
        msg.setFont(QFont("Segoe UI", 16, QFont.Bold))
        msg.setStyleSheet("color: #6b7280;")
        msg.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(msg)
        
        info = QLabel(
            "Bölüm seçebilmek için önce Kullanıcı Yönetimi'nden\n"
            "bir koordinatör oluşturup bölüm ataması yapmalısınız."
        )
        info.setFont(QFont("Segoe UI", 12))
        info.setStyleSheet("color: #9ca3af;")
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        container_layout.addWidget(info)
        
        self.bolum_layout.addWidget(container)
        self.bolum_layout.addStretch()
    
    def on_bolum_selected(self, bolum_data):
        """Handle department selection"""
        logger.info(f"Department selected: {bolum_data['bolum_adi']}")
        
        # Get coordinator info
        koordinatorler = bolum_data.get('koordinatorler', [])
        koor_info = ""
        if koordinatorler:
            if len(koordinatorler) == 1:
                koor_info = f"\n\nKoordinatör: {koordinatorler[0]['ad_soyad']}"
            else:
                koor_names = ", ".join([k['ad_soyad'] for k in koordinatorler])
                koor_info = f"\n\nKoordinatörler: {koor_names}"
        
        # Directly emit selection (no confirmation needed)
        self.bolum_selected.emit(bolum_data)

