"""
Sınav Oluştur View - COMPLETE REFACTORED VERSION
Sadece UI ve kullanıcı etkileşimi
İş mantığı tamamen controller ve algorithm katmanlarında
"""

import logging
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QDateTimeEdit, QMessageBox,
    QGroupBox, QFormLayout, QSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QCheckBox,
    QLineEdit, QScrollArea, QFileDialog, QTabWidget, QDialog,
    QSizePolicy
)
from PySide6.QtCore import Qt, QDateTime, QThread, Signal
from PySide6.QtGui import QFont, QColor

from models.database import db
from models.sinav_model import SinavModel
from models.ders_model import DersModel
from models.derslik_model import DerslikModel
from models.ogrenci_model import OgrenciModel
from controllers.sinav_controller import SinavController
from algorithms.sinav_planlama import SinavPlanlama
from algorithms.scoring_system import SinavProgramScorer
from styles.kou_theme import KOUTheme  # Modern KOÜ yeşil tema
from algorithms.attempt_manager import AttemptManager
from utils.export_utils import ExportUtils
from utils.modern_dialogs import ModernMessageBox, sanitize_filename
from utils.view_helpers import refresh_main_window_ui
from views.koordinator.program_result_dialog import ProgramResultDialog

logger = logging.getLogger(__name__)


class SinavPlanlamaThread(QThread):
    """Thread for exam planning with multiple attempts"""
    progress = Signal(int, str)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, params, use_multiple_attempts=True):
        super().__init__()
        self.params = params
        self.use_multiple_attempts = use_multiple_attempts

    def run(self):
        try:
            if self.use_multiple_attempts:
                # Çoklu deneme modu
                scorer = SinavProgramScorer()
                attempt_manager = AttemptManager(scorer)
                planner = SinavPlanlama()

                result = attempt_manager.run_multiple_attempts(
                    planning_function=planner.plan_exam_schedule,
                    params=self.params,
                    max_attempts=self.params.get('max_attempts', 300),  # Default to 300
                    progress_callback=self.progress.emit
                )
            else:
                # Tek deneme modu
                planner = SinavPlanlama()
                result = planner.plan_exam_schedule(
                    self.params,
                    progress_callback=self.progress.emit
                )

            self.finished.emit(result)

        except Exception as e:
            logger.error(f"Planning thread error: {e}", exc_info=True)
            self.error.emit(str(e))


