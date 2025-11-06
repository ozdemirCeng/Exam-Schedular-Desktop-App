"""
Program Result Dialog - WITH SCORING
Shows exam schedule with quality score and details
"""

import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QGroupBox, QTextEdit, QTabWidget, QWidget, QScrollArea,
    QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from models.database import db
from models.sinav_model import SinavModel
from models.ders_model import DersModel
from models.derslik_model import DerslikModel
from controllers.sinav_controller import SinavController
from utils.export_utils import ExportUtils

logger = logging.getLogger(__name__)


class ProgramResultDialog(QDialog):
    """Dialog to show exam schedule results with scoring"""

    def __init__(self, schedule_data, params, score_result=None, parent=None):
        super().__init__(parent)
        self.schedule_data = schedule_data
        self.params = params
        self.score_result = score_result
        self.bolum_id = params.get('bolum_id')

        self.setWindowTitle("Sınav Programı Oluşturuldu")
        self.setMinimumSize(1200, 800)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Success header with score
        header = self._create_header()
        layout.addWidget(header)

        # Tabs: Schedule / Score Details / Metrics
        tabs = QTabWidget()
        tabs.setFont(QFont("Segoe UI", 11))

        # Tab 1: Schedule
        schedule_tab = self._create_schedule_tab()
        tabs.addTab(schedule_tab, "📅 Program")

        # Tab 2: Score Details (if available)
        if self.score_result:
            score_tab = self._create_score_tab()
            tabs.addTab(score_tab, "📊 Puanlama Detayı")

        # Tab 3: Metrics
        if self.score_result:
            metrics_tab = self._create_metrics_tab()
            tabs.addTab(metrics_tab, "📈 Metrikler")

        layout.addWidget(tabs)

        # Action buttons
        btn_layout = self._create_action_buttons()
        layout.addLayout(btn_layout)

    def _create_header(self) -> QFrame:
        """Create header with score badge"""
        header = QFrame()

        # Color based on score
        if self.score_result:
            score = self.score_result.get('total_score', 0)
            if score >= 90:
                color_start = "#10b981"  # Green
                color_end = "#059669"
            elif score >= 75:
                color_start = "#3b82f6"  # Blue
                color_end = "#2563eb"
            elif score >= 60:
                color_start = "#f59e0b"  # Orange
                color_end = "#d97706"
            else:
                color_start = "#ef4444"  # Red
                color_end = "#dc2626"
        else:
            color_start = "#10b981"
            color_end = "#059669"

        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color_start}, stop:1 {color_end});
                border-radius: 12px;
                padding: 20px;
            }}
        """)

        header_layout = QHBoxLayout(header)

        # Left side: Title and stats
        left_layout = QVBoxLayout()

        title = QLabel("✅ Sınav Programı Başarıyla Oluşturuldu!")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        left_layout.addWidget(title)

        # Calculate unique exams and dates (group by datetime + ders_id)
        from collections import defaultdict
        exam_groups = defaultdict(list)
        for s in self.schedule_data:
            tarih = datetime.fromisoformat(s['tarih_saat']) if isinstance(s['tarih_saat'], str) else s['tarih_saat']
            ders_id = s.get('ders_id')
            key = (tarih, ders_id)
            exam_groups[key].append(s)
        
        unique_exams = len(exam_groups)
        unique_dates = len(set(
            (datetime.fromisoformat(s['tarih_saat']) if isinstance(s['tarih_saat'], str) else s['tarih_saat']).date()
            for s in self.schedule_data
        ))
        
        # Count total classrooms used
        total_classrooms_used = sum(len(exams) for exams in exam_groups.values())

        stats = QLabel(
            f"📚 {unique_exams} Sınav  •  📅 {unique_dates} Gün  •  🏛 {total_classrooms_used} Derslik Ataması")
        stats.setStyleSheet("color: white; font-size: 14px;")
        left_layout.addWidget(stats)

        # Attempt info
        if self.score_result:
            attempt_info = self.score_result.get('best_attempt', 1)
            total_attempts = self.score_result.get('total_attempts', 1)
            strategy = self.score_result.get('strategy_used', 'N/A')

            attempt_label = QLabel(f"🔄 Deneme: {attempt_info}/{total_attempts}  •  🎯 Strateji: {strategy}")
            attempt_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 12px;")
            left_layout.addWidget(attempt_label)

        header_layout.addLayout(left_layout, 1)

        # Right side: Score badge
        if self.score_result:
            score = self.score_result.get('total_score', 0)

            score_frame = QFrame()
            score_frame.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 0.2);
                    border-radius: 12px;
                    padding: 15px;
                }
            """)
            score_layout = QVBoxLayout(score_frame)
            score_layout.setAlignment(Qt.AlignCenter)

            score_label = QLabel(f"{score:.1f}")
            score_label.setStyleSheet("color: white; font-size: 36px; font-weight: bold;")
            score_label.setAlignment(Qt.AlignCenter)

            score_max = QLabel("/ 100")
            score_max.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 14px;")
            score_max.setAlignment(Qt.AlignCenter)

            score_layout.addWidget(score_label)
            score_layout.addWidget(score_max)

            header_layout.addWidget(score_frame)

        return header

    def _create_schedule_tab(self) -> QWidget:
        """Create schedule table tab with merged classrooms"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        # Table
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            'Tarih/Saat', 'Ders Kodu', 'Ders Adı', 'Öğretim Elemanı', 'Derslikler', 'Öğrenci'
        ])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)

        # Group by (datetime, ders_id) to merge multiple classrooms
        from collections import defaultdict
        exam_groups = defaultdict(lambda: {
            'ders_kodu': '',
            'ders_adi': '',
            'ogretim_elemani': '',
            'ogrenci_sayisi': 0,
            'derslikler': []
        })
        
        for row_data in self.schedule_data:
            tarih = datetime.fromisoformat(row_data['tarih_saat']) if isinstance(row_data['tarih_saat'], str) else row_data['tarih_saat']
            ders_id = row_data.get('ders_id')
            key = (tarih, ders_id)
            
            group = exam_groups[key]
            if not group['ders_kodu']:
                group['ders_kodu'] = row_data.get('ders_kodu', '')
                group['ders_adi'] = row_data.get('ders_adi', '')
                group['ogretim_elemani'] = row_data.get('ogretim_elemani', '')
                group['ogrenci_sayisi'] = row_data.get('ogrenci_sayisi', 0)
            
            # Add unique classroom(s). Handle comma-joined fields from DB aggregation.
            derslik_field = row_data.get('derslik_adi', row_data.get('derslik_kodu', ''))
            if derslik_field:
                if isinstance(derslik_field, str) and ',' in derslik_field:
                    for part in [p.strip() for p in derslik_field.split(',') if p.strip()]:
                        if part not in group['derslikler']:
                            group['derslikler'].append(part)
                else:
                    if derslik_field not in group['derslikler']:
                        group['derslikler'].append(derslik_field)
        
        # Sort by datetime
        sorted_exams = sorted(exam_groups.items(), key=lambda x: x[0][0])
        
        # Populate table with merged data
        for (tarih, ders_id), group_data in sorted_exams:
            row = table.rowCount()
            table.insertRow(row)

            tarih_str = tarih.strftime("%d.%m.%Y %H:%M")
            derslikler_str = ', '.join(group_data['derslikler']) if group_data['derslikler'] else '-'

            table.setItem(row, 0, QTableWidgetItem(tarih_str))
            table.setItem(row, 1, QTableWidgetItem(group_data['ders_kodu']))
            table.setItem(row, 2, QTableWidgetItem(group_data['ders_adi']))
            table.setItem(row, 3, QTableWidgetItem(group_data['ogretim_elemani']))
            table.setItem(row, 4, QTableWidgetItem(derslikler_str))

            ogrenci_item = QTableWidgetItem(str(group_data['ogrenci_sayisi']))
            ogrenci_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 5, ogrenci_item)

        # Column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        layout.addWidget(table)

        return tab

    def _create_score_tab(self) -> QWidget:
        """Create score details tab with proper layout"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 1. Breakdown Table - Compact and clean
        breakdown_group = QGroupBox("📊 Puan Dağılımı")
        breakdown_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        breakdown_layout = QVBoxLayout(breakdown_group)
        breakdown_layout.setContentsMargins(12, 20, 12, 12)
        breakdown_layout.setSpacing(8)

        breakdown_table = QTableWidget()
        breakdown_table.setColumnCount(4)
        breakdown_table.setHorizontalHeaderLabels(['Kriter', 'Puan', 'Ağırlık (%)', 'Katkı'])
        breakdown_table.setEditTriggers(QTableWidget.NoEditTriggers)
        breakdown_table.setSelectionMode(QTableWidget.NoSelection)
        breakdown_table.setAlternatingRowColors(True)
        breakdown_table.verticalHeader().setVisible(False)
        breakdown_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                gridline-color: #f3f4f6;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f9fafb;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #e5e7eb;
                font-weight: bold;
            }
        """)

        breakdown = self.score_result.get('breakdown', {})

        # Criteria names (Turkish)
        criteria_names = {
            'no_conflict': '🚫 Çakışma Yok',
            'student_daily_limit': '👥 Öğrenci Günlük Limit',
            'class_daily_limit': '📚 Sınıf Günlük Limit',
            'student_gaps': '⏱️ Öğrenci Arası Boşluk',
            'class_gaps': '📅 Sınıf Arası Boşluk',
            'classroom_reuse': '🏛️ Derslik Dengesi',
            'balanced_distribution': '⚖️ Dengeli Dağılım',
            'exam_duration_opt': '⏰ Süre Optimizasyonu'
        }

        row_count = 0
        for key, data in breakdown.items():
            breakdown_table.insertRow(row_count)

            name = criteria_names.get(key, key)
            score = data['score']
            weight = data['weight']
            contribution = data['weighted_score']

            # Column 0: Name
            name_item = QTableWidgetItem(name)
            name_item.setFont(QFont("Segoe UI", 10))
            breakdown_table.setItem(row_count, 0, name_item)

            # Column 1: Score with color
            score_item = QTableWidgetItem(f"{score:.1f}")
            score_item.setTextAlignment(Qt.AlignCenter)
            score_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            if score >= 90:
                score_item.setForeground(QColor("#10b981"))
            elif score >= 75:
                score_item.setForeground(QColor("#3b82f6"))
            elif score >= 60:
                score_item.setForeground(QColor("#f59e0b"))
            else:
                score_item.setForeground(QColor("#ef4444"))
            breakdown_table.setItem(row_count, 1, score_item)

            # Column 2: Weight
            weight_item = QTableWidgetItem(f"{weight:.1f}")
            weight_item.setTextAlignment(Qt.AlignCenter)
            weight_item.setFont(QFont("Segoe UI", 10))
            breakdown_table.setItem(row_count, 2, weight_item)

            # Column 3: Contribution
            contrib_item = QTableWidgetItem(f"{contribution:.2f}")
            contrib_item.setTextAlignment(Qt.AlignCenter)
            contrib_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            breakdown_table.setItem(row_count, 3, contrib_item)

            row_count += 1

        # Auto-resize to content
        breakdown_table.resizeColumnsToContents()
        breakdown_table.horizontalHeader().setStretchLastSection(False)
        breakdown_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        breakdown_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        breakdown_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        breakdown_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        
        # Set fixed column widths for better alignment
        breakdown_table.setColumnWidth(1, 80)
        breakdown_table.setColumnWidth(2, 100)
        breakdown_table.setColumnWidth(3, 80)
        
        # Set table height based on row count
        row_height = breakdown_table.rowHeight(0) if row_count > 0 else 35
        header_height = breakdown_table.horizontalHeader().height()
        table_height = header_height + (row_height * row_count) + 4
        breakdown_table.setFixedHeight(table_height)

        breakdown_layout.addWidget(breakdown_table)
        layout.addWidget(breakdown_group)

        # 2. Bonuses section - List style
        bonuses = self.score_result.get('bonuses', [])
        if bonuses:
            bonus_group = QGroupBox(f"✨ Artılar ({len(bonuses)})")
            bonus_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    font-size: 14px;
                    border: 2px solid #86efac;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 12px;
                    background-color: #f0fdf4;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 8px;
                    color: #059669;
                }
            """)
            bonus_layout = QVBoxLayout(bonus_group)
            bonus_layout.setContentsMargins(12, 20, 12, 12)
            bonus_layout.setSpacing(6)

            for bonus in bonuses:
                bonus_label = QLabel(f"  {bonus}")
                bonus_label.setWordWrap(True)
                bonus_label.setStyleSheet("""
                    QLabel {
                        font-size: 11px;
                        padding: 6px;
                        color: #065f46;
                        background-color: transparent;
                    }
                """)
                bonus_layout.addWidget(bonus_label)

            layout.addWidget(bonus_group)

        # 3. Penalties section - List style
        penalties = self.score_result.get('penalties', [])
        if penalties:
            penalty_group = QGroupBox(f"⚠️ İyileştirme Alanları ({len(penalties)})")
            penalty_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    font-size: 14px;
                    border: 2px solid #fca5a5;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 12px;
                    background-color: #fef2f2;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 8px;
                    color: #dc2626;
                }
            """)
            penalty_layout = QVBoxLayout(penalty_group)
            penalty_layout.setContentsMargins(12, 20, 12, 12)
            penalty_layout.setSpacing(6)

            for penalty in penalties:
                penalty_label = QLabel(f"  {penalty}")
                penalty_label.setWordWrap(True)
                penalty_label.setStyleSheet("""
                    QLabel {
                        font-size: 11px;
                        padding: 6px;
                        color: #991b1b;
                        background-color: transparent;
                    }
                """)
                penalty_layout.addWidget(penalty_label)

            layout.addWidget(penalty_group)

        # Add stretch at bottom
        layout.addStretch()

        # Set content to scroll area
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        return tab

    def _create_metrics_tab(self) -> QWidget:
        """Create metrics tab with modern card layout"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        metrics = self.score_result.get('metrics', {})

        # Create metrics cards
        cards_data = [
            {
                'title': '👥 Öğrenci Metrikleri',
                'color': '#3b82f6',
                'items': [
                    ('Maksimum günlük sınav', f"{metrics.get('max_student_daily', 0)}"),
                    ('Ortalama günlük sınav', f"{metrics.get('avg_student_daily', 0):.2f}"),
                    ('Limit aşan öğrenci', f"{metrics.get('student_over_limit', 0)}")
                ]
            },
            {
                'title': '📚 Sınıf Metrikleri',
                'color': '#10b981',
                'items': [
                    ('Maksimum günlük sınav', f"{metrics.get('max_class_daily', 0)}"),
                    ('Ortalama günlük sınav', f"{metrics.get('avg_class_daily', 0):.2f}"),
                    ('Limit aşan sınıf', f"{metrics.get('class_over_limit', 0)}")
                ]
            },
            {
                'title': '🏛️ Derslik Metrikleri',
                'color': '#f59e0b',
                'items': [
                    ('Derslik dengesi', f"{metrics.get('classroom_balance', 0):.1f}%"),
                    ('Günlük dağılım dengesi', f"{metrics.get('day_balance', 0):.1f}%")
                ]
            }
        ]

        for card_data in cards_data:
            card = self._create_metric_card(
                card_data['title'],
                card_data['items'],
                card_data['color']
            )
            layout.addWidget(card)

        layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        return tab

    def _create_metric_card(self, title: str, items: list, color: str) -> QGroupBox:
        """Create a styled metric card"""
        card = QGroupBox(title)
        card.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 14px;
                border: 2px solid {color};
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: {color};
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 20, 16, 16)
        card_layout.setSpacing(12)

        # Create grid-like layout for metrics
        for label, value in items:
            row = QHBoxLayout()
            row.setSpacing(8)

            label_widget = QLabel(f"• {label}:")
            label_widget.setStyleSheet("font-size: 12px; color: #6b7280;")
            row.addWidget(label_widget)

            row.addStretch()

            value_widget = QLabel(value)
            value_widget.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {color};")
            row.addWidget(value_widget)

            card_layout.addLayout(row)

        return card

    def _create_action_buttons(self) -> QHBoxLayout:
        """Create action buttons"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        # Excel button
        excel_btn = QPushButton("📊 Excel İndir")
        excel_btn.setFixedHeight(44)
        excel_btn.clicked.connect(self.export_excel)
        btn_layout.addWidget(excel_btn)

        # PDF button
        pdf_btn = QPushButton("📄 PDF İndir")
        pdf_btn.setFixedHeight(44)
        pdf_btn.clicked.connect(self.export_pdf)
        btn_layout.addWidget(pdf_btn)

        # Save button
        save_btn = QPushButton("💾 Veritabanına Kaydet")
        save_btn.setFixedHeight(44)
        save_btn.clicked.connect(self.save_to_db)
        btn_layout.addWidget(save_btn)

        btn_layout.addStretch()

        # Close button
        close_btn = QPushButton("❌ Kapat (İptal)")
        close_btn.setFixedHeight(44)
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)

        return btn_layout

    def export_excel(self):
        """Export to Excel"""
        try:
            from models.bolum_model import BolumModel
            
            # Get bolum info
            bolum_adi = ""
            if self.bolum_id:
                try:
                    bolum_model = BolumModel(db)
                    bolum = bolum_model.get_bolum_by_id(self.bolum_id)
                    if bolum:
                        bolum_adi = bolum.get('bolum_adi', '')
                except Exception as e:
                    logger.warning(f"Could not get bolum info: {e}")
            
            # Suggest filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suggested_name = f"Sinav_Programi_{timestamp}.xlsx"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Excel Dosyası Kaydet",
                suggested_name,
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                return
            
            # Prepare data for export
            export_data = {
                'type': 'sinav_takvimi',
                'title': 'Sınav Takvimi',
                'bolum_adi': bolum_adi,
                'sinav_tipi': self.params.get('sinav_tipi', ''),
                'data': self.schedule_data
            }
            
            # Export
            if ExportUtils.export_to_excel(export_data, file_path):
                from utils.modern_dialogs import ModernMessageBox
                ModernMessageBox.success(
                    self,
                    "Başarılı",
                    "Excel dosyası oluşturuldu!",
                    f"Dosya: {file_path}"
                )
            else:
                from utils.modern_dialogs import ModernMessageBox
                ModernMessageBox.error(
                    self,
                    "Hata",
                    "Excel dosyası oluşturulamadı."
                )
                
        except Exception as e:
            logger.error(f"Excel export error: {e}", exc_info=True)
            from utils.modern_dialogs import ModernMessageBox
            ModernMessageBox.error(
                self,
                "Hata",
                "Excel dosyası oluşturulurken hata oluştu.",
                str(e)
            )

    def export_pdf(self):
        """Export to PDF"""
        try:
            from models.bolum_model import BolumModel
            
            # Get bolum info
            bolum_adi = ""
            if self.bolum_id:
                try:
                    bolum_model = BolumModel(db)
                    bolum = bolum_model.get_bolum_by_id(self.bolum_id)
                    if bolum:
                        bolum_adi = bolum.get('bolum_adi', '')
                except Exception as e:
                    logger.warning(f"Could not get bolum info: {e}")
            
            # Suggest filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suggested_name = f"Sinav_Programi_{timestamp}.pdf"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "PDF Dosyası Kaydet",
                suggested_name,
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return
            
            # Prepare data for export
            export_data = {
                'type': 'sinav_takvimi',
                'title': 'Sınav Takvimi',
                'bolum_adi': bolum_adi,
                'sinav_tipi': self.params.get('sinav_tipi', ''),
                'data': self.schedule_data
            }
            
            # Export
            if ExportUtils.export_to_pdf(export_data, file_path):
                from utils.modern_dialogs import ModernMessageBox
                ModernMessageBox.success(
                    self,
                    "Başarılı",
                    "PDF dosyası oluşturuldu!",
                    f"Dosya: {file_path}"
                )
            else:
                from utils.modern_dialogs import ModernMessageBox
                ModernMessageBox.error(
                    self,
                    "Hata",
                    "PDF dosyası oluşturulamadı."
                )
                
        except Exception as e:
            logger.error(f"PDF export error: {e}", exc_info=True)
            from utils.modern_dialogs import ModernMessageBox
            ModernMessageBox.error(
                self,
                "Hata",
                "PDF dosyası oluşturulurken hata oluştu.",
                str(e)
            )

    def save_to_db(self):
        """Save to database - Uses controller"""
        try:
            # Controller kullan
            controller = SinavController(
                SinavModel(db),
                DersModel(db),
                DerslikModel(db)
            )

            result = controller.save_exam_schedule(self.schedule_data)

            if result['success']:
                from utils.modern_dialogs import ModernMessageBox
                ModernMessageBox.success(
                    self,
                    "Başarılı",
                    f"{result.get('success_count', 0)} sınav kaydedildi!",
                    f"Program ID: {result.get('program_id', 'N/A')}"
                )
                self.accept()
            else:
                from utils.modern_dialogs import ModernMessageBox
                ModernMessageBox.warning(
                    self,
                    "Uyarı",
                    result['message']
                )

        except Exception as e:
            logger.error(f"Save error: {e}", exc_info=True)
            from utils.modern_dialogs import ModernMessageBox
            ModernMessageBox.error(
                self,
                "Kayıt Hatası",
                "Program kaydedilirken hata oluştu.",
                str(e)
            )