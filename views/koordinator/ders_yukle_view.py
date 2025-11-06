"""
Ders Yükleme (Course Upload) View
Professional interface for uploading and managing courses from Excel
"""

import logging

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QFileDialog, QGroupBox, QSplitter, QComboBox, QDialog
)

from controllers.ders_controller import DersController
from models.database import db
from models.ders_model import DersModel
from models.ogrenci_model import OgrenciModel
from utils.excel_parser import ExcelParser
from utils.modern_dialogs import ModernMessageBox
from utils.view_helpers import refresh_main_window_ui

logger = logging.getLogger(__name__)


class ExcelLoadThread(QThread):
    """Thread for loading Excel file"""
    progress = Signal(int)
    finished = Signal(list)
    error = Signal(str)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
    
    def run(self):
        try:
            parser = ExcelParser()
            dersler = parser.parse_ders_listesi(self.file_path)
            self.finished.emit(dersler)
        except Exception as e:
            self.error.emit(str(e))


class DersYukleView(QWidget):
    """Course upload and management view"""
    
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.bolum_id = user_data.get('bolum_id', 1)
        
        self.ders_model = DersModel(db)
        self.ogrenci_model = OgrenciModel(db)
        self.ders_controller = DersController(self.ders_model)
        
        self.pending_dersler = []
        
        self.setup_ui()
        self.load_existing_dersler()
    
    def setup_ui(self):
        """Setup UI - table first, info last"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Compact Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Ders Listesi")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        
        upload_btn = QPushButton("📤 Excel Yükle")
        upload_btn.setObjectName("primaryBtn")
        upload_btn.setFixedHeight(36)
        upload_btn.setMinimumWidth(140)
        upload_btn.setCursor(Qt.PointingHandCursor)
        upload_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb, stop:1 #1d4ed8);
            }
            QPushButton:pressed {
                background: #1e40af;
            }
        """)
        upload_btn.clicked.connect(self.upload_excel)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(upload_btn)
        
        layout.addWidget(header)
        
        # Modern Filter section with frame
        filter_container = QFrame()
        filter_container.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 8px;
            }
        """)
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(12)
        
        filter_icon = QLabel("🎓")
        filter_icon.setFont(QFont("Segoe UI", 14))
        filter_icon.setStyleSheet("background: transparent;")
        
        filter_label = QLabel("Sınıf Filtresi:")
        filter_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 13px; 
            color: #1e293b;
            background: transparent;
        """)
        
        self.class_filter = QComboBox()
        self.class_filter.addItems([
            "Tüm Dersler",
            "1. Sınıf",
            "2. Sınıf", 
            "3. Sınıf",
            "4. Sınıf",
            "Seçmeli Dersler"
        ])
        self.class_filter.setFixedHeight(40)
        self.class_filter.setMinimumWidth(220)
        self.class_filter.setStyleSheet("""
            QComboBox {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                background: white;
                color: #1e293b;
            }
            QComboBox:focus {
                border: 2px solid #3b82f6;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #64748b;
                margin-right: 8px;
            }
        """)
        self.class_filter.currentTextChanged.connect(self.filter_by_class)
        
        filter_layout.addWidget(filter_icon)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.class_filter)
        filter_layout.addStretch()
        
        layout.addWidget(filter_container)
        
        # Splitter for courses and students
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Courses table
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)  # Added column for Zorunlu/Seçmeli
        self.table.setHorizontalHeaderLabels([
            "DERS KODU", "DERSİN ADI", "DERSİ VEREN ÖĞR. ELEMANI", "SINIF", "TÜR"
        ])
        
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.show_course_students)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)     # DERS KODU
        header.setSectionResizeMode(1, QHeaderView.Stretch)   # DERSİN ADI
        header.setSectionResizeMode(2, QHeaderView.Stretch)   # ÖĞR. ELEMANI
        header.setSectionResizeMode(3, QHeaderView.Fixed)     # SINIF
        header.setSectionResizeMode(4, QHeaderView.Fixed)     # TÜR
        
        self.table.setColumnWidth(0, 100)  # DERS KODU
        self.table.setColumnWidth(3, 60)   # SINIF
        self.table.setColumnWidth(4, 90)   # TÜR
        
        left_layout.addWidget(self.table)
        
        # Course action buttons
        course_actions = QHBoxLayout()
        course_actions.setSpacing(8)
        
        select_all_btn = QPushButton("✓ Tümünü Seç")
        select_all_btn.setFixedHeight(34)
        select_all_btn.setCursor(Qt.PointingHandCursor)
        select_all_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #10b981, stop:1 #059669);
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: 600;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #059669, stop:1 #047857);
            }
        """)
        select_all_btn.clicked.connect(self.select_all_courses)
        
        deselect_all_btn = QPushButton("✗ Seçimi Kaldır")
        deselect_all_btn.setFixedHeight(34)
        deselect_all_btn.setCursor(Qt.PointingHandCursor)
        deselect_all_btn.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: 600;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: #4b5563;
            }
        """)
        deselect_all_btn.clicked.connect(self.deselect_all_courses)
        
        edit_course_btn = QPushButton("✎ Düzenle")
        edit_course_btn.setFixedHeight(34)
        edit_course_btn.setCursor(Qt.PointingHandCursor)
        edit_course_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f59e0b, stop:1 #d97706);
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: 600;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d97706, stop:1 #b45309);
            }
        """)
        edit_course_btn.clicked.connect(self.edit_selected_course)
        
        delete_course_btn = QPushButton("🗑 Sil")
        delete_course_btn.setFixedHeight(34)
        delete_course_btn.setCursor(Qt.PointingHandCursor)
        delete_course_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ef4444, stop:1 #dc2626);
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: 600;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc2626, stop:1 #b91c1c);
            }
        """)
        delete_course_btn.clicked.connect(self.delete_selected_courses)
        
        course_actions.addWidget(select_all_btn)
        course_actions.addWidget(deselect_all_btn)
        course_actions.addWidget(edit_course_btn)
        course_actions.addWidget(delete_course_btn)
        course_actions.addStretch()
        
        left_layout.addLayout(course_actions)
        splitter.addWidget(left_widget)
        
        # Right side - Students table
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        students_header = QLabel("👥 Dersi Alan Öğrenciler")
        students_header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        students_header.setStyleSheet("padding: 8px; background-color: #f3f4f6; border-radius: 4px;")
        right_layout.addWidget(students_header)
        
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(3)
        self.students_table.setHorizontalHeaderLabels(["Öğrenci No", "Ad Soyad", "Sınıf"])
        self.students_table.verticalHeader().setVisible(False)
        self.students_table.setAlternatingRowColors(True)
        self.students_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        students_header_view = self.students_table.horizontalHeader()
        students_header_view.setSectionResizeMode(0, QHeaderView.Fixed)
        students_header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        students_header_view.setSectionResizeMode(2, QHeaderView.Fixed)
        
        self.students_table.setColumnWidth(0, 100)
        self.students_table.setColumnWidth(2, 60)
        
        right_layout.addWidget(self.students_table)
        
        self.students_stats = QLabel("Bir ders seçin")
        self.students_stats.setStyleSheet("color: #6b7280; font-size: 11px; padding: 8px;")
        right_layout.addWidget(self.students_stats)
        
        splitter.addWidget(right_widget)
        
        # Set splitter proportions (60% courses, 40% students)
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)
        
        layout.addWidget(splitter, stretch=1)  # Give most space to table
        
        # Bottom section with stats and info
        bottom_container = QFrame()
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 8, 0, 0)
        bottom_layout.setSpacing(12)
        
        # Stats group box
        stats_group = QGroupBox("📊 İstatistikler")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #1f2937;
                border: 2px solid #3b82f6;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                background: white;
            }
        """)
        stats_group_layout = QVBoxLayout(stats_group)
        stats_group_layout.setContentsMargins(12, 8, 12, 12)
        
        self.stats_label = QLabel()
        self.stats_label.setFont(QFont("Segoe UI", 11))
        self.stats_label.setStyleSheet("color: #374151; padding: 4px;")
        stats_group_layout.addWidget(self.stats_label)
        
        # Info group box
        info_group = QGroupBox("💡 Excel Format Bilgisi")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #92400e;
                border: 2px solid #f59e0b;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background: #fef3c7;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                background: #fef3c7;
            }
        """)
        info_group_layout = QVBoxLayout(info_group)
        info_group_layout.setContentsMargins(12, 8, 12, 12)
        
        info_text = QLabel(
            "<b>Sütunlar:</b> DERS KODU • DERSİN ADI • DERSİ VEREN ÖĞR. ELEMANI<br>"
            "<b>Sınıf Bilgisi:</b> Excel'de sınıf başlıkları kullanın (1. Sınıf, 2. Sınıf, vb.)"
        )
        info_text.setStyleSheet("color: #92400e; font-size: 11px;")
        info_text.setWordWrap(True)
        info_group_layout.addWidget(info_text)
        
        bottom_layout.addWidget(stats_group)
        bottom_layout.addWidget(info_group, stretch=1)
        
        layout.addWidget(bottom_container)
        
        # Store all courses
        self.all_courses = []
    
    def filter_by_class(self, filter_text):
        """Filter courses by class - Excel başlıklarından alınan sınıf bilgisi ile"""
        if not self.all_courses:
            return
        
        filtered_courses = []
        
        if filter_text == "Tüm Dersler":
            filtered_courses = self.all_courses
        elif filter_text == "1. Sınıf":
            filtered_courses = [d for d in self.all_courses if d.get('sinif', 0) == 1]
        elif filter_text == "2. Sınıf":
            filtered_courses = [d for d in self.all_courses if d.get('sinif', 0) == 2]
        elif filter_text == "3. Sınıf":
            filtered_courses = [d for d in self.all_courses if d.get('sinif', 0) == 3]
        elif filter_text == "4. Sınıf":
            filtered_courses = [d for d in self.all_courses if d.get('sinif', 0) == 4]
        elif filter_text == "Seçmeli Dersler":
            filtered_courses = [d for d in self.all_courses if d.get('ders_yapisi', '') == 'Seçmeli']
        
        # Display filtered results without updating all_courses
        self.display_courses(filtered_courses)
    
    def load_existing_dersler(self):
        """Load existing courses"""
        try:
            dersler = self.ders_model.get_dersler_by_bolum(self.bolum_id)
            
            # Reset filter to show all courses
            if hasattr(self, 'class_filter'):
                self.class_filter.blockSignals(True)
                self.class_filter.setCurrentIndex(0)  # "Tüm Dersler"
                self.class_filter.blockSignals(False)
            
            self.populate_table(dersler, existing=True)
            self.update_stats(len(dersler), 0)
            
            logger.info(f"Loaded {len(dersler)} courses from database")
        except Exception as e:
            logger.error(f"Error loading courses: {e}")
            ModernMessageBox.error(self, "Hata", "Dersler yüklenirken oluştu", f"{str(e)}")
    
    def display_courses(self, dersler):
        """Display courses in table without updating all_courses"""
        self.table.setRowCount(0)
        
        for row, ders in enumerate(dersler):
            self.table.insertRow(row)
            
            # DERS KODU
            kod_item = QTableWidgetItem(str(ders.get('ders_kodu', '')))
            self.table.setItem(row, 0, kod_item)
            
            # DERSİN ADI
            adi_item = QTableWidgetItem(str(ders.get('ders_adi', '')))
            self.table.setItem(row, 1, adi_item)
            
            # DERSİ VEREN ÖĞR. ELEMANI
            ogretim_elemani = str(ders.get('ogretim_elemani', '-'))
            elem_item = QTableWidgetItem(ogretim_elemani)
            self.table.setItem(row, 2, elem_item)
            
            # SINIF
            sinif = ders.get('sinif', 0)
            sinif_text = f"{sinif}. Sınıf" if sinif > 0 else "-"
            sinif_item = QTableWidgetItem(sinif_text)
            sinif_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, sinif_item)
            
            # TÜR (Zorunlu/Seçmeli)
            ders_yapisi = ders.get('ders_yapisi', 'Zorunlu')
            tur_item = QTableWidgetItem(ders_yapisi)
            tur_item.setTextAlignment(Qt.AlignCenter)
            
            # Color code based on type
            if ders_yapisi == 'Seçmeli':
                tur_item.setForeground(QColor('#f59e0b'))  # Orange for elective
                tur_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            else:
                tur_item.setForeground(QColor('#059669'))  # Green for mandatory
            
            self.table.setItem(row, 4, tur_item)
    
    def populate_table(self, dersler, existing=False):
        """Populate table with course data and update all_courses if from database"""
        # Update all_courses only when loading from database
        if existing:
            self.all_courses = dersler
        
        # Display the courses
        self.display_courses(dersler)
    
    def upload_excel(self):
        """Upload Excel file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Excel Dosyası Seç",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        
        if file_path:
            self.load_excel(file_path)
    
    def load_excel(self, file_path):
        """Load Excel file in background thread"""
        self.thread = ExcelLoadThread(file_path)
        self.thread.finished.connect(self.on_excel_loaded)
        self.thread.error.connect(self.on_excel_error)
        self.thread.start()
    
    def on_excel_loaded(self, dersler):
        """Handle loaded Excel data with validation summary"""
        if not dersler:
            ModernMessageBox.warning(self, "Uyarı", "Excel dosyasında ders bulunamadı!")
            return
        
        # Check for existing courses
        existing_count = 0
        new_count = 0
        existing_details = []
        
        for idx, ders in enumerate(dersler, start=1):
            excel_row = idx + 1  # +1 for header row
            existing = self.ders_model.get_ders_by_kod(self.bolum_id, ders.get('ders_kodu', ''))
            if existing:
                existing_count += 1
                existing_details.append(
                    f"Satır {excel_row}: {ders.get('ders_kodu')} - {ders.get('ders_adi')} - {ders.get('sinif', '?')}. Sınıf"
                )
            else:
                new_count += 1
        
        self.pending_dersler = dersler
        # Display pending courses (don't update all_courses until saved)
        self.display_courses(dersler)
        self.update_stats(len(self.all_courses), len(dersler))
        
        # Show summary with existing course info
        summary_msg = f"📚 Excel'den {len(dersler)} ders yüklendi\n\n"
        summary_msg += f"✅ Yeni ders: {new_count}\n"
        summary_msg += f"⚠️ Zaten mevcut: {existing_count}"
        
        if existing_count > 0:
            summary_msg += f"\n\n❓ Mevcut dersler atlanacak. Devam edilsin mi?"
        else:
            summary_msg += f"\n\nVeritabanına kaydetmek istiyor musunuz?"
        
        # Prepare details text
        details_text = ""
        if existing_count > 0:
            details_text = "⚠️ MEVCUT DERSLER (Atlanacak):\n\n" + "\n".join(existing_details[:15])
            if len(existing_details) > 15:
                details_text += f"\n\n... ve {len(existing_details) - 15} ders daha"
        
        # Ask for confirmation
        confirmed = ModernMessageBox.question(
            self,
            "Dersleri Kaydet",
            summary_msg,
            details_text  # Empty string is OK, no need for conditional
        )

        if confirmed:
            self.save_dersler(skip_existing=True)
    
    def on_excel_error(self, error_msg):
        """Handle Excel loading error with detailed information"""
        # Parse error message to provide better formatting
        if "❌" in error_msg:
            # Formatted error from parser (e.g., format errors, missing columns)
            ModernMessageBox.error(
                self,
                "Excel Format Hatası",
                "Excel formatı hatalı veya gerekli sütunlar eksik.",
                error_msg
            )
        elif "Satır" in error_msg and error_msg.count("Satır") > 3:
            # Multiple row errors - show summary
            row_count = error_msg.count("Satır")
            detailed_text = error_msg.replace("Satır ", "\n• Satır ")
            
            ModernMessageBox.error(
                self,
                "Excel Yükleme Hatası",
                f"Excel'de {row_count} satırda hata bulundu!\n\n"
                "Lütfen Excel dosyasını kontrol edin ve düzeltip tekrar yükleyin.",
                detailed_text
            )
        else:
            # Generic or single error
            ModernMessageBox.error(
                self,
                "Excel Yükleme Hatası",
                "Excel dosyası yüklenirken bir hata oluştu.",
                error_msg
            )
    
    def save_dersler(self, skip_existing=True):
        """Save courses to database with detailed error reporting"""
        if not self.pending_dersler:
            return
        
        try:
            success_count = 0
            skipped_count = 0
            error_count = 0
            error_details = []
            skipped_details = []
            
            for idx, ders in enumerate(self.pending_dersler, 1):
                excel_row = idx + 1  # Account for header row
                ders['bolum_id'] = self.bolum_id
                
                # Check if course already exists
                if skip_existing:
                    existing = self.ders_model.get_ders_by_kod(self.bolum_id, ders.get('ders_kodu', ''))
                    if existing:
                        skipped_count += 1
                        skipped_details.append(f"Satır {excel_row}: {ders.get('ders_kodu')} - {ders.get('ders_adi')}")
                        logger.info(f"Skipped existing course at row {excel_row}: {ders.get('ders_kodu')}")
                        continue
                
                result = self.ders_controller.create_ders(ders)
                
                if result['success']:
                    success_count += 1
                else:
                    error_count += 1
                    # Track which row failed
                    error_msg = f"Satır {excel_row} ({ders.get('ders_kodu', '?')} - {ders.get('ders_adi', '?')}): {result['message']}"
                    error_details.append(error_msg)
                    logger.warning(error_msg)
            
            # Show detailed results
            result_message = []
            if success_count > 0:
                result_message.append(f"✅ {success_count} yeni ders kaydedildi")
            if skipped_count > 0:
                result_message.append(f"⏭️ {skipped_count} mevcut ders atlandı")
            if error_count > 0:
                result_message.append(f"❌ {error_count} ders kaydedilemedi")
            
            # Prepare detailed text
            detailed_parts = []
            
            if skipped_count > 0:
                skipped_text = "⏭️ ATLANAN DERSLER:\n" + "\n".join(skipped_details[:15])
                if len(skipped_details) > 15:
                    skipped_text += f"\n... ve {len(skipped_details) - 15} ders daha"
                detailed_parts.append(skipped_text)
            
            if error_count > 0:
                error_text = "❌ HATA OLUŞAN KAYITLAR:\n" + "\n".join(error_details[:15])
                if len(error_details) > 15:
                    error_text += f"\n... ve {len(error_details) - 15} hata daha"
                detailed_parts.append(error_text)
            
            detailed_text = "\n\n".join(detailed_parts) if detailed_parts else None
            
            if error_count > 0:
                ModernMessageBox.warning(
                    self,
                    "Kaydetme Sonuçları",
                    "\n".join(result_message),
                    detailed_text
                )
            else:
                message = "\n".join(result_message)
                if skipped_count > 0 and success_count == 0:
                    ModernMessageBox.information(
                        self, 
                        "Bilgi", 
                        "Tüm dersler zaten veritabanında mevcut.\n\n"
                        f"{skipped_count} ders atlandı.",
                        detailed_text
                    )
                else:
                    ModernMessageBox.success(
                        self, "Başarılı", message
                    )
            
            self.pending_dersler = []
            self.load_existing_dersler()
            
            # Refresh main window UI (menus and shortcuts) if courses were added
            if success_count > 0:
                refresh_main_window_ui(self)
            
        except Exception as e:
            logger.error(f"Error saving courses: {e}", exc_info=True)
            ModernMessageBox.error(self, "Hata", "Dersler kaydedilirken oluştu", f"{str(e)}")
    
    def update_stats(self, existing, pending):
        """Update statistics label"""
        self.stats_label.setText(
            f"📊 Kayıtlı: {existing} | Beklemede: {pending}"
        )
    
    def show_course_students(self):
        """Show students of selected course"""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            self.students_table.setRowCount(0)
            self.students_stats.setText("Bir ders seçin")
            return
        
        row = selected_rows[0].row()
        ders_kodu = self.table.item(row, 0).text()
        ders_adi = self.table.item(row, 1).text()
        
        # Get ders_id from model
        try:
            ders = self.ders_model.get_ders_by_kod(self.bolum_id, ders_kodu)
            if not ders:
                self.students_table.setRowCount(0)
                self.students_stats.setText("❌ Ders bulunamadı")
                return
            
            # Get students taking this course
            ogrenciler = self.ogrenci_model.get_ogrenciler_by_ders(ders['ders_id'])
            
            # Update students table
            self.students_table.setRowCount(0)
            
            if not ogrenciler:
                self.students_stats.setText(f"📚 {ders_kodu} - Kayıtlı öğrenci yok")
            else:
                for row_idx, ogrenci in enumerate(ogrenciler):
                    self.students_table.insertRow(row_idx)
                    
                    no_item = QTableWidgetItem(ogrenci.get('ogrenci_no', ''))
                    ad_item = QTableWidgetItem(ogrenci.get('ad_soyad', ''))
                    sinif_item = QTableWidgetItem(str(ogrenci.get('sinif', '')))
                    sinif_item.setTextAlignment(Qt.AlignCenter)
                    
                    self.students_table.setItem(row_idx, 0, no_item)
                    self.students_table.setItem(row_idx, 1, ad_item)
                    self.students_table.setItem(row_idx, 2, sinif_item)
                
                self.students_stats.setText(f"📚 {ders_kodu} - {len(ogrenciler)} öğrenci")
            
        except Exception as e:
            logger.error(f"Error loading course students: {e}")
            self.students_stats.setText(f"❌ Hata: {str(e)}")
    
    def edit_selected_course(self):
        """Edit selected course with modern dialog"""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            ModernMessageBox.warning(self, "Uyarı", "Lütfen düzenlemek için bir ders seçin!")
            return
        
        # Get course code from table
        row = selected_rows[0].row()
        ders_kodu_item = self.table.item(row, 0)
        if not ders_kodu_item:
            ModernMessageBox.warning(self, "Hata", "Ders kodu bulunamadı!")
            return
        
        ders_kodu = ders_kodu_item.text()
        
        # Get full course data from database
        ders = self.ders_model.get_ders_by_kod(self.bolum_id, ders_kodu)
        if not ders:
            ModernMessageBox.warning(self, "Hata", f"Ders bulunamadı: {ders_kodu}")
            return
        
        # Create modern edit dialog
        from utils.edit_dialogs import DersEditDialog
        
        dialog = DersEditDialog(ders, self.ders_model, self.bolum_id, self)
        
        if dialog.exec() == QDialog.Accepted:
            updated_data = dialog.get_updated_data()
            
            result = self.ders_controller.update_ders(ders['ders_id'], updated_data)
            
            if result['success']:
                ModernMessageBox.success(self, "Başarılı", result['message'])
                self.load_existing_dersler()
                refresh_main_window_ui(self)
            else:
                ModernMessageBox.error(self, "Hata", result['message'])
    
    def select_all_courses(self):
        """Select all courses in table"""
        self.table.selectAll()
    
    def deselect_all_courses(self):
        """Deselect all courses"""
        self.table.clearSelection()
    
    def delete_selected_courses(self):
        """Delete multiple selected courses"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            ModernMessageBox.warning(self, "Uyarı", "Lütfen silmek için en az bir ders seçin!")
            return
        
        # Get course list from selected rows
        course_list = []
        for index in selected_rows:
            row = index.row()
            ders_kodu = self.table.item(row, 0).text() if self.table.item(row, 0) else None
            ders_adi = self.table.item(row, 1).text() if self.table.item(row, 1) else "İsimsiz"
            if ders_kodu:
                course_list.append((ders_kodu, ders_adi))
        
        if not course_list:
            ModernMessageBox.warning(self, "Uyarı", "Silinecek ders bulunamadı!")
            return
        
        confirmed = ModernMessageBox.question(
            self,
            "Dersleri Sil",
            f"{len(course_list)} dersi silmek istediğinizden emin misiniz?\n\n"
            "Bu işlem geri alınamaz!"
        )

        
        if confirmed:
            success_count = 0
            error_count = 0
            
            for ders_kodu, ders_adi in course_list:
                ders = self.ders_model.get_ders_by_kod(self.bolum_id, ders_kodu)
                if ders:
                    result = self.ders_controller.delete_ders(ders['ders_id'])
                    if result['success']:
                        success_count += 1
                    else:
                        error_count += 1
                        logger.error(f"Failed to delete {ders_kodu}: {result['message']}")
                else:
                    error_count += 1
            
            # Show result message
            if error_count > 0:
                ModernMessageBox.warning(
                    self, 
                    "İşlem Tamamlandı", 
                    f"✅ {success_count} ders silindi\n❌ {error_count} ders silinemedi"
                )
            else:
                ModernMessageBox.success(
                    self, 
                    "Başarılı", 
                    f"{success_count} ders başarıyla silindi!"
                )
            
            self.load_existing_dersler()
            
            # Refresh main window UI if courses were deleted
            if success_count > 0:
                refresh_main_window_ui(self)
    
    def delete_selected_course(self):
        """Delete selected course"""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            ModernMessageBox.warning(self, "Uyarı", "Lütfen silmek için bir ders seçin!")
            return
        
        row = selected_rows[0].row()
        ders_kodu = self.table.item(row, 0).text() if self.table.item(row, 0) else None
        ders_adi = self.table.item(row, 1).text() if self.table.item(row, 1) else "İsimsiz"
        
        if not ders_kodu:
            ModernMessageBox.warning(self, "Uyarı", "Ders kodu bulunamadı!")
            return
        
        ders = self.ders_model.get_ders_by_kod(self.bolum_id, ders_kodu)
        if not ders:
            ModernMessageBox.warning(self, "Hata", "Ders bulunamadı!")
            return
        
        confirmed = ModernMessageBox.question(
            self,
            "Ders Sil",
            f"'{ders_adi}' ({ders_kodu}) dersini silmek istediğinizden emin misiniz?\n\n"
            "Bu işlem geri alınamaz!"
        )

        
        if confirmed:
            result = self.ders_controller.delete_ders(ders['ders_id'])
            
            if result['success']:
                ModernMessageBox.success(self, "Başarılı", result['message'])
                self.load_existing_dersler()
                refresh_main_window_ui(self)
            else:
                ModernMessageBox.error(self, "Hata", result['message'])
