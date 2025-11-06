"""
Kocaeli Üniversitesi Modern Yeşil Tema
Profesyonel ve tutarlı UI bileşenleri
"""

class KOUTheme:
    """Kocaeli Üniversitesi Tema Renkleri ve Stilleri"""
    
    # Ana renkler
    PRIMARY = "#00A651"  # KOÜ Yeşili
    PRIMARY_DARK = "#008741"
    PRIMARY_LIGHT = "#33B870"
    PRIMARY_LIGHTER = "#E6F7EF"
    
    SECONDARY = "#1e293b"  # Koyu gri (başlıklar)
    SECONDARY_LIGHT = "#475569"
    
    # Arka plan renkleri
    BG_WHITE = "#ffffff"
    BG_LIGHT = "#f8fafc"
    BG_LIGHTER = "#f1f5f9"
    
    # Border renkleri
    BORDER_LIGHT = "#e2e8f0"
    BORDER_MEDIUM = "#cbd5e1"
    
    # Text renkleri
    TEXT_PRIMARY = "#1e293b"
    TEXT_SECONDARY = "#64748b"
    TEXT_MUTED = "#94a3b8"
    
    # Status renkleri
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"
    INFO = "#3b82f6"
    
    # Shadow
    SHADOW = "0 2px 4px rgba(0, 0, 0, 0.06)"
    SHADOW_MEDIUM = "0 4px 6px rgba(0, 0, 0, 0.1)"
    SHADOW_LARGE = "0 10px 15px rgba(0, 0, 0, 0.1)"
    
    @staticmethod
    def button_primary():
        """Ana yeşil buton stili"""
        return f"""
            QPushButton {{
                background: {KOUTheme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 600;
                min-height: 42px;
            }}
            QPushButton:hover {{
                background: {KOUTheme.PRIMARY_DARK};
            }}
            QPushButton:pressed {{
                background: {KOUTheme.PRIMARY_DARK};
                padding: 13px 23px 11px 25px;
            }}
            QPushButton:disabled {{
                background: {KOUTheme.BORDER_MEDIUM};
                color: {KOUTheme.TEXT_MUTED};
            }}
        """
    
    @staticmethod
    def button_secondary():
        """İkincil buton stili"""
        return f"""
            QPushButton {{
                background: white;
                color: {KOUTheme.PRIMARY};
                border: 2px solid {KOUTheme.PRIMARY};
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 600;
                min-height: 42px;
            }}
            QPushButton:hover {{
                background: {KOUTheme.PRIMARY_LIGHTER};
            }}
            QPushButton:pressed {{
                background: {KOUTheme.PRIMARY_LIGHTER};
                padding: 13px 23px 11px 25px;
            }}
            QPushButton:disabled {{
                border-color: {KOUTheme.BORDER_MEDIUM};
                color: {KOUTheme.TEXT_MUTED};
            }}
        """
    
    @staticmethod
    def button_ghost():
        """Ghost buton stili (sadece icon/text için)"""
        return f"""
            QPushButton {{
                background: transparent;
                color: {KOUTheme.TEXT_SECONDARY};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {KOUTheme.BG_LIGHTER};
                color: {KOUTheme.PRIMARY};
            }}
            QPushButton:pressed {{
                background: {KOUTheme.PRIMARY_LIGHTER};
            }}
        """
    
    @staticmethod
    def button_danger():
        """Silme butonu stili"""
        return f"""
            QPushButton {{
                background: white;
                color: {KOUTheme.ERROR};
                border: 2px solid {KOUTheme.ERROR};
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {KOUTheme.ERROR};
                color: white;
            }}
            QPushButton:pressed {{
                background: #dc2626;
            }}
        """
    
    @staticmethod
    def card():
        """Card container stili"""
        return f"""
            QFrame {{
                background: white;
                border: 1px solid {KOUTheme.BORDER_LIGHT};
                border-radius: 12px;
                padding: 20px;
            }}
        """
    
    @staticmethod
    def toolbar():
        """Toolbar stili"""
        return f"""
            QFrame {{
                background: {KOUTheme.BG_LIGHT};
                border-radius: 8px;
                padding: 12px;
            }}
        """
    
    @staticmethod
    def input_field():
        """Input field stili (QLineEdit, QSpinBox, QComboBox)"""
        return f"""
            QLineEdit, QSpinBox, QComboBox, QDateTimeEdit {{
                background: white;
                border: 2px solid {KOUTheme.BORDER_LIGHT};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                color: {KOUTheme.TEXT_PRIMARY};
                min-height: 42px;
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QDateTimeEdit:focus {{
                border-color: {KOUTheme.PRIMARY};
                background: white;
            }}
            QLineEdit:hover, QSpinBox:hover, QComboBox:hover, QDateTimeEdit:hover {{
                border-color: {KOUTheme.PRIMARY_LIGHT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {KOUTheme.TEXT_SECONDARY};
                margin-right: 8px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background: {KOUTheme.BG_LIGHT};
                border: none;
                width: 20px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background: {KOUTheme.PRIMARY_LIGHTER};
            }}
        """
    
    @staticmethod
    def checkbox():
        """Checkbox stili"""
        return f"""
            QCheckBox {{
                color: {KOUTheme.TEXT_PRIMARY};
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {KOUTheme.BORDER_MEDIUM};
                border-radius: 4px;
                background: white;
            }}
            QCheckBox::indicator:hover {{
                border-color: {KOUTheme.PRIMARY};
            }}
            QCheckBox::indicator:checked {{
                background: {KOUTheme.PRIMARY};
                border-color: {KOUTheme.PRIMARY};
                image: none;
            }}
            QCheckBox::indicator:checked::after {{
                content: "✓";
                color: white;
            }}
        """
    
    @staticmethod
    def table():
        """Table stili"""
        return f"""
            QTableWidget {{
                background: white;
                border: 1px solid {KOUTheme.BORDER_LIGHT};
                border-radius: 8px;
                gridline-color: {KOUTheme.BG_LIGHTER};
                selection-background-color: {KOUTheme.PRIMARY_LIGHTER};
            }}
            QTableWidget::item {{
                padding: 8px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background: {KOUTheme.PRIMARY_LIGHTER};
                color: {KOUTheme.PRIMARY_DARK};
            }}
            QHeaderView::section {{
                background: {KOUTheme.BG_LIGHT};
                color: {KOUTheme.TEXT_PRIMARY};
                padding: 12px;
                border: none;
                border-bottom: 2px solid {KOUTheme.PRIMARY};
                font-weight: 600;
                font-size: 13px;
            }}
            QHeaderView::section:hover {{
                background: {KOUTheme.PRIMARY_LIGHTER};
            }}
        """
    
    @staticmethod
    def tab_widget():
        """Tab widget stili"""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {KOUTheme.BORDER_LIGHT};
                background: white;
                border-radius: 8px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: {KOUTheme.BG_LIGHT};
                color: {KOUTheme.TEXT_SECONDARY};
                padding: 12px 24px;
                margin-right: 2px;
                border: 1px solid {KOUTheme.BORDER_LIGHT};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }}
            QTabBar::tab:hover {{
                color: {KOUTheme.PRIMARY};
                background: {KOUTheme.PRIMARY_LIGHTER};
            }}
            QTabBar::tab:selected {{
                color: {KOUTheme.PRIMARY};
                background: white;
                border-bottom: 2px solid white;
            }}
        """
    
    @staticmethod
    def progress_bar():
        """Progress bar stili"""
        return f"""
            QProgressBar {{
                background: {KOUTheme.BG_LIGHT};
                border: none;
                border-radius: 8px;
                height: 12px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {KOUTheme.PRIMARY}, stop:1 {KOUTheme.PRIMARY_LIGHT});
                border-radius: 8px;
            }}
        """
    
    @staticmethod
    def scroll_area():
        """Scroll area stili"""
        return f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {KOUTheme.BG_LIGHT};
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {KOUTheme.BORDER_MEDIUM};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {KOUTheme.PRIMARY_LIGHT};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """
    
    @staticmethod
    def group_box():
        """Group box stili"""
        return f"""
            QGroupBox {{
                background: white;
                border: 2px solid {KOUTheme.BORDER_LIGHT};
                border-radius: 10px;
                margin-top: 12px;
                padding: 20px 16px 16px 16px;
                font-weight: 600;
                font-size: 14px;
                color: {KOUTheme.PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: {KOUTheme.PRIMARY};
            }}
        """
    
    @staticmethod
    def header_label():
        """Header label stili"""
        return f"""
            QLabel {{
                color: {KOUTheme.SECONDARY};
                font-size: 24px;
                font-weight: 700;
                padding: 0 0 10px 0;
            }}
        """
    
    @staticmethod
    def info_label():
        """Info label stili"""
        return f"""
            QLabel {{
                color: {KOUTheme.TEXT_SECONDARY};
                font-size: 13px;
                font-weight: 500;
            }}
        """
