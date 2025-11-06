"""
Professional Theme System for Kocaeli Üniversitesi Sınav Takvimi Sistemi
Consistent, modern design language across the application
"""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt


class KocaeliTheme:
    """
    Kocaeli Üniversitesi tema renkleri ve stilleri
    """
    
    # Primary Brand Colors
    PRIMARY = "#00A651"  # Kocaeli green
    PRIMARY_DARK = "#008F47"
    PRIMARY_LIGHT = "#00C75F"
    
    # Secondary Colors
    SECONDARY = "#1e293b"
    SECONDARY_LIGHT = "#334155"
    
    # Neutral Colors
    WHITE = "#ffffff"
    BLACK = "#000000"
    GRAY_50 = "#f9fafb"
    GRAY_100 = "#f3f4f6"
    GRAY_200 = "#e5e7eb"
    GRAY_300 = "#d1d5db"
    GRAY_400 = "#9ca3af"
    GRAY_500 = "#6b7280"
    GRAY_600 = "#4b5563"
    GRAY_700 = "#374151"
    GRAY_800 = "#1f2937"
    GRAY_900 = "#111827"
    
    # Semantic Colors
    SUCCESS = "#10b981"
    SUCCESS_BG = "#ecfdf5"
    WARNING = "#f59e0b"
    WARNING_BG = "#fffbeb"
    ERROR = "#ef4444"
    ERROR_BG = "#fef2f2"
    INFO = "#3b82f6"
    INFO_BG = "#eff6ff"
    
    # UI Element Colors
    BORDER = "#e2e8f0"
    BORDER_FOCUS = PRIMARY
    CARD_BG = WHITE
    SIDEBAR_BG = WHITE
    HOVER_BG = "#f1f5f9"
    
    @staticmethod
    def get_main_stylesheet(dark_mode=False):
        """
        Ana uygulama için stylesheet döndür
        """
        if dark_mode:
            return KocaeliTheme._dark_stylesheet()
        return KocaeliTheme._light_stylesheet()
    
    @staticmethod
    def _light_stylesheet():
        """Light mode stylesheet"""
        return f"""
            /* ============================================================
               GLOBAL STYLES
            ============================================================ */
            * {{
                font-family: 'Segoe UI', 'San Francisco', 'Helvetica Neue', Arial, sans-serif;
                outline: none;
            }}
            
            QMainWindow {{
                background: {KocaeliTheme.GRAY_50};
            }}
            
            QWidget {{
                background: transparent;
                color: {KocaeliTheme.GRAY_900};
            }}
            
            /* ============================================================
               CARDS & FRAMES
            ============================================================ */
            QFrame {{
                background: {KocaeliTheme.WHITE};
                border: 1px solid {KocaeliTheme.BORDER};
                border-radius: 12px;
            }}
            
            QFrame:hover {{
                border: 1px solid {KocaeliTheme.PRIMARY};
            }}
            
            /* ============================================================
               BUTTONS
            ============================================================ */
            QPushButton {{
                background: {KocaeliTheme.WHITE};
                border: 1px solid {KocaeliTheme.BORDER};
                border-radius: 8px;
                padding: 10px 20px;
                color: {KocaeliTheme.GRAY_700};
                font-size: 13px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background: {KocaeliTheme.HOVER_BG};
                border: 1px solid {KocaeliTheme.PRIMARY};
            }}
            
            QPushButton:pressed {{
                background: {KocaeliTheme.GRAY_200};
            }}
            
            QPushButton:disabled {{
                background: {KocaeliTheme.GRAY_100};
                color: {KocaeliTheme.GRAY_400};
                border: 1px solid {KocaeliTheme.GRAY_200};
            }}
            
            QPushButton#primaryBtn {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {KocaeliTheme.PRIMARY},
                    stop:1 {KocaeliTheme.PRIMARY_LIGHT}
                );
                color: white;
                border: none;
                font-weight: 600;
            }}
            
            QPushButton#primaryBtn:hover {{
                background: {KocaeliTheme.PRIMARY_DARK};
            }}
            
            QPushButton#dangerBtn {{
                background: {KocaeliTheme.ERROR};
                color: white;
                border: none;
            }}
            
            QPushButton#dangerBtn:hover {{
                background: #dc2626;
            }}
            
            /* ============================================================
               INPUT FIELDS
            ============================================================ */
            QLineEdit {{
                background: {KocaeliTheme.WHITE};
                border: 2px solid {KocaeliTheme.BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                color: {KocaeliTheme.GRAY_900};
            }}
            
            QLineEdit:focus {{
                border: 2px solid {KocaeliTheme.PRIMARY};
                background: {KocaeliTheme.WHITE};
            }}
            
            QLineEdit:disabled {{
                background: {KocaeliTheme.GRAY_100};
                color: {KocaeliTheme.GRAY_500};
            }}
            
            QTextEdit {{
                background: {KocaeliTheme.WHITE};
                border: 2px solid {KocaeliTheme.BORDER};
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                color: {KocaeliTheme.GRAY_900};
            }}
            
            QTextEdit:focus {{
                border: 2px solid {KocaeliTheme.PRIMARY};
            }}
            
            /* ============================================================
               COMBO BOX
            ============================================================ */
            QComboBox {{
                background: {KocaeliTheme.WHITE};
                border: 2px solid {KocaeliTheme.BORDER};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 13px;
                min-height: 32px;
            }}
            
            QComboBox:focus {{
                border: 2px solid {KocaeliTheme.PRIMARY};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {KocaeliTheme.GRAY_500};
                margin-right: 8px;
            }}
            
            QComboBox QAbstractItemView {{
                background: {KocaeliTheme.WHITE};
                border: 1px solid {KocaeliTheme.BORDER};
                border-radius: 8px;
                selection-background-color: {KocaeliTheme.SUCCESS_BG};
                selection-color: {KocaeliTheme.PRIMARY};
                padding: 4px;
            }}
            
            /* ============================================================
               TABLE VIEW
            ============================================================ */
            QTableView {{
                background: {KocaeliTheme.WHITE};
                border: 1px solid {KocaeliTheme.BORDER};
                border-radius: 12px;
                gridline-color: {KocaeliTheme.GRAY_200};
                selection-background-color: {KocaeliTheme.SUCCESS_BG};
                selection-color: {KocaeliTheme.GRAY_900};
            }}
            
            QTableView::item {{
                padding: 8px;
                border-bottom: 1px solid {KocaeliTheme.GRAY_100};
            }}
            
            QTableView::item:selected {{
                background: {KocaeliTheme.SUCCESS_BG};
                color: {KocaeliTheme.GRAY_900};
            }}
            
            QTableView::item:hover {{
                background: {KocaeliTheme.HOVER_BG};
            }}
            
            QHeaderView::section {{
                background: {KocaeliTheme.GRAY_50};
                color: {KocaeliTheme.GRAY_700};
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid {KocaeliTheme.BORDER};
                font-weight: 600;
                font-size: 12px;
            }}
            
            /* ============================================================
               SCROLL BAR
            ============================================================ */
            QScrollBar:vertical {{
                background: {KocaeliTheme.GRAY_100};
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background: {KocaeliTheme.GRAY_300};
                border-radius: 6px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {KocaeliTheme.GRAY_400};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background: {KocaeliTheme.GRAY_100};
                height: 12px;
                border-radius: 6px;
                margin: 0;
            }}
            
            QScrollBar::handle:horizontal {{
                background: {KocaeliTheme.GRAY_300};
                border-radius: 6px;
                min-width: 30px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background: {KocaeliTheme.GRAY_400};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            
            /* ============================================================
               CHECKBOX & RADIO
            ============================================================ */
            QCheckBox {{
                spacing: 8px;
                color: {KocaeliTheme.GRAY_700};
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {KocaeliTheme.BORDER};
                background: {KocaeliTheme.WHITE};
            }}
            
            QCheckBox::indicator:hover {{
                border: 2px solid {KocaeliTheme.PRIMARY};
            }}
            
            QCheckBox::indicator:checked {{
                background: {KocaeliTheme.PRIMARY};
                border: 2px solid {KocaeliTheme.PRIMARY};
            }}
            
            QRadioButton {{
                spacing: 8px;
                color: {KocaeliTheme.GRAY_700};
            }}
            
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {KocaeliTheme.BORDER};
                background: {KocaeliTheme.WHITE};
            }}
            
            QRadioButton::indicator:hover {{
                border: 2px solid {KocaeliTheme.PRIMARY};
            }}
            
            QRadioButton::indicator:checked {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {KocaeliTheme.PRIMARY},
                    stop:1 {KocaeliTheme.PRIMARY_LIGHT}
                );
                border: 2px solid {KocaeliTheme.PRIMARY};
            }}
            
            /* ============================================================
               PROGRESS BAR
            ============================================================ */
            QProgressBar {{
                background: {KocaeliTheme.GRAY_200};
                border-radius: 6px;
                text-align: center;
                color: {KocaeliTheme.GRAY_700};
                font-weight: 600;
                font-size: 11px;
            }}
            
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {KocaeliTheme.PRIMARY},
                    stop:1 {KocaeliTheme.SUCCESS}
                );
                border-radius: 6px;
            }}
            
            /* ============================================================
               TAB WIDGET
            ============================================================ */
            QTabWidget::pane {{
                background: {KocaeliTheme.WHITE};
                border: 1px solid {KocaeliTheme.BORDER};
                border-radius: 12px;
                top: -1px;
            }}
            
            QTabBar::tab {{
                background: {KocaeliTheme.GRAY_100};
                color: {KocaeliTheme.GRAY_600};
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
            }}
            
            QTabBar::tab:selected {{
                background: {KocaeliTheme.WHITE};
                color: {KocaeliTheme.PRIMARY};
                border-bottom: 3px solid {KocaeliTheme.PRIMARY};
            }}
            
            QTabBar::tab:hover {{
                background: {KocaeliTheme.HOVER_BG};
            }}
            
            /* ============================================================
               LABELS
            ============================================================ */
            QLabel {{
                color: {KocaeliTheme.GRAY_900};
                border: none;
                background: transparent;
            }}
            
            /* ============================================================
               MESSAGE BOX
            ============================================================ */
            QMessageBox {{
                background: {KocaeliTheme.WHITE};
            }}
            
            QMessageBox QLabel {{
                color: {KocaeliTheme.GRAY_900};
                font-size: 13px;
            }}
            
            /* ============================================================
               MENU & MENU BAR
            ============================================================ */
            QMenuBar {{
                background: {KocaeliTheme.WHITE};
                border-bottom: 1px solid {KocaeliTheme.BORDER};
                padding: 4px;
            }}
            
            QMenuBar::item {{
                padding: 8px 12px;
                background: transparent;
                border-radius: 6px;
            }}
            
            QMenuBar::item:selected {{
                background: {KocaeliTheme.HOVER_BG};
            }}
            
            QMenu {{
                background: {KocaeliTheme.WHITE};
                border: 1px solid {KocaeliTheme.BORDER};
                border-radius: 8px;
                padding: 4px;
            }}
            
            QMenu::item {{
                padding: 8px 24px 8px 12px;
                border-radius: 6px;
            }}
            
            QMenu::item:selected {{
                background: {KocaeliTheme.SUCCESS_BG};
                color: {KocaeliTheme.PRIMARY};
            }}
            
            /* ============================================================
               SPIN BOX
            ============================================================ */
            QSpinBox, QDoubleSpinBox {{
                background: {KocaeliTheme.WHITE};
                border: 2px solid {KocaeliTheme.BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {KocaeliTheme.PRIMARY};
            }}
            
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                border: none;
                background: transparent;
                width: 20px;
            }}
            
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                border: none;
                background: transparent;
                width: 20px;
            }}
            
            /* ============================================================
               DATE EDIT
            ============================================================ */
            QDateEdit, QTimeEdit, QDateTimeEdit {{
                background: {KocaeliTheme.WHITE};
                border: 2px solid {KocaeliTheme.BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            
            QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {{
                border: 2px solid {KocaeliTheme.PRIMARY};
            }}
            
            QCalendarWidget {{
                background: {KocaeliTheme.WHITE};
                border: 1px solid {KocaeliTheme.BORDER};
                border-radius: 12px;
            }}
            
            QCalendarWidget QToolButton {{
                color: {KocaeliTheme.GRAY_700};
                background: transparent;
                border-radius: 6px;
            }}
            
            QCalendarWidget QToolButton:hover {{
                background: {KocaeliTheme.HOVER_BG};
            }}
            
            QCalendarWidget QAbstractItemView:enabled {{
                color: {KocaeliTheme.GRAY_900};
                background: {KocaeliTheme.WHITE};
                selection-background-color: {KocaeliTheme.PRIMARY};
                selection-color: white;
            }}
        """
    
    @staticmethod
    def _dark_stylesheet():
        """Dark mode stylesheet (future implementation)"""
        return KocaeliTheme._light_stylesheet()  # For now, return light theme
    
    @staticmethod
    def get_color_palette():
        """Get QPalette for the theme"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(KocaeliTheme.GRAY_50))
        palette.setColor(QPalette.WindowText, QColor(KocaeliTheme.GRAY_900))
        palette.setColor(QPalette.Base, QColor(KocaeliTheme.WHITE))
        palette.setColor(QPalette.AlternateBase, QColor(KocaeliTheme.GRAY_100))
        palette.setColor(QPalette.ToolTipBase, QColor(KocaeliTheme.GRAY_900))
        palette.setColor(QPalette.ToolTipText, QColor(KocaeliTheme.WHITE))
        palette.setColor(QPalette.Text, QColor(KocaeliTheme.GRAY_900))
        palette.setColor(QPalette.Button, QColor(KocaeliTheme.WHITE))
        palette.setColor(QPalette.ButtonText, QColor(KocaeliTheme.GRAY_900))
        palette.setColor(QPalette.Link, QColor(KocaeliTheme.PRIMARY))
        palette.setColor(QPalette.Highlight, QColor(KocaeliTheme.PRIMARY))
        palette.setColor(QPalette.HighlightedText, QColor(KocaeliTheme.WHITE))
        return palette

