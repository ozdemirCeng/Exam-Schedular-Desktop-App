"""
Modern Edit Dialogs for Courses and Students
KOÜ themed professional edit dialogs with course/student management
"""

import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QComboBox, QFrame, QScrollArea,
    QWidget, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from styles.kou_theme import KOUTheme

logger = logging.getLogger(__name__)


class ModernEditDialog(QDialog):
    """Base class for modern edit dialogs"""
    
    def __init__(self, parent=None, title="Düzenle", width=600):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(width)
        self.setModal(True)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header
        self._create_header(title)
        
        # Content area (to be filled by subclasses)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(24, 24, 24, 24)
        self.content_layout.setSpacing(20)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self.content_widget)
        scroll.setStyleSheet(KOUTheme.scroll_area())
        
        self.main_layout.addWidget(scroll, 1)
        
        # Footer buttons
        self._create_footer()
    
    def _create_header(self, title):
        """Create modern header"""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: {KOUTheme.PRIMARY};
                border: none;
                padding: 20px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        
        icon_label = QLabel("✏️")
        icon_label.setFont(QFont("Segoe UI Emoji", 24))
        icon_label.setStyleSheet("color: white; background: transparent;")
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        self.main_layout.addWidget(header)
    
    def _create_footer(self):
        """Create footer with buttons"""
        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background: {KOUTheme.BG_LIGHT};
                border-top: 1px solid {KOUTheme.BORDER_LIGHT};
                padding: 16px 24px;
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setSpacing(12)
        
        footer_layout.addStretch()
        
        # Cancel button
        self.cancel_btn = QPushButton("❌ İptal")
        self.cancel_btn.setFixedHeight(44)
        self.cancel_btn.setMinimumWidth(120)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet(KOUTheme.button_secondary())
        self.cancel_btn.clicked.connect(self.reject)
        
        # Save button
        self.save_btn = QPushButton("💾 Kaydet")
        self.save_btn.setFixedHeight(44)
        self.save_btn.setMinimumWidth(120)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(KOUTheme.button_primary())
        self.save_btn.clicked.connect(self.accept)
        
        footer_layout.addWidget(self.cancel_btn)
        footer_layout.addWidget(self.save_btn)
        
        self.main_layout.addWidget(footer)
    
    def add_field(self, label_text, widget, tooltip=None):
        """Add a form field"""
        field_frame = QFrame()
        field_frame.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {KOUTheme.BORDER_LIGHT};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        field_layout = QVBoxLayout(field_frame)
        field_layout.setSpacing(8)
        
        label = QLabel(label_text)
        label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        label.setStyleSheet(f"color: {KOUTheme.TEXT_PRIMARY}; background: transparent; border: none; padding: 0;")
        
        if tooltip:
            info_label = QLabel(f"ℹ️ {tooltip}")
            info_label.setFont(QFont("Segoe UI", 10))
            info_label.setStyleSheet(f"color: {KOUTheme.TEXT_MUTED}; background: transparent; border: none; padding: 0;")
            info_label.setWordWrap(True)
        
        field_layout.addWidget(label)
        if tooltip:
            field_layout.addWidget(info_label)
        
        widget.setStyleSheet(KOUTheme.input_field())
        field_layout.addWidget(widget)
        
        self.content_layout.addWidget(field_frame)
        
        return widget