class SinavOlusturView(QWidget):
    """Modern exam schedule creation view"""

    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.bolum_id = user_data.get('bolum_id', 1)

        # Models
        self.sinav_model = SinavModel(db)
        self.ders_model = DersModel(db)
        self.derslik_model = DerslikModel(db)
        self.ogrenci_model = OgrenciModel(db)

        # Controller
        self.controller = SinavController(
            self.sinav_model,
            self.ders_model,
            self.derslik_model
        )

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup modern UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Modern header with KOÜ theme
        header = QLabel("📅 Sınav Programı Yönetimi")
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet(KOUTheme.header_label())
        layout.addWidget(header)

        # Tab widget with modern KOÜ theme
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Segoe UI", 11))
        self.tab_widget.setStyleSheet(KOUTheme.tab_widget())

        # Tab 1: Existing Programs
        self.programs_tab = QWidget()
        self.setup_programs_tab()
        self.tab_widget.addTab(self.programs_tab, "📋 Mevcut Programlar")

        # Tab 2: Create New
        self.create_tab = QWidget()
        self.setup_create_tab()
        self.tab_widget.addTab(self.create_tab, "➕ Yeni Program Oluştur")

        layout.addWidget(self.tab_widget)

    def setup_programs_tab(self):
        """Setup existing programs tab with modern KOÜ theme"""
        layout = QVBoxLayout(self.programs_tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Programs table with modern theme (no toolbar - clean look)
        self.programs_table = QTableWidget()
        self.programs_table.setColumnCount(6)
        self.programs_table.setHorizontalHeaderLabels([
            "Program Adı", "Sınav Tipi", "Başlangıç", "Bitiş", "Sınav Sayısı", "İşlemler"
        ])
        self.programs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.programs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.programs_table.setSelectionMode(QTableWidget.SingleSelection)
        self.programs_table.setAlternatingRowColors(True)
        self.programs_table.verticalHeader().setVisible(False)
        self.programs_table.verticalHeader().setDefaultSectionSize(80)
        self.programs_table.setStyleSheet(KOUTheme.table())

        # Make table expand to fill the tab area
        self.programs_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        header = self.programs_table.horizontalHeader()
        # Program adı sadece içeriği kadar yer kaplasın, tarih kolonları boşluğu doldursun
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Program Adı
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Sınav Tipi
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)           # Başlangıç
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)           # Bitiş
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Sınav Sayısı
        header.setSectionResizeMode(5, QHeaderView.Stretch)             # İşlemler

        # İşlemler kolonu geniş; butonlar sığsın ve program adı alanı kalabilsin
        header.resizeSection(5, 520)
        header.sectionResized.connect(self._on_programs_section_resized)

        # Use stretch so table consumes remaining space vertically
        layout.addWidget(self.programs_table, 1)

        # Auto-load existing programs (no manual refresh needed)
        self.load_existing_programs()

    def setup_create_tab(self):
        """Setup create new program tab"""
        layout = QVBoxLayout(self.create_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Global SpinBox style
        self.create_tab.setStyleSheet("""
            QSpinBox {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 8px;
                background: white;
            }
            QSpinBox:focus {
                border: 1px solid #3b82f6;
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 16px;
                border-left: 1px solid #cbd5e1;
                background: #f8fafc;
            }
            QSpinBox::up-button:hover {
                background: #e2e8f0;
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 16px;
                border-left: 1px solid #cbd5e1;
                background: #f8fafc;
            }
            QSpinBox::down-button:hover {
                background: #e2e8f0;
            }
            QSpinBox::up-arrow {
                width: 7px;
                height: 7px;
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid #475569;
            }
            QSpinBox::down-arrow {
                width: 7px;
                height: 7px;
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #475569;
            }
        """)

        # Three column layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(12)

        # LEFT COLUMN
        left_col = QVBoxLayout()
        left_col.setSpacing(16)

        # Basic info
        basic_group = self._create_basic_info_group()
        left_col.addWidget(basic_group)

        # Constraints
        constraints_group = self._create_constraints_group()
        left_col.addWidget(constraints_group)

        # Time settings
        time_group = self._create_time_settings_group()
        left_col.addWidget(time_group)

        # Days
        days_group = self._create_days_group()
        left_col.addWidget(days_group)

        main_layout.addLayout(left_col, 1)

        # RIGHT COLUMN - Courses
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        course_group = self._create_course_selection_group()
        right_col.addWidget(course_group)

        main_layout.addLayout(right_col, 2)

        layout.addLayout(main_layout)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(24)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                text-align: center;
                background: #f8fafc;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #059669);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.progress_label)

        # Create button
        self.create_btn = QPushButton("🚀 Sınav Programı Oluştur")
        self.create_btn.setMinimumHeight(42)
        self.create_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.create_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #059669);
                color: white;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                border: 2px solid #047857;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #047857);
                border: 2px solid #065f46;
            }
            QPushButton:disabled {
                background: #d1d5db;
                color: #9ca3af;
                border: 2px solid #d1d5db;
            }
        """)
        self.create_btn.clicked.connect(self.create_schedule)
        layout.addWidget(self.create_btn)

    def _create_basic_info_group(self) -> QGroupBox:
        """Create basic info group"""
        group = QGroupBox("⚙️ Temel Bilgiler")
        group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        group.setStyleSheet("""
            QGroupBox {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                margin-top: 8px;
                font-size: 11px;
                color: #1e293b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #1e293b;
                background: white;
            }
        """)
        layout = QFormLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        input_style = """
            QComboBox, QDateTimeEdit {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                background: white;
                color: #1e293b;
            }
            QComboBox:focus, QDateTimeEdit:focus {
                border: 1px solid #3b82f6;
            }
        """

        self.sinav_tipi_combo = QComboBox()
        self.sinav_tipi_combo.addItems(["Vize", "Final", "Bütünleme"])
        self.sinav_tipi_combo.setFixedHeight(28)
        self.sinav_tipi_combo.setStyleSheet(input_style)
        layout.addRow("Sınav Tipi:", self.sinav_tipi_combo)

        self.baslangic_tarih = QDateTimeEdit()
        self.baslangic_tarih.setDateTime(QDateTime.currentDateTime().addDays(7))
        self.baslangic_tarih.setCalendarPopup(True)
        self.baslangic_tarih.setDisplayFormat("dd.MM.yyyy")
        self.baslangic_tarih.setFixedHeight(28)
        self.baslangic_tarih.setStyleSheet(input_style)
        layout.addRow("Başlangıç:", self.baslangic_tarih)

        self.bitis_tarih = QDateTimeEdit()
        self.bitis_tarih.setDateTime(QDateTime.currentDateTime().addDays(14))
        self.bitis_tarih.setCalendarPopup(True)
        self.bitis_tarih.setDisplayFormat("dd.MM.yyyy")
        self.bitis_tarih.setFixedHeight(28)
        self.bitis_tarih.setStyleSheet(input_style)
        layout.addRow("Bitiş:", self.bitis_tarih)

        self.sinav_suresi = QSpinBox()
        self.sinav_suresi.setRange(1, 999)
        self.sinav_suresi.setValue(75)
        self.sinav_suresi.setSuffix(" dk")
        self.sinav_suresi.setFixedHeight(28)
        self.sinav_suresi.setMinimumWidth(90)
        self.sinav_suresi.valueChanged.connect(self.update_all_course_durations)
        layout.addRow("Sınav Süresi:", self.sinav_suresi)

        self.ara_suresi = QSpinBox()
        self.ara_suresi.setRange(5, 60)
        self.ara_suresi.setValue(15)
        self.ara_suresi.setSuffix(" dk")
        self.ara_suresi.setFixedHeight(28)
        self.ara_suresi.setMinimumWidth(90)
        layout.addRow("Bekleme:", self.ara_suresi)

        return group

    def _create_constraints_group(self) -> QGroupBox:
        """Create constraints group"""
        group = QGroupBox("🔒 Kısıtlamalar")
        group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        group.setStyleSheet("""
            QGroupBox {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                margin-top: 8px;
                font-size: 11px;
                color: #1e293b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #1e293b;
                background: white;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        self.ayni_anda_sinav_checkbox = QCheckBox("Paralel sınav olmasın")
        self.ayni_anda_sinav_checkbox.setToolTip("Bir sınav başladığında, o sınav bitene kadar başka sınav başlamaz")
        self.ayni_anda_sinav_checkbox.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.ayni_anda_sinav_checkbox)

        gunluk_limit_layout = QHBoxLayout()
        gunluk_limit_layout.setSpacing(12)

        gunluk_limit_label = QLabel("Günlük limit (sınıf):")
        gunluk_limit_label.setStyleSheet("font-size: 11px; color: #1e293b;")
        self.gunluk_sinav_limiti = QSpinBox()
        self.gunluk_sinav_limiti.setRange(1, 10)
        self.gunluk_sinav_limiti.setValue(3)
        self.gunluk_sinav_limiti.setFixedHeight(28)
        self.gunluk_sinav_limiti.setFixedWidth(60)
        self.gunluk_sinav_limiti.setToolTip("Bir sınıf için günde maksimum kaç sınav olabilir")

        ogrenci_limit_label = QLabel("Günlük limit (öğrenci):")
        ogrenci_limit_label.setStyleSheet("font-size: 11px; color: #1e293b;")
        self.ogrenci_gunluk_limiti = QSpinBox()
        self.ogrenci_gunluk_limiti.setRange(0, 10)  # 0 = limit yok
        self.ogrenci_gunluk_limiti.setValue(0)      # Varsayılan: günde en fazla 1 sınav
        self.ogrenci_gunluk_limiti.setFixedHeight(28)
        self.ogrenci_gunluk_limiti.setFixedWidth(60)
        self.ogrenci_gunluk_limiti.setToolTip("Öğrenci günlük limit (0 = yok, 1-10 = katı kural - UYULMALI)")
        self.ogrenci_gunluk_limiti.setSpecialValueText("Yok")  # Show "Yok" instead of "0"

        gunluk_limit_layout.addWidget(gunluk_limit_label)
        gunluk_limit_layout.addWidget(self.gunluk_sinav_limiti)
        gunluk_limit_layout.addSpacing(16)
        gunluk_limit_layout.addWidget(ogrenci_limit_label)
        gunluk_limit_layout.addWidget(self.ogrenci_gunluk_limiti)
        gunluk_limit_layout.addStretch()
        layout.addLayout(gunluk_limit_layout)

        return group

    def _create_time_settings_group(self) -> QGroupBox:
        """Create time settings group"""
        group = QGroupBox("🕐 Saat Ayarları")
        group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        group.setStyleSheet("""
            QGroupBox {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                margin-top: 8px;
                font-size: 11px;
                color: #1e293b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #1e293b;
                background: white;
            }
        """)
        layout = QFormLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # First exam
        first_layout = QHBoxLayout()
        first_layout.setSpacing(4)
        self.ilk_sinav_saat = QSpinBox()
        self.ilk_sinav_saat.setRange(0, 23)
        self.ilk_sinav_saat.setValue(10)
        self.ilk_sinav_saat.setFixedHeight(28)
        self.ilk_sinav_saat.setFixedWidth(50)
        self.ilk_sinav_dakika = QSpinBox()
        self.ilk_sinav_dakika.setRange(0, 59)
        self.ilk_sinav_dakika.setValue(0)
        self.ilk_sinav_dakika.setFixedHeight(28)
        self.ilk_sinav_dakika.setFixedWidth(50)
        first_layout.addWidget(self.ilk_sinav_saat)
        sep1 = QLabel(":")
        sep1.setStyleSheet("font-size: 14px; font-weight: bold;")
        first_layout.addWidget(sep1)
        first_layout.addWidget(self.ilk_sinav_dakika)
        first_layout.addStretch()
        layout.addRow("İlk:", first_layout)

        # Last exam
        last_layout = QHBoxLayout()
        last_layout.setSpacing(4)
        self.son_sinav_saat = QSpinBox()
        self.son_sinav_saat.setRange(0, 23)
        self.son_sinav_saat.setValue(19)
        self.son_sinav_saat.setFixedHeight(28)
        self.son_sinav_saat.setFixedWidth(50)
        self.son_sinav_dakika = QSpinBox()
        self.son_sinav_dakika.setRange(0, 59)
        self.son_sinav_dakika.setValue(15)
        self.son_sinav_dakika.setFixedHeight(28)
        self.son_sinav_dakika.setFixedWidth(50)
        last_layout.addWidget(self.son_sinav_saat)
        sep2 = QLabel(":")
        sep2.setStyleSheet("font-size: 14px; font-weight: bold;")
        last_layout.addWidget(sep2)
        last_layout.addWidget(self.son_sinav_dakika)
        last_layout.addStretch()
        layout.addRow("Son:", last_layout)

        # Lunch start
        lunch_start_layout = QHBoxLayout()
        lunch_start_layout.setSpacing(4)
        self.ogle_baslangic_saat = QSpinBox()
        self.ogle_baslangic_saat.setRange(0, 23)
        self.ogle_baslangic_saat.setValue(12)
        self.ogle_baslangic_saat.setFixedHeight(28)
        self.ogle_baslangic_saat.setFixedWidth(50)
        self.ogle_baslangic_dakika = QSpinBox()
        self.ogle_baslangic_dakika.setRange(0, 59)
        self.ogle_baslangic_dakika.setValue(0)
        self.ogle_baslangic_dakika.setFixedHeight(28)
        self.ogle_baslangic_dakika.setFixedWidth(50)
        lunch_start_layout.addWidget(self.ogle_baslangic_saat)
        sep3 = QLabel(":")
        sep3.setStyleSheet("font-size: 14px; font-weight: bold;")
        lunch_start_layout.addWidget(sep3)
        lunch_start_layout.addWidget(self.ogle_baslangic_dakika)
        lunch_start_layout.addStretch()
        layout.addRow("Öğle Baş:", lunch_start_layout)

        # Lunch end
        lunch_end_layout = QHBoxLayout()
        lunch_end_layout.setSpacing(4)
        self.ogle_bitis_saat = QSpinBox()
        self.ogle_bitis_saat.setRange(0, 23)
        self.ogle_bitis_saat.setValue(13)
        self.ogle_bitis_saat.setFixedHeight(28)
        self.ogle_bitis_saat.setFixedWidth(50)
        self.ogle_bitis_dakika = QSpinBox()
        self.ogle_bitis_dakika.setRange(0, 59)
        self.ogle_bitis_dakika.setValue(0)
        self.ogle_bitis_dakika.setFixedHeight(28)
        self.ogle_bitis_dakika.setFixedWidth(50)
        lunch_end_layout.addWidget(self.ogle_bitis_saat)
        sep4 = QLabel(":")
        sep4.setStyleSheet("font-size: 14px; font-weight: bold;")
        lunch_end_layout.addWidget(sep4)
        lunch_end_layout.addWidget(self.ogle_bitis_dakika)
        lunch_end_layout.addStretch()
        layout.addRow("Öğle Bit:", lunch_end_layout)

        return group

    def _create_days_group(self) -> QGroupBox:
        """Create days selection group"""
        group = QGroupBox("📅 Günler")
        group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        group.setStyleSheet("""
            QGroupBox {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                margin-top: 8px;
                font-size: 11px;
                color: #1e293b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #1e293b;
                background: white;
            }
            QCheckBox {
                spacing: 4px;
                font-size: 10px;
                color: #1e293b;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #e2e8f0;
                border-radius: 4px;
                background: white;
            }
            QCheckBox::indicator:checked {
                background: #10b981;
                border-color: #10b981;
            }
        """)

        days_main_layout = QVBoxLayout(group)
        days_main_layout.setSpacing(4)
        days_main_layout.setContentsMargins(8, 8, 8, 8)

        # Weekdays
        weekdays_layout = QHBoxLayout()
        weekdays_layout.setSpacing(4)

        # Weekend
        weekend_layout = QHBoxLayout()
        weekend_layout.setSpacing(4)

        self.gun_checkboxes = {}
        gun_isimleri = {
            0: "Pzt", 1: "Sal", 2: "Çar", 3: "Per",
            4: "Cum", 5: "Cmt", 6: "Paz"
        }

        for day_num in range(5):
            checkbox = QCheckBox(gun_isimleri[day_num])
            checkbox.setChecked(True)
            self.gun_checkboxes[day_num] = checkbox
            weekdays_layout.addWidget(checkbox)

        for day_num in range(5, 7):
            checkbox = QCheckBox(gun_isimleri[day_num])
            self.gun_checkboxes[day_num] = checkbox
            weekend_layout.addWidget(checkbox)

        weekend_layout.addStretch()

        days_main_layout.addLayout(weekdays_layout)
        days_main_layout.addLayout(weekend_layout)

        return group

    def _create_course_selection_group(self) -> QGroupBox:
        """Create course selection group"""
        group = QGroupBox("📚 Ders Seçimi")
        group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        group.setStyleSheet("""
            QGroupBox {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                margin-top: 8px;
                font-size: 11px;
                color: #1e293b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #1e293b;
                background: white;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Info
        info_label = QLabel("Sınava dahil olmayanların işaretini kaldırın")
        info_label.setStyleSheet("color: #64748b; font-size: 10px; padding: 4px; background: #f8fafc; border-radius: 4px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.ders_search = QLineEdit()
        self.ders_search.setPlaceholderText("🔍 Ara...")
        self.ders_search.setFixedHeight(28)
        self.ders_search.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """)
        self.ders_search.textChanged.connect(self.filter_courses)
        toolbar.addWidget(self.ders_search, 1)

        select_all_btn = QPushButton("✓ Tümü")
        select_all_btn.setFixedHeight(28)
        select_all_btn.setCursor(Qt.PointingHandCursor)
        select_all_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
                padding: 0 10px;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        select_all_btn.clicked.connect(self.select_all_courses)
        toolbar.addWidget(select_all_btn)

        clear_all_btn = QPushButton("✗")
        clear_all_btn.setFixedHeight(28)
        clear_all_btn.setFixedWidth(32)
        clear_all_btn.setCursor(Qt.PointingHandCursor)
        clear_all_btn.setStyleSheet("""
            QPushButton {
                background: #f59e0b;
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #d97706;
            }
        """)
        clear_all_btn.clicked.connect(self.clear_all_courses)
        toolbar.addWidget(clear_all_btn)

        check_parallel_btn = QPushButton("👥")
        check_parallel_btn.setFixedHeight(28)
        check_parallel_btn.setFixedWidth(32)
        check_parallel_btn.setCursor(Qt.PointingHandCursor)
        check_parallel_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        check_parallel_btn.setToolTip("Ortak öğrenciler")
        check_parallel_btn.clicked.connect(self.show_parallel_exams)
        toolbar.addWidget(check_parallel_btn)

        layout.addLayout(toolbar)

        # Course list
        course_scroll = QScrollArea()
        course_scroll.setWidgetResizable(True)

        self.ders_container = QWidget()
        self.ders_container_layout = QVBoxLayout(self.ders_container)
        self.ders_container_layout.setSpacing(4)
        self.ders_checkboxes = {}
        self.ders_duration_spinboxes = {}

        course_scroll.setWidget(self.ders_container)
        layout.addWidget(course_scroll)

        # Stats
        self.ders_stats_label = QLabel("Yükleniyor...")
        self.ders_stats_label.setStyleSheet("color: #6b7280; font-size: 12px; padding: 4px;")
        layout.addWidget(self.ders_stats_label)

        return group

    def load_data(self):
        """Load necessary data"""
        try:
            dersler = self.ders_model.get_dersler_by_bolum(self.bolum_id)
            derslikler = self.derslik_model.get_derslikler_by_bolum(self.bolum_id)

            if not dersler:
                QMessageBox.warning(self, "Uyarı", "Henüz ders tanımlanmamış!")
                return

            if not derslikler:
                QMessageBox.warning(self, "Uyarı", "Henüz derslik tanımlanmamış!")
                return

            self.populate_course_list(dersler)

        except Exception as e:
            logger.error(f"Error loading data: {e}")

    def populate_course_list(self, dersler):
        """Populate course selection checkboxes"""
        while self.ders_container_layout.count():
            item = self.ders_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.ders_checkboxes.clear()
        self.ders_duration_spinboxes.clear()

        for ders in dersler:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            checkbox = QCheckBox(f"{ders['ders_kodu']} - {ders['ders_adi']}")
            checkbox.setChecked(True)
            checkbox.setProperty('ders_id', ders['ders_id'])
            checkbox.setStyleSheet("font-size: 11px;")
            checkbox.stateChanged.connect(self.update_course_stats)
            row_layout.addWidget(checkbox, 1)

            duration_label = QLabel("Süre:")
            duration_label.setStyleSheet("color: #6b7280; font-size: 10px;")
            row_layout.addWidget(duration_label)

            duration_spinbox = QSpinBox()
            duration_spinbox.setRange(1, 999)
            duration_spinbox.setValue(75)
            duration_spinbox.setSuffix(" dk")
            duration_spinbox.setFixedWidth(75)
            duration_spinbox.setFixedHeight(24)
            duration_spinbox.setToolTip("Bu ders için sınav süresi")
            row_layout.addWidget(duration_spinbox)

            self.ders_checkboxes[ders['ders_id']] = checkbox
            self.ders_duration_spinboxes[ders['ders_id']] = duration_spinbox
            self.ders_container_layout.addWidget(row_widget)

        self.update_course_stats()

    def filter_courses(self):
        """Filter courses based on search"""
        search_text = self.ders_search.text().lower()

        for ders_id, checkbox in self.ders_checkboxes.items():
            text = checkbox.text().lower()
            checkbox.parent().setVisible(search_text in text)

    def select_all_courses(self):
        """Select all courses"""
        for checkbox in self.ders_checkboxes.values():
            checkbox.setChecked(True)
        self.update_course_stats()

    def clear_all_courses(self):
        """Clear all course selections"""
        for checkbox in self.ders_checkboxes.values():
            checkbox.setChecked(False)
        self.update_course_stats()

    def update_course_stats(self):
        """Update course selection statistics"""
        total = len(self.ders_checkboxes)
        selected = sum(1 for cb in self.ders_checkboxes.values() if cb.isChecked())
        self.ders_stats_label.setText(f"📊 Seçili: {selected} / {total} ders")

    def update_all_course_durations(self, value):
        """Update all course duration spinboxes"""
        for spinbox in self.ders_duration_spinboxes.values():
            spinbox.setValue(value)

    def show_parallel_exams(self):
        """Show which courses can be held in parallel"""
        try:
            dersler = self.ders_model.get_dersler_by_bolum(self.bolum_id)
            if not dersler or len(dersler) < 2:
                QMessageBox.information(self, "Bilgi", "En az 2 ders olmalıdır!")
                return

            course_students = {}
            course_info = {}

            for ders in dersler:
                ogrenciler = self.ogrenci_model.get_ogrenciler_by_ders(ders['ders_id'])
                student_ids = set(o['ogrenci_no'] for o in ogrenciler)
                course_students[ders['ders_id']] = student_ids
                course_info[ders['ders_id']] = {
                    'ders_kodu': ders['ders_kodu'],
                    'ders_adi': ders['ders_adi'],
                    'sinif': ders.get('sinif', 0),
                    'ogrenci_sayisi': len(student_ids)
                }

            all_pairs = []
            course_ids = list(course_info.keys())

            for ders_id1 in course_ids:
                for ders_id2 in course_ids:
                    if ders_id1 >= ders_id2:
                        continue

                    shared = len(course_students[ders_id1] & course_students[ders_id2])

                    all_pairs.append((
                        course_info[ders_id1]['ders_kodu'],
                        course_info[ders_id2]['ders_kodu'],
                        course_info[ders_id1]['sinif'],
                        course_info[ders_id2]['sinif'],
                        shared
                    ))

            all_pairs.sort(key=lambda x: x[4], reverse=True)

            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Tüm Ders Çiftleri - Ortak Öğrenci Analizi")
            dialog.setMinimumSize(1000, 700)

            layout = QVBoxLayout(dialog)

            header = QLabel(f"📊 Tüm Ders Çiftleri Analizi ({len(all_pairs)} çift)")
            header.setFont(QFont("Segoe UI", 14, QFont.Bold))
            layout.addWidget(header)

            zero_conflict = sum(1 for p in all_pairs if p[4] == 0)
            high_conflict = sum(1 for p in all_pairs if p[4] >= 10)

            info = QLabel(
                f"✅ Ortak öğrencisi olmayan: {zero_conflict} çift\n"
                f"⚠️ Orta çakışma (5-9 öğrenci): {sum(1 for p in all_pairs if 5 <= p[4] < 10)} çift\n"
                f"❌ Yüksek çakışma (10+ öğrenci): {high_conflict} çift"
            )
            info.setStyleSheet("color: #6b7280; padding: 10px; background: #f3f4f6; border-radius: 4px;")
            layout.addWidget(info)

            table = QTableWidget()
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels(["Ders 1", "Sınıf", "Ders 2", "Sınıf", "Ortak Öğrenci", "Durum"])
            table.setRowCount(len(all_pairs))

            for row, (d1, d2, s1, s2, shared) in enumerate(all_pairs):
                table.setItem(row, 0, QTableWidgetItem(d1))
                table.setItem(row, 1, QTableWidgetItem(f"{s1}. Sınıf"))
                table.setItem(row, 2, QTableWidgetItem(d2))
                table.setItem(row, 3, QTableWidgetItem(f"{s2}. Sınıf"))

                count_item = QTableWidgetItem(str(shared))
                count_item.setTextAlignment(Qt.AlignCenter)
                count_item.setFont(QFont("Segoe UI", 10, QFont.Bold))

                if shared == 0:
                    count_item.setForeground(QColor("#10b981"))
                    status = "✅ Paralel yapılabilir"
                elif shared < 5:
                    count_item.setForeground(QColor("#3b82f6"))
                    status = "ℹ️ Az çakışma"
                elif shared < 10:
                    count_item.setForeground(QColor("#f59e0b"))
                    status = "⚠️ Orta çakışma"
                else:
                    count_item.setForeground(QColor("#dc2626"))
                    status = "❌ Yüksek çakışma"

                table.setItem(row, 4, count_item)

                status_item = QTableWidgetItem(status)
                status_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, 5, status_item)

            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setAlternatingRowColors(True)
            table.setSortingEnabled(True)
            layout.addWidget(table)

            close_btn = QPushButton("Kapat")
            close_btn.setFixedHeight(35)
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.exec()

        except Exception as e:
            logger.error(f"Error analyzing parallel exams: {e}")
            QMessageBox.critical(self, "Hata", f"Analiz hatası: {str(e)}")

    def create_schedule(self):
        """Create exam schedule"""
        # Validate
        validation = self._validate_inputs()
        if not validation['valid']:
            ModernMessageBox.warning(
                self,
                "Geçersiz Giriş",
                validation['message']
            )
            return

        # Collect parameters
        params = self._collect_parameters()

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setVisible(True)
        self.progress_label.setText("Sınav programı oluşturuluyor...")
        self.create_btn.setEnabled(False)

        # Start thread
        use_multiple = params.get('use_multiple_attempts', True)
        self.planning_thread = SinavPlanlamaThread(params, use_multiple)
        self.planning_thread.progress.connect(self.on_planning_progress)
        self.planning_thread.finished.connect(self.on_planning_finished)
        self.planning_thread.error.connect(self.on_planning_error)
        self.planning_thread.start()

    def _validate_inputs(self) -> dict:
        """Validate user inputs"""
        if self.baslangic_tarih.dateTime() >= self.bitis_tarih.dateTime():
            return {
                'valid': False,
                'message': "Bitiş tarihi başlangıçtan sonra olmalıdır!"
            }

        allowed_weekdays = [
            day for day, checkbox in self.gun_checkboxes.items()
            if checkbox.isChecked()
        ]
        if not allowed_weekdays:
            return {
                'valid': False,
                'message': "En az bir gün seçmelisiniz!"
            }

        selected_ders_ids = [
            ders_id for ders_id, checkbox in self.ders_checkboxes.items()
            if checkbox.isChecked()
        ]
        if not selected_ders_ids:
            return {
                'valid': False,
                'message': "En az bir ders seçmelisiniz!"
            }

        return {'valid': True}

    def _collect_parameters(self) -> dict:
        """Collect all parameters from UI"""
        selected_ders_ids = [
            ders_id for ders_id, checkbox in self.ders_checkboxes.items()
            if checkbox.isChecked()
        ]

        ders_sureleri = {}
        for ders_id, spinbox in self.ders_duration_spinboxes.items():
            if ders_id in selected_ders_ids:
                ders_sureleri[ders_id] = spinbox.value()

        allowed_weekdays = [
            day for day, checkbox in self.gun_checkboxes.items()
            if checkbox.isChecked()
        ]

        ilk_sinav = f"{self.ilk_sinav_saat.value():02d}:{self.ilk_sinav_dakika.value():02d}"
        son_sinav = f"{self.son_sinav_saat.value():02d}:{self.son_sinav_dakika.value():02d}"
        ogle_baslangic = f"{self.ogle_baslangic_saat.value():02d}:{self.ogle_baslangic_dakika.value():02d}"
        ogle_bitis = f"{self.ogle_bitis_saat.value():02d}:{self.ogle_bitis_dakika.value():02d}"
        
        # Calculate number of available days for diagnostic purposes
        from datetime import timedelta
        start_date = self.baslangic_tarih.dateTime().toPython()
        end_date = self.bitis_tarih.dateTime().toPython()
        days_count = 0
        current = start_date
        while current <= end_date:
            if current.weekday() in allowed_weekdays:
                days_count += 1
            current += timedelta(days=1)

        return {
            'bolum_id': self.bolum_id,
            'sinav_tipi': self.sinav_tipi_combo.currentText(),
            'baslangic_tarih': self.baslangic_tarih.dateTime().toPython(),
            'bitis_tarih': self.bitis_tarih.dateTime().toPython(),
            'varsayilan_sinav_suresi': self.sinav_suresi.value(),
            'ara_suresi': self.ara_suresi.value(),
            'allowed_weekdays': allowed_weekdays,
            'selected_ders_ids': selected_ders_ids,
            'gunluk_ilk_sinav': ilk_sinav,
            'gunluk_son_sinav': son_sinav,
            'ogle_arasi_baslangic': ogle_baslangic,
            'ogle_arasi_bitis': ogle_bitis,
            'no_parallel_exams': self.ayni_anda_sinav_checkbox.isChecked(),
            'class_per_day_limit': self.gunluk_sinav_limiti.value(),
            'student_per_day_limit': self.ogrenci_gunluk_limiti.value(),
            'ders_sinavlari_suresi': ders_sureleri,
            'max_attempts': 300,  # Increased for better optimization
            'use_multiple_attempts': True,
            'days_count': days_count,  # For diagnostic error messages
            'randomize': False  # Deterministic results for same inputs by default
        }

    def on_planning_progress(self, percent, message):
        """Update planning progress"""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(message)

    def on_planning_finished(self, result):
        """Handle planning completion"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.create_btn.setEnabled(True)

        if hasattr(self, 'planning_thread') and self.planning_thread:
            self.planning_thread.quit()
            self.planning_thread.wait()
            self.planning_thread = None

        if not result.get('success'):
            self._show_error(result)
            return

        schedule = result.get('schedule', [])
        if not schedule:
            QMessageBox.warning(self, "Uyarı", "Boş program oluşturuldu!")
            return

        self._show_result_dialog(result)

    def on_planning_error(self, error_msg):
        """Handle planning error"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.create_btn.setEnabled(True)

        if hasattr(self, 'planning_thread') and self.planning_thread:
            self.planning_thread.quit()
            self.planning_thread.wait()
            self.planning_thread = None

        QMessageBox.critical(self, "Hata", f"Planlama hatası:\n{error_msg}")

    def _show_result_dialog(self, result: dict):
        """Show result dialog with scoring details"""
        params = {
            'bolum_id': self.bolum_id,
            'sinav_tipi': self.sinav_tipi_combo.currentText()
        }

        dialog = ProgramResultDialog(
            schedule_data=result['schedule'],
            params=params,
            score_result=result.get('score_details'),
            parent=self
        )

        dialog_result = dialog.exec()

        if dialog_result:
            self.load_existing_programs()
            refresh_main_window_ui(self)

    def _show_error(self, result: dict):
        """Show error message with ModernMessageBox"""
        message = result.get('message', 'Program oluşturulamadı!')
        details = result.get('details', '')
        suggestions = result.get('suggestions', [])
        
        # Build full error message
        full_message = ""
        
        if details:
            full_message += f"{details}\n\n"
        
        if suggestions:
            full_message += "💡 Öneriler:\n"
            for suggestion in suggestions:
                full_message += f"{suggestion}\n"
        
        # Fallback if no details
        if not full_message:
            warnings = result.get('warnings', [])
            full_message = "\n".join(warnings) if warnings else "Detay bilgi bulunmuyor"
        
        ModernMessageBox.error(
            self,
            "Sınav Programı Oluşturulamadı",
            message,
            full_message.strip()
        )

    def load_existing_programs(self):
        """Load and display existing programs"""
        try:
            programs = self.controller.get_programs_by_bolum(self.bolum_id)

            self.programs_table.setRowCount(0)

            for program in programs:
                row = self.programs_table.rowCount()
                self.programs_table.insertRow(row)
                self.programs_table.setRowHeight(row, 55)  # Orta boy satır yüksekliği

                sinavlar = self.controller.get_schedule_by_program(program['program_id'])
                exam_count = len(set((s['ders_id'], s.get('tarih_saat')) for s in sinavlar))

                self.programs_table.setItem(row, 0, QTableWidgetItem(program['program_adi']))
                self.programs_table.setItem(row, 1, QTableWidgetItem(program.get('sinav_tipi', 'Final')))
                self.programs_table.setItem(row, 2, QTableWidgetItem(str(program.get('baslangic_tarihi', ''))))
                self.programs_table.setItem(row, 3, QTableWidgetItem(str(program.get('bitis_tarihi', ''))))

                count_item = QTableWidgetItem(str(exam_count))
                count_item.setTextAlignment(Qt.AlignCenter)
                self.programs_table.setItem(row, 4, count_item)

                actions_widget = self._create_action_buttons(program)
                self.programs_table.setCellWidget(row, 5, actions_widget)

            logger.info(f"Loaded {len(programs)} exam programs")

        except Exception as e:
            logger.error(f"Error loading programs: {e}", exc_info=True)
            QMessageBox.critical(self, "Hata", f"Programlar yüklenirken hata:\n{str(e)}")

    def _create_action_buttons(self, program: dict) -> QWidget:
        """Create action buttons for program row"""
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(2, 2, 2, 2)
        actions_layout.setSpacing(10)

        # Buton stili: ders_yukle sayfasının gradient-temalı butonlarına uyumlu
        btn_style_view = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: 700;
                font-size: 12px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb, stop:1 #1d4ed8);
            }
            QPushButton:pressed {
                background: #1e40af;
            }
        """

        btn_style_excel = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #10b981, stop:1 #059669);
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: 700;
                font-size: 12px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #059669, stop:1 #047857);
            }
        """

        btn_style_pdf = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: 700;
                font-size: 12px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb, stop:1 #1d4ed8);
            }
        """

        btn_style_class = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8b5cf6, stop:1 #7c3aed);
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: 700;
                font-size: 12px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7c3aed, stop:1 #6d28d9);
            }
        """

        btn_style_delete = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ef4444, stop:1 #dc2626);
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: 700;
                font-size: 12px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc2626, stop:1 #b91c1c);
            }
        """

        view_btn = QPushButton("👁️ Görüntüle")
        view_btn.setFixedHeight(34)
        view_btn.setMinimumWidth(110)
        view_btn.setCursor(Qt.PointingHandCursor)
        view_btn.setStyleSheet(btn_style_view)
        view_btn.clicked.connect(lambda: self.view_program(program))
        actions_layout.addWidget(view_btn)

        excel_btn = QPushButton("📊 Excel")
        excel_btn.setFixedHeight(34)
        excel_btn.setMinimumWidth(100)
        excel_btn.setCursor(Qt.PointingHandCursor)
        excel_btn.setStyleSheet(btn_style_excel)
        excel_btn.clicked.connect(lambda: self.export_program(program, 'excel'))
        actions_layout.addWidget(excel_btn)

        pdf_btn = QPushButton("📄 PDF")
        pdf_btn.setFixedHeight(34)
        pdf_btn.setMinimumWidth(90)
        pdf_btn.setCursor(Qt.PointingHandCursor)
        pdf_btn.setStyleSheet(btn_style_pdf)
        pdf_btn.clicked.connect(lambda: self.export_program(program, 'pdf'))
        actions_layout.addWidget(pdf_btn)

        class_btn = QPushButton("🎓 Sınıf")
        class_btn.setFixedHeight(34)
        class_btn.setMinimumWidth(90)
        class_btn.setCursor(Qt.PointingHandCursor)
        class_btn.setStyleSheet(btn_style_class)
        class_btn.clicked.connect(lambda: self.export_program(program, 'class'))
        actions_layout.addWidget(class_btn)

        delete_btn = QPushButton("🗑️ Sil")
        delete_btn.setFixedHeight(34)
        delete_btn.setFixedWidth(70)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet(btn_style_delete)
        delete_btn.clicked.connect(lambda: self.delete_program(program))
        actions_layout.addWidget(delete_btn)

        actions_layout.addStretch()

        # Ekran genişliğine göre buton yazı boyutunu kompaktlaştır


        return actions_widget

    def _fit_actions_widget(self, actions_widget: QWidget):
        """Reduce button font-size progressively if buttons overflow the actions column."""
        try:
            col_index = 5
            available = self.programs_table.columnWidth(col_index)
            layout = actions_widget.layout()
            margins = layout.contentsMargins()
            spacing = layout.spacing()

            def total_width():
                width = margins.left() + margins.right()
                btns = [layout.itemAt(i).widget() for i in range(layout.count()) if layout.itemAt(i) and layout.itemAt(i).widget() and isinstance(layout.itemAt(i).widget(), QPushButton)]
                if not btns:
                    return 0
                width += sum(btn.sizeHint().width() for btn in btns)
                width += spacing * (len(btns) - 1)
                return width

            # Try normal -> small -> smaller
            if total_width() > available:
                for px in (11, 10, 9):
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        w = item.widget() if item else None
                        if w and isinstance(w, QPushButton):
                            # Append a smaller font-size override
                            w.setStyleSheet(w.styleSheet() + f"\nQPushButton {{ font-size: {px}px; padding: 2px 6px; }}")
                    # Recalculate with smaller font
                    if total_width() <= available:
                        break
        except Exception as e:
            logger.warning(f"Actions widget fit adjustment failed: {e}")

    def _on_programs_section_resized(self, logicalIndex: int, oldSize: int, newSize: int):
        """When the actions column width changes, re-fit buttons to avoid overlap."""
        try:
            if logicalIndex != 5:
                return
            row_count = self.programs_table.rowCount()
            for row in range(row_count):
                w = self.programs_table.cellWidget(row, 5)
                if w:
                    self._fit_actions_widget(w)
        except Exception as e:
            logger.warning(f"Section resize handling failed: {e}")

    def view_program(self, program: dict):
        """View program in result dialog (directly open result view)"""
        try:
            schedule = self.controller.get_schedule_by_program(program['program_id'])

            if not schedule:
                ModernMessageBox.warning(
                    self,
                    "Uyarı",
                    "Bu programa ait sınav bulunamadı!"
                )
                return

            # Bu program için puanlama verilerini hesapla (mevcut programlar için de puanlı görünüm)
            ders_ids = {item['ders_id'] for item in schedule if 'ders_id' in item}

            course_students = {}
            course_info = {}

            for ders_id in ders_ids:
                try:
                    ogrenciler = self.ogrenci_model.get_ogrenciler_by_ders(ders_id)
                    student_ids = set(o['ogrenci_no'] for o in ogrenciler)
                    course_students[ders_id] = student_ids

                    ders_detay = self.ders_model.get_ders_by_id(ders_id) or {}
                    course_info[ders_id] = {
                        'ders_kodu': ders_detay.get('ders_kodu', str(ders_id)),
                        'ders_adi': ders_detay.get('ders_adi', ''),
                        'sinif': ders_detay.get('sinif', 0),
                        'ogrenci_sayisi': len(student_ids)
                    }
                except Exception as e:
                    logger.warning(f"Course data load failed for ders_id={ders_id}: {e}")

            # Mevcut programı değerlendirirken, "Yeni Program Oluştur" sürecinde kullanılan
            # puanlama parametrelerinin aynısını kullan (UI'daki mevcut ayarlar).
            scorer = SinavProgramScorer()
            score_params = {
                'bolum_id': self.bolum_id,
                'sinav_tipi': program.get('sinav_tipi', 'Final'),
                'ara_suresi': getattr(self, 'ara_suresi', None).value() if hasattr(self, 'ara_suresi') else 15,
                'class_per_day_limit': getattr(self, 'gunluk_sinav_limiti', None).value() if hasattr(self, 'gunluk_sinav_limiti') else 3,
                'student_per_day_limit': getattr(self, 'ogrenci_gunluk_limiti', None).value() if hasattr(self, 'ogrenci_gunluk_limiti') else 1,
            }
            score_result = scorer.score_schedule(schedule, course_students, course_info, score_params)
            
            if isinstance(score_result, dict):
                score_result = score_result.copy()
                score_result['best_attempt'] = 1
                score_result['total_attempts'] = 1
                score_result['strategy_used'] = 'Kaydedilmiş Program'

            # Puanlı result dialog'u aç
            dialog = ProgramResultDialog(
                schedule_data=schedule,
                params={'bolum_id': self.bolum_id, 'sinav_tipi': program.get('sinav_tipi', 'Final')},
                score_result=score_result,
                parent=self
            )
            dialog.exec()

        except Exception as e:
            logger.error(f"Error viewing program: {e}", exc_info=True)
            ModernMessageBox.error(
                self,
                "Hata",
                "Program görüntülenirken hata oluştu.",
                str(e)
            )

    def export_program(self, program: dict, export_type: str):
        """Export program to Excel / PDF / Class-based"""
        try:
            schedule = self.controller.get_schedule_by_program(program['program_id'])

            if not schedule:
                ModernMessageBox.warning(
                    self,
                    "Uyarı",
                    "Bu programa ait sınav bulunamadı!"
                )
                return

            program_name = sanitize_filename(program['program_adi'])
            
            # Bölüm adını al (program dict'inde yoksa BolumModel'den çek)
            bolum_adi = program.get('bolum_adi', '')
            if not bolum_adi:
                from models.bolum_model import BolumModel
                bolum_model = BolumModel(db)
                bolum = bolum_model.get_bolum_by_id(self.bolum_id)
                bolum_adi = bolum.get('bolum_adi', 'Bölüm') if bolum else 'Bölüm'
            
            sinav_tipi = program.get('sinav_tipi', 'Sınav')
            
            # Dosya ismi için bölüm ve sınav tipi ekle
            bolum_safe = sanitize_filename(bolum_adi)
            sinav_tipi_safe = sanitize_filename(sinav_tipi)
            file_prefix = f"{bolum_safe}_{sinav_tipi_safe}_Sinav_Programi"

            # Ortak export data yapısı (Excel ve PDF için)
            export_data = {
                'type': 'sinav_takvimi',
                'title': 'Sınav Programı',
                'data': schedule,
                'bolum_adi': bolum_adi,
                'sinav_tipi': sinav_tipi,
            }

            # === EXCEL EXPORT ===
            if export_type == 'excel':
                filename = f"{file_prefix}.xlsx"
                filepath = QFileDialog.getSaveFileName(
                    self,
                    "Excel Kaydet",
                    filename,
                    "Excel Files (*.xlsx)"
                )[0]

                if filepath:
                    result = ExportUtils.export_to_excel(export_data, filepath)
                    if result:
                        ModernMessageBox.success(
                            self,
                            "Başarılı",
                            "Excel dosyası oluşturuldu!",
                            filepath
                        )
                    else:
                        ModernMessageBox.error(
                            self,
                            "Hata",
                            "Excel dosyası oluşturulamadı!"
                        )

            # === PDF EXPORT ===
            elif export_type == 'pdf':
                filename = f"{file_prefix}.pdf"
                filepath = QFileDialog.getSaveFileName(
                    self,
                    "PDF Kaydet",
                    filename,
                    "PDF Files (*.pdf)"
                )[0]

                if filepath:
                    result = ExportUtils.export_to_pdf(export_data, filepath)
                    if result:
                        ModernMessageBox.success(
                            self,
                            "Başarılı",
                            "PDF dosyası oluşturuldu!",
                            filepath
                        )
                    else:
                        ModernMessageBox.error(
                            self,
                            "Hata",
                            "PDF dosyası oluşturulamadı!"
                        )

            # === CLASS-BASED EXPORT ===
            elif export_type == 'class':
                folder_path = QFileDialog.getExistingDirectory(
                    self,
                    "Klasör Seç",
                    "",
                    QFileDialog.ShowDirsOnly
                )

                if folder_path:
                    result = ExportUtils.export_by_class(
                        schedule, 
                        folder_path, 
                        file_prefix,
                        bolum_adi=bolum_adi,
                        sinav_tipi=sinav_tipi
                    )
                    if isinstance(result, dict) and result.get('success'):
                        ModernMessageBox.success(
                            self,
                            "Başarılı",
                            f"{result.get('class_count', 0)} sınıf için dosyalar oluşturuldu!",
                            folder_path
                        )
                    else:
                        ModernMessageBox.error(
                            self,
                            "Hata",
                            "Sınıf bazlı dosyalar oluşturulamadı!"
                        )

        except Exception as e:
            logger.error(f"Export error: {e}", exc_info=True)
            ModernMessageBox.error(
                self,
                "Dışa Aktarma Hatası",
                "Dosya oluşturulurken hata oluştu.",
                str(e)
            )

    def delete_program(self, program: dict):
        """Delete exam program"""
        try:
            from utils.modern_dialogs import ModernMessageBox

            reply = ModernMessageBox.question(
                self,
                "Silme Onayı",
                f"'{program['program_adi']}' programını silmek istediğinizden emin misiniz?",
                "Bu işlem geri alınamaz!"
            )

            if reply:
                result = self.controller.delete_program(program['program_id'])

                if result['success']:
                    ModernMessageBox.success(
                        self,
                        "Başarılı",
                        result['message']
                    )
                    self.load_existing_programs()
                    refresh_main_window_ui(self)
                else:
                    ModernMessageBox.warning(
                        self,
                        "Uyarı",
                        result['message']
                    )

        except Exception as e:
            logger.error(f"Delete error: {e}", exc_info=True)
            ModernMessageBox.error(
                self,
                "Silme Hatası",
                "Program silinirken hata oluştu.",
                str(e)
            )
