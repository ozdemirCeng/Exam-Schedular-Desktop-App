"""
Öğrenci Yükleme (Student Upload) View
Professional interface for uploading and managing students from Excel
"""

import logging

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QFileDialog, QGroupBox, QLineEdit, QSplitter,
    QSpinBox, QFormLayout, QDialog, QDialogButtonBox
)

from controllers.ogrenci_controller import OgrenciController
from models.database import db
from models.ogrenci_model import OgrenciModel
from utils.excel_parser import ExcelParser
from utils.modern_dialogs import ModernMessageBox
from utils.view_helpers import refresh_main_window_ui

logger = logging.getLogger(__name__)


class OgrenciLoadThread(QThread):
    """Thread for loading student Excel file"""
    finished = Signal(list)
    error = Signal(str)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
    
    def run(self):
        try:
            parser = ExcelParser()
            ogrenciler = parser.parse_ogrenci_listesi(self.file_path)
            self.finished.emit(ogrenciler)
        except Exception as e:
            self.error.emit(str(e))


class OgrenciYukleView(QWidget):
    """Student upload and management view"""
    
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.search_input = None
        self.user_data = user_data
        self.bolum_id = user_data.get('bolum_id', 1)
        
        self.ogrenci_model = OgrenciModel(db)
        self.ogrenci_controller = OgrenciController(self.ogrenci_model)
        
        self.pending_ogrenciler = []
        
        self.setup_ui()
        self.load_existing_ogrenciler()
    
    def setup_ui(self):
        """Setup UI - table first, info last"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Compact Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Öğrenci Listesi")
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
        
        # Modern Search bar with frame
        search_container = QFrame()
        search_container.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 4px;
            }
        """)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(16, 8, 16, 8)
        search_layout.setSpacing(12)
        
        search_icon = QLabel("🔍")
        search_icon.setFont(QFont("Segoe UI", 14))
        search_icon.setStyleSheet("background: transparent;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Öğrenci no veya ad ile ara...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setFixedHeight(42)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 14px;
                padding: 8px;
                color: #1e293b;
            }
            QLineEdit::placeholder {
                color: #94a3b8;
            }
        """)
        
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_input)
        
        layout.addWidget(search_container)
        
        # Splitter for students and courses
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Students table
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Öğrenci No", "Ad Soyad", "Sınıf", "Durum"
        ])
        
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.show_student_courses)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 100)
        
        left_layout.addWidget(self.table)
        
        # Student action buttons
        student_actions = QHBoxLayout()
        student_actions.setSpacing(8)
        
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
        select_all_btn.clicked.connect(self.select_all_students)
        
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
        deselect_all_btn.clicked.connect(self.deselect_all_students)
        
        edit_student_btn = QPushButton("✎ Düzenle")
        edit_student_btn.setFixedHeight(34)
        edit_student_btn.setCursor(Qt.PointingHandCursor)
        edit_student_btn.setStyleSheet("""
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
        edit_student_btn.clicked.connect(self.edit_selected_student)
        
        delete_student_btn = QPushButton("🗑 Sil")
        delete_student_btn.setFixedHeight(34)
        delete_student_btn.setCursor(Qt.PointingHandCursor)
        delete_student_btn.setStyleSheet("""
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
        delete_student_btn.clicked.connect(self.delete_selected_students)
        
        student_actions.addWidget(select_all_btn)
        student_actions.addWidget(deselect_all_btn)
        student_actions.addWidget(edit_student_btn)
        student_actions.addWidget(delete_student_btn)
        student_actions.addStretch()
        
        left_layout.addLayout(student_actions)
        splitter.addWidget(left_widget)
        
        # Right side - Courses table
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        courses_header = QLabel("Öğrencinin Aldığı Dersler")
        courses_header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        courses_header.setStyleSheet("padding: 8px; background-color: #f3f4f6; border-radius: 4px;")
        right_layout.addWidget(courses_header)
        
        self.courses_table = QTableWidget()
        self.courses_table.setColumnCount(3)
        self.courses_table.setHorizontalHeaderLabels(["Ders Kodu", "Ders Adı", "Sınıf"])
        self.courses_table.verticalHeader().setVisible(False)
        self.courses_table.setAlternatingRowColors(True)
        self.courses_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        courses_header_view = self.courses_table.horizontalHeader()
        courses_header_view.setSectionResizeMode(0, QHeaderView.Fixed)
        courses_header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        courses_header_view.setSectionResizeMode(2, QHeaderView.Fixed)
        
        self.courses_table.setColumnWidth(0, 100)
        self.courses_table.setColumnWidth(2, 60)
        
        right_layout.addWidget(self.courses_table)
        
        self.courses_stats = QLabel("Bir öğrenci seçin")
        self.courses_stats.setStyleSheet("color: #6b7280; font-size: 11px; padding: 8px;")
        right_layout.addWidget(self.courses_stats)
        
        splitter.addWidget(right_widget)
        
        # Set splitter proportions (60% students, 40% courses)
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
            "<b>Sütunlar:</b> ÖĞRENCİ NO • AD SOYAD • SINIF<br>"
            "<b>Örnek:</b> 2020123456, Ahmet Yılmaz, 2"
        )
        info_text.setStyleSheet("color: #92400e; font-size: 11px;")
        info_text.setWordWrap(True)
        info_group_layout.addWidget(info_text)
        
        bottom_layout.addWidget(stats_group)
        bottom_layout.addWidget(info_group, stretch=1)
        
        layout.addWidget(bottom_container)
    
    def load_existing_ogrenciler(self):
        """Load existing students"""
        try:
            ogrenciler = self.ogrenci_model.get_ogrenciler_by_bolum(self.bolum_id)
            self.populate_table(ogrenciler, existing=True)
            self.update_stats(len(ogrenciler), 0)
        except Exception as e:
            logger.error(f"Error loading students: {e}")
            ModernMessageBox.error(self, "Hata", "Öğrenciler yüklenirken oluştu", f"{str(e)}")
    
    def populate_table(self, ogrenciler, existing=False):
        """Populate table with student data"""
        self.table.setRowCount(0)
        
        for row, ogrenci in enumerate(ogrenciler):
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(ogrenci.get('ogrenci_no', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(str(ogrenci.get('ad_soyad', ''))))
            
            sinif_item = QTableWidgetItem(str(ogrenci.get('sinif', '')))
            sinif_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, sinif_item)
            
            durum = "✅ Kayıtlı" if existing else "⏳ Beklemede"
            durum_item = QTableWidgetItem(durum)
            durum_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, durum_item)
    
    def filter_table(self):
        """Filter table based on search"""
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            no = self.table.item(row, 0).text().lower()
            ad = self.table.item(row, 1).text().lower()
            
            if search_text in no or search_text in ad:
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)
    
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
        self.thread = OgrenciLoadThread(file_path)
        self.thread.finished.connect(self.on_excel_loaded)
        self.thread.error.connect(self.on_excel_error)
        self.thread.start()
    
    def on_excel_loaded(self, ogrenciler):
        """Handle loaded Excel data"""
        if not ogrenciler:
            ModernMessageBox.warning(self, "Uyarı", "Excel dosyasında öğrenci bulunamadı!")
            return
        
        # Check for existing students
        existing_count = 0
        new_count = 0
        existing_details = []
        
        for idx, ogrenci in enumerate(ogrenciler, start=1):
            excel_row = idx + 1  # +1 for header row
            existing = self.ogrenci_model.get_ogrenci_by_no(ogrenci.get('ogrenci_no', ''))
            if existing:
                existing_count += 1
                existing_details.append(
                    f"Satır {excel_row}: {ogrenci.get('ogrenci_no')} - {ogrenci.get('ad_soyad')} - {ogrenci.get('sinif', '?')}. Sınıf"
                )
            else:
                new_count += 1
        
        self.pending_ogrenciler = ogrenciler
        self.populate_table(ogrenciler, existing=False)
        self.update_stats(0, len(ogrenciler))
        
        # Show summary with existing student info
        summary_msg = f"📚 Excel'den {len(ogrenciler)} öğrenci yüklendi\n\n"
        summary_msg += f"✅ Yeni öğrenci: {new_count}\n"
        summary_msg += f"⚠️ Zaten mevcut: {existing_count}"
        
        if existing_count > 0:
            summary_msg += f"\n\n❓ Mevcut öğrenciler atlanacak. Devam edilsin mi?"
        else:
            summary_msg += f"\n\nVeritabanına kaydetmek istiyor musunuz?"
        
        # Prepare details text
        details_text = ""
        if existing_count > 0:
            details_text = "⚠️ MEVCUT ÖĞRENCİLER (Atlanacak):\n\n" + "\n".join(existing_details)
        
        confirmed = ModernMessageBox.question(
            self,
            "Öğrencileri Kaydet",
            summary_msg,
            details_text if details_text else None
        )

        
        if confirmed:
            self.save_ogrenciler(skip_existing=True)
    
    def on_excel_error(self, error_msg):
        """Handle Excel loading error with detailed information"""
        # Format detailed text for better readability
        detailed_text = error_msg
        if "Satır" in error_msg:
            # Already has line numbers
            detailed_text = error_msg.replace("Satır ", "\n• Satır ")
        
        ModernMessageBox.error(
            self,
            "Excel Yükleme Hatası",
            "Excel dosyası yüklenirken hata oluştu!",
            detailed_text
        )
    
    def save_ogrenciler(self, skip_existing=True):
        """Save students to database with detailed error reporting"""
        if not self.pending_ogrenciler:
            return
        
        try:
            success_count = 0
            skipped_count = 0
            error_count = 0
            error_details = []
            skipped_details = []
            
            for idx, ogrenci in enumerate(self.pending_ogrenciler, 1):
                excel_row = idx + 1  # +1 for header row in Excel
                ogrenci['bolum_id'] = self.bolum_id
                
                # Check if student already exists
                if skip_existing:
                    existing = self.ogrenci_model.get_ogrenci_by_no(ogrenci.get('ogrenci_no', ''))
                    if existing:
                        skipped_count += 1
                        skipped_details.append(f"Satır {excel_row}: {ogrenci.get('ogrenci_no')} - {ogrenci.get('ad_soyad')}")
                        logger.info(f"Skipped existing student at row {excel_row}: {ogrenci.get('ogrenci_no')}")
                        continue
                
                result = self.ogrenci_controller.create_ogrenci(ogrenci)
                
                if result['success']:
                    success_count += 1
                else:
                    error_count += 1
                    # Track which row failed
                    error_msg = f"Satır {excel_row} ({ogrenci.get('ogrenci_no', '?')} - {ogrenci.get('ad_soyad', '?')}): {result['message']}"
                    error_details.append(error_msg)
                    logger.warning(error_msg)
            
            # Show detailed results
            result_message = []
            if success_count > 0:
                result_message.append(f"✅ {success_count} yeni öğrenci kaydedildi")
            if skipped_count > 0:
                result_message.append(f"⏭️ {skipped_count} mevcut öğrenci atlandı")
            if error_count > 0:
                result_message.append(f"❌ {error_count} öğrenci kaydedilemedi")
            
            # Prepare detailed text
            detailed_parts = []
            
            if skipped_count > 0:
                skipped_text = "⏭️ ATLANAN ÖĞRENCİLER:\n" + "\n".join(skipped_details[:15])
                if len(skipped_details) > 15:
                    skipped_text += f"\n... ve {len(skipped_details) - 15} öğrenci daha"
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
                        "Tüm öğrenciler zaten veritabanında mevcut.\n\n"
                        f"{skipped_count} öğrenci atlandı.",
                        detailed_text
                    )
                else:
                    ModernMessageBox.success(
                        self, "Başarılı", message
                    )
            
            self.pending_ogrenciler = []
            self.load_existing_ogrenciler()
            
            # Refresh main window UI (menus and shortcuts) if students were added
            if success_count > 0:
                refresh_main_window_ui(self)
            
        except Exception as e:
            logger.error(f"Error saving students: {e}", exc_info=True)
            ModernMessageBox.error(self, "Hata", "Öğrenciler kaydedilirken oluştu", f"{str(e)}")
    
    def update_stats(self, existing, pending):
        """Update statistics label"""
        self.stats_label.setText(
            f"📊 Kayıtlı: {existing} | Beklemede: {pending}"
        )
    
    def show_student_courses(self):
        """Show courses of selected student"""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            self.courses_table.setRowCount(0)
            self.courses_stats.setText("Bir öğrenci seçin")
            return
        
        row = selected_rows[0].row()
        ogrenci_no = self.table.item(row, 0).text()
        ad_soyad = self.table.item(row, 1).text()
        
        # Get student's courses
        try:
            dersler = self.ogrenci_model.get_dersler_by_ogrenci(ogrenci_no)
            
            # Update courses table
            self.courses_table.setRowCount(0)
            
            if not dersler:
                self.courses_stats.setText(f"👤 {ad_soyad} - Kayıtlı ders yok")
            else:
                for row_idx, ders in enumerate(dersler):
                    self.courses_table.insertRow(row_idx)
                    
                    kod_item = QTableWidgetItem(ders.get('ders_kodu', ''))
                    ad_item = QTableWidgetItem(ders.get('ders_adi', ''))
                    sinif_item = QTableWidgetItem(str(ders.get('sinif', '')))
                    sinif_item.setTextAlignment(Qt.AlignCenter)
                    
                    self.courses_table.setItem(row_idx, 0, kod_item)
                    self.courses_table.setItem(row_idx, 1, ad_item)
                    self.courses_table.setItem(row_idx, 2, sinif_item)
                
                self.courses_stats.setText(f"👤 {ad_soyad} - {len(dersler)} ders")
            
        except Exception as e:
            logger.error(f"Error loading student courses: {e}")
            self.courses_stats.setText(f"❌ Hata: {str(e)}")
    
    def select_all_students(self):
        """Select all students in table"""
        self.table.selectAll()
    
    def deselect_all_students(self):
        """Deselect all students"""
        self.table.clearSelection()
    
    def delete_selected_students(self):
        """Delete multiple selected students"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            ModernMessageBox.warning(self, "Uyarı", "Lütfen silmek için en az bir öğrenci seçin!")
            return
        
        # Check if any are pending
        pending_found = False
        student_list = []
        for index in selected_rows:
            row = index.row()
            durum = self.table.item(row, 3).text()
            if durum == "⏳ Beklemede":
                pending_found = True
                break
            ogrenci_no = self.table.item(row, 0).text()
            ad_soyad = self.table.item(row, 1).text()
            student_list.append((ogrenci_no, ad_soyad))
        
        if pending_found:
            ModernMessageBox.warning(self, "Uyarı", "Beklemedeki öğrenciler silinemez! İptal için sayfayı yenileyin.")
            return
        
        confirmed = ModernMessageBox.question(
            self,
            "Öğrencileri Sil",
            f"{len(student_list)} öğrenciyi silmek istediğinizden emin misiniz?\n\n"
            "Bu işlem geri alınamaz!"
        )

        
        if confirmed:
            success_count = 0
            error_count = 0
            
            for ogrenci_no, ad_soyad in student_list:
                result = self.ogrenci_controller.delete_ogrenci(ogrenci_no)
                if result['success']:
                    success_count += 1
                else:
                    error_count += 1
                    logger.error(f"Failed to delete {ogrenci_no}: {result['message']}")
            
            ModernMessageBox.success(
                self, "İşlem Tamamlandı", f"{success_count} öğrenci silindi", f"❌ {error_count} öğrenci silinemedi"
            )
            
            self.load_existing_ogrenciler()
    
    def edit_selected_student(self):
        """Edit selected student with modern dialog"""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            ModernMessageBox.warning(self, "Uyarı", "Lütfen düzenlemek için bir öğrenci seçin!")
            return
        
        row = selected_rows[0].row()
        durum_item = self.table.item(row, 3)
        
        if durum_item and durum_item.text() == "⏳ Beklemede":
            ModernMessageBox.warning(self, "Uyarı", "Beklemedeki öğrenciler düzenlenemez! Önce kaydedin.")
            return
        
        ogrenci_no_item = self.table.item(row, 0)
        if not ogrenci_no_item:
            ModernMessageBox.warning(self, "Hata", "Öğrenci numarası bulunamadı!")
            return
        
        ogrenci_no = ogrenci_no_item.text()
        
        # Get full student data from database
        ogrenci = self.ogrenci_model.get_ogrenci_by_no(ogrenci_no)
        if not ogrenci:
            ModernMessageBox.warning(self, "Hata", f"Öğrenci bulunamadı: {ogrenci_no}")
            return
        
        # Create modern edit dialog
        from utils.edit_dialogs import OgrenciEditDialog
        
        dialog = OgrenciEditDialog(ogrenci, self.ogrenci_model, self.bolum_id, self)
        
        if dialog.exec() == QDialog.Accepted:
            updated_data = dialog.get_updated_data()
            
            result = self.ogrenci_controller.update_ogrenci(ogrenci_no, updated_data)
            
            if result['success']:
                ModernMessageBox.success(self, "Başarılı", result['message'])
                self.load_existing_ogrenciler()
            else:
                ModernMessageBox.error(self, "Güncelleme Hatası", result['message'])