class DersEditDialog(ModernEditDialog):
    """Modern course edit dialog with course-student management"""
    
    def __init__(self, ders_data, ders_model, bolum_id, parent=None):
        self.ders_data = ders_data
        self.ders_model = ders_model
        self.bolum_id = bolum_id
        
        super().__init__(parent, "Ders Düzenle", 700)
        self._setup_fields()
        self._load_course_students()
    
    def _setup_fields(self):
        """Setup form fields"""
        # Course code (read-only)
        self.kod_edit = QLineEdit(self.ders_data.get('ders_kodu', ''))
        self.kod_edit.setReadOnly(True)
        self.kod_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {KOUTheme.BG_LIGHTER};
                border: 2px solid {KOUTheme.BORDER_LIGHT};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                color: {KOUTheme.TEXT_SECONDARY};
                min-height: 42px;
            }}
        """)
        self.add_field("📋 Ders Kodu", self.kod_edit, "Ders kodu değiştirilemez")
        
        # Course name
        self.ad_edit = QLineEdit(self.ders_data.get('ders_adi', ''))
        self.add_field("📚 Ders Adı", self.ad_edit)
        
        # Instructor
        self.ogretim_elemani_edit = QLineEdit(self.ders_data.get('ogretim_elemani', ''))
        self.add_field("👨‍🏫 Öğretim Elemanı", self.ogretim_elemani_edit)
        
        # Class level
        self.sinif_edit = QSpinBox()
        self.sinif_edit.setRange(1, 4)
        self.sinif_edit.setValue(self.ders_data.get('sinif', 1))
        self.add_field("🎓 Sınıf", self.sinif_edit)
        
        # Course type
        self.yapi_combo = QComboBox()
        self.yapi_combo.addItems(["Zorunlu", "Seçmeli"])
        self.yapi_combo.setCurrentText(self.ders_data.get('ders_yapisi', 'Zorunlu'))
        self.add_field("📝 Ders Yapısı", self.yapi_combo)
        
        # Student count info
        ogrenci_sayisi = self.ders_data.get('ogrenci_sayisi', 0)
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background: {KOUTheme.PRIMARY_LIGHTER};
                border: 2px solid {KOUTheme.PRIMARY_LIGHT};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        
        info_title = QLabel("👥 Kayıtlı Öğrenciler")
        info_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        info_title.setStyleSheet(f"color: {KOUTheme.PRIMARY}; background: transparent;")
        
        self.student_count_label = QLabel(f"{ogrenci_sayisi} öğrenci bu dersi alıyor")
        self.student_count_label.setFont(QFont("Segoe UI", 11))
        self.student_count_label.setStyleSheet(f"color: {KOUTheme.TEXT_SECONDARY}; background: transparent;")
        
        info_layout.addWidget(info_title)
        info_layout.addWidget(self.student_count_label)
        
        self.content_layout.addWidget(info_frame)
    
    def _load_course_students(self):
        """Load and display students taking this course"""
        try:
            # Get students for this course
            query = """
                SELECT o.ogrenci_no, o.ad_soyad, o.sinif
                FROM ogrenciler o
                INNER JOIN ders_kayitlari dk ON o.ogrenci_no = dk.ogrenci_no
                WHERE dk.ders_id = %s
                ORDER BY o.sinif, o.ad_soyad
            """
            students = self.ders_model.db.execute_query(query, (self.ders_data['ders_id'],))
            
            if students:
                # Update count
                self.student_count_label.setText(f"{len(students)} öğrenci bu dersi alıyor")
                
                # Create students table
                table_frame = QFrame()
                table_frame.setStyleSheet(f"""
                    QFrame {{
                        background: white;
                        border: 1px solid {KOUTheme.BORDER_LIGHT};
                        border-radius: 8px;
                        padding: 12px;
                    }}
                """)
                table_layout = QVBoxLayout(table_frame)
                
                table_title = QLabel("📋 Öğrenci Listesi (İlk 10)")
                table_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
                table_title.setStyleSheet(f"color: {KOUTheme.TEXT_PRIMARY}; background: transparent;")
                table_layout.addWidget(table_title)
                
                students_table = QTableWidget()
                students_table.setColumnCount(3)
                students_table.setHorizontalHeaderLabels(["Öğrenci No", "Ad Soyad", "Sınıf"])
                students_table.setEditTriggers(QTableWidget.NoEditTriggers)
                students_table.setSelectionMode(QTableWidget.NoSelection)
                students_table.verticalHeader().setVisible(False)
                students_table.setMaximumHeight(300)
                students_table.setStyleSheet(KOUTheme.table())
                
                # Show first 10 students
                for student in students[:10]:
                    row = students_table.rowCount()
                    students_table.insertRow(row)
                    students_table.setItem(row, 0, QTableWidgetItem(student['ogrenci_no']))
                    students_table.setItem(row, 1, QTableWidgetItem(student['ad_soyad']))
                    students_table.setItem(row, 2, QTableWidgetItem(str(student['sinif'])))
                
                students_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
                students_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
                students_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
                
                table_layout.addWidget(students_table)
                
                if len(students) > 10:
                    more_label = QLabel(f"... ve {len(students) - 10} öğrenci daha")
                    more_label.setStyleSheet(f"color: {KOUTheme.TEXT_MUTED}; font-size: 10px;")
                    table_layout.addWidget(more_label)
                
                self.content_layout.addWidget(table_frame)
        
        except Exception as e:
            logger.error(f"Error loading course students: {e}")
    
    def get_updated_data(self):
        """Get updated course data"""
        return {
            'ders_adi': self.ad_edit.text().strip(),
            'ogretim_elemani': self.ogretim_elemani_edit.text().strip(),
            'sinif': self.sinif_edit.value(),
            'ders_yapisi': self.yapi_combo.currentText()
        }


class OgrenciEditDialog(ModernEditDialog):
    """Modern student edit dialog with enrolled courses"""
    
    def __init__(self, ogrenci_data, ogrenci_model, bolum_id, parent=None):
        self.ogrenci_data = ogrenci_data
        self.ogrenci_model = ogrenci_model
        self.bolum_id = bolum_id
        
        super().__init__(parent, "Öğrenci Düzenle", 700)
        self._setup_fields()
        self._load_student_courses()
    
    def _setup_fields(self):
        """Setup form fields"""
        # Student number (read-only)
        self.no_edit = QLineEdit(self.ogrenci_data.get('ogrenci_no', ''))
        self.no_edit.setReadOnly(True)
        self.no_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {KOUTheme.BG_LIGHTER};
                border: 2px solid {KOUTheme.BORDER_LIGHT};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                color: {KOUTheme.TEXT_SECONDARY};
                min-height: 42px;
            }}
        """)
        self.add_field("🎫 Öğrenci No", self.no_edit, "Öğrenci numarası değiştirilemez")
        
        # Student name
        self.ad_edit = QLineEdit(self.ogrenci_data.get('ad_soyad', ''))
        self.add_field("👤 Ad Soyad", self.ad_edit)
        
        # Class level
        self.sinif_edit = QSpinBox()
        self.sinif_edit.setRange(1, 6)
        self.sinif_edit.setValue(self.ogrenci_data.get('sinif', 1))
        self.add_field("🎓 Sınıf", self.sinif_edit)
        
        # Course count info
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background: {KOUTheme.PRIMARY_LIGHTER};
                border: 2px solid {KOUTheme.PRIMARY_LIGHT};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        
        info_title = QLabel("📚 Kayıtlı Dersler")
        info_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        info_title.setStyleSheet(f"color: {KOUTheme.PRIMARY}; background: transparent;")
        
        self.course_count_label = QLabel("Dersler yükleniyor...")
        self.course_count_label.setFont(QFont("Segoe UI", 11))
        self.course_count_label.setStyleSheet(f"color: {KOUTheme.TEXT_SECONDARY}; background: transparent;")
        
        info_layout.addWidget(info_title)
        info_layout.addWidget(self.course_count_label)
        
        self.content_layout.addWidget(info_frame)
    
    def _load_student_courses(self):
        """Load and display courses student is enrolled in"""
        try:
            # Get courses for this student using ogrenci_no (not ogrenci_id)
            query = """
                SELECT d.ders_kodu, d.ders_adi, d.sinif, d.ders_yapisi, d.ogretim_elemani
                FROM dersler d
                INNER JOIN ders_kayitlari dk ON d.ders_id = dk.ders_id
                WHERE dk.ogrenci_no = %s
                ORDER BY d.sinif, d.ders_kodu
            """
            courses = self.ogrenci_model.db.execute_query(
                query, 
                (self.ogrenci_data['ogrenci_no'],)
            )
            
            if courses:
                # Update count
                self.course_count_label.setText(f"{len(courses)} derse kayıtlı")
                
                # Create courses table
                table_frame = QFrame()
                table_frame.setStyleSheet(f"""
                    QFrame {{
                        background: white;
                        border: 1px solid {KOUTheme.BORDER_LIGHT};
                        border-radius: 8px;
                        padding: 12px;
                    }}
                """)
                table_layout = QVBoxLayout(table_frame)
                
                table_title = QLabel("📋 Ders Listesi")
                table_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
                table_title.setStyleSheet(f"color: {KOUTheme.TEXT_PRIMARY}; background: transparent;")
                table_layout.addWidget(table_title)
                
                courses_table = QTableWidget()
                courses_table.setColumnCount(4)
                courses_table.setHorizontalHeaderLabels(["Ders Kodu", "Ders Adı", "Sınıf", "Yapı"])
                courses_table.setEditTriggers(QTableWidget.NoEditTriggers)
                courses_table.setSelectionMode(QTableWidget.NoSelection)
                courses_table.verticalHeader().setVisible(False)
                courses_table.setMaximumHeight(300)
                courses_table.setStyleSheet(KOUTheme.table())
                
                for course in courses:
                    row = courses_table.rowCount()
                    courses_table.insertRow(row)
                    courses_table.setItem(row, 0, QTableWidgetItem(course['ders_kodu']))
                    courses_table.setItem(row, 1, QTableWidgetItem(course['ders_adi']))
                    courses_table.setItem(row, 2, QTableWidgetItem(str(course['sinif'])))
                    courses_table.setItem(row, 3, QTableWidgetItem(course['ders_yapisi']))
                
                courses_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
                courses_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
                courses_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
                courses_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
                
                table_layout.addWidget(courses_table)
                self.content_layout.addWidget(table_frame)
            else:
                self.course_count_label.setText("Henüz derse kayıtlı değil")
        
        except Exception as e:
            logger.error(f"Error loading student courses: {e}")
            logger.error(f"Available keys in ogrenci_data: {list(self.ogrenci_data.keys())}")
            self.course_count_label.setText(f"❌ Hata: {str(e)}")
    
    def get_updated_data(self):
        """Get updated student data"""
        return {
            'ad_soyad': self.ad_edit.text().strip(),
            'sinif': self.sinif_edit.value()
        }
