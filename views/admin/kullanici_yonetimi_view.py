"""
Admin Kullanıcı Yönetimi View
Tüm kullanıcıları yönet, şifre değiştir, yeni kullanıcı ekle
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QHeaderView,
    QScrollArea, QGroupBox, QAbstractItemView, QAbstractScrollArea, QSizePolicy,
    QToolButton, QStyle
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from models.user_model import UserModel
from models.bolum_model import BolumModel
from models.database import db
from utils.password_utils import PasswordUtils
from utils.modern_dialogs import ModernMessageBox

logger = logging.getLogger(__name__)


class KullaniciDialog(QDialog):
    """Dialog for adding/editing users"""
    
    def __init__(self, user_data=None, bolumler=None, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.bolumler = bolumler or []
        self.is_edit = user_data is not None
        
        self.setWindowTitle("Kullanıcı Düzenle" if self.is_edit else "Yeni Kullanıcı Ekle")
        self.setMinimumWidth(500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # Ad Soyad
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Örn: ömer özdemir")
        self.name_input.setFixedHeight(36)
        if self.is_edit:
            self.name_input.setText(self.user_data.get('ad_soyad', ''))
        form_layout.addRow("Ad Soyad:", self.name_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Örn: ömer@kocaeli.edu.tr")
        self.email_input.setFixedHeight(36)
        if self.is_edit:
            self.email_input.setText(self.user_data.get('email', ''))
        form_layout.addRow("E-posta:", self.email_input)
        
        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Bölüm Koordinatörü", "Admin"])
        self.role_combo.setFixedHeight(36)
        self.role_combo.currentTextChanged.connect(self.on_role_changed)
        if self.is_edit:
            role = self.user_data.get('role', 'Bölüm Koordinatörü')
            self.role_combo.setCurrentText(role)
        form_layout.addRow("Rol:", self.role_combo)
        
        # Bölüm
        self.bolum_combo = QComboBox()
        self.bolum_combo.addItem("-- Bölüm Seçiniz --", None)
        for bolum in self.bolumler:
            self.bolum_combo.addItem(bolum['bolum_adi'], bolum['bolum_id'])
        self.bolum_combo.setFixedHeight(36)
        if self.is_edit and self.user_data.get('bolum_id'):
            index = self.bolum_combo.findData(self.user_data['bolum_id'])
            if index >= 0:
                self.bolum_combo.setCurrentIndex(index)
        form_layout.addRow("Bölüm:", self.bolum_combo)
        
        # Password (only for new users)
        if not self.is_edit:
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            self.password_input.setPlaceholderText("Min. 6 karakter")
            self.password_input.setFixedHeight(36)
            form_layout.addRow("Şifre:", self.password_input)
            
            self.password_confirm = QLineEdit()
            self.password_confirm.setEchoMode(QLineEdit.Password)
            self.password_confirm.setPlaceholderText("Şifreyi tekrar girin")
            self.password_confirm.setFixedHeight(36)
            form_layout.addRow("Şifre Tekrar:", self.password_confirm)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setFixedWidth(120)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("💾 Kaydet")
        save_btn.setFixedHeight(40)
        save_btn.setFixedWidth(120)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        save_btn.clicked.connect(self.accept)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        # Initial role check
        self.on_role_changed(self.role_combo.currentText())

    def on_role_changed(self, role):
        """Enable/disable bolum based on role"""
        is_koordinator = role == "Bölüm Koordinatörü"
        self.bolum_combo.setEnabled(is_koordinator)
        if not is_koordinator:
            self.bolum_combo.setCurrentIndex(0)

    def get_data(self):
        """Get form data"""
        role = self.role_combo.currentText()
        bolum_id = self.bolum_combo.currentData() if role == "Bölüm Koordinatörü" else None

        data = {
            'ad_soyad': self.name_input.text().strip(),
            'email': self.email_input.text().strip(),
            'role': role,
            'bolum_id': bolum_id
        }

        if not self.is_edit:
            data['password'] = self.password_input.text().strip()
            data['password_confirm'] = self.password_confirm.text().strip()

        return data


class SifreDialog(QDialog):
    """Dialog for changing user password"""

    def __init__(self, user_name, parent=None):
        super().__init__(parent)
        self.user_name = user_name

        self.setWindowTitle(f"Şifre Değiştir - {user_name}")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Info
        info = QLabel(f" {self.user_name} kullanıcısı için yeni şifre belirleyin:")
        info.setWordWrap(True)
        info.setStyleSheet("color: #374151; font-size: 13px; padding: 8px;")
        layout.addWidget(info)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Min. 6 karakter")
        self.password_input.setFixedHeight(36)
        form_layout.addRow("Yeni Şifre:", self.password_input)

        self.password_confirm = QLineEdit()
        self.password_confirm.setEchoMode(QLineEdit.Password)
        self.password_confirm.setPlaceholderText("Şifreyi tekrar girin")
        self.password_confirm.setFixedHeight(36)
        form_layout.addRow("Şifre Tekrar:", self.password_confirm)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        cancel_btn = QPushButton("İptal")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setFixedWidth(120)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Şifreyi Değiştir")
        save_btn.setFixedHeight(40)
        save_btn.setFixedWidth(160)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d97706;
            }
        """)
        save_btn.clicked.connect(self.accept)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def get_password(self):
        """Get password data"""
        return {
            'password': self.password_input.text().strip(),
            'password_confirm': self.password_confirm.text().strip()
        }


class KullaniciYonetimiView(QWidget):
    """Admin user management view"""

    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.user_model = UserModel(db)
        self.bolum_model = BolumModel(db)

        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Kullanıcı Yönetimi")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #111827;")

        subtitle = QLabel("Tüm kullanıcıları yönetin, yeni koordinatörler ekleyin")
        subtitle.setStyleSheet("color: #6b7280; font-size: 13px;")

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        add_btn = QPushButton("➕ Yeni Kullanıcı Ekle")
        add_btn.setFixedHeight(44)
        add_btn.setFixedWidth(200)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self.add_user)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(add_btn)

        layout.addWidget(header)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #e5e7eb; max-height: 1px;")
        layout.addWidget(divider)

        # Table Container
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
        """)
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Ad Soyad", "E-posta", "Rol", "Bölüm", "Son Giriş", "İşlemler"
        ])

        # Behavior and scrolling
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Disable editing
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setTextElideMode(Qt.ElideMiddle)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        # Column widths - Percentage based
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setSectionsMovable(False)
        header.setSectionsClickable(False)
        header.setHighlightSections(False)

        # Set all to Stretch for proportional sizing
        for i in range(6):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        header.setFixedHeight(40)
        self.table.verticalHeader().setDefaultSectionSize(65)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: #f3f4f6;
            }
            QTableWidget::item {
                padding: 10px 12px;
                border-bottom: 1px solid #f3f4f6;
                color: #374151;
            }
            QTableWidget::item:selected {
                background-color: #dbeafe;
                color: #1e40af;
            }
            QTableWidget::item:alternate {
                background-color: #f9fafb;
            }
            QHeaderView::section {
                background-color: #f9fafb;
                padding: 12px 12px;
                border: none;
                border-bottom: 2px solid #e5e7eb;
                font-weight: bold;
                color: #111827;
                font-size: 13px;
            }
        """)

        table_layout.addWidget(self.table)
        layout.addWidget(table_container)

    def load_users(self):
        """Load all users"""
        try:
            # Get all users except current admin
            query = """
                SELECT u.user_id, u.ad_soyad, u.email, u.role, u.bolum_id, u.son_giris,
                       b.bolum_adi
                FROM users u
                LEFT JOIN bolumler b ON u.bolum_id = b.bolum_id
                WHERE u.aktif = TRUE AND u.user_id != %s
                ORDER BY u.role, u.ad_soyad
            """
            users = db.execute_query(query, (self.user_data.get('user_id'),))

            self.table.setRowCount(0)

            for user in users:
                row = self.table.rowCount()
                self.table.insertRow(row)

                # Ad Soyad
                name_item = QTableWidgetItem(user['ad_soyad'])
                name_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                self.table.setItem(row, 0, name_item)

                # Email
                email_item = QTableWidgetItem(user['email'])
                self.table.setItem(row, 1, email_item)

                # Role
                role_item = QTableWidgetItem(user['role'])
                if user['role'] == 'Admin':
                    role_item.setForeground(Qt.red)
                    role_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                else:
                    role_item.setForeground(Qt.blue)
                self.table.setItem(row, 2, role_item)

                # Bölüm
                bolum = user.get('bolum_adi', '-')
                dept_item = QTableWidgetItem(bolum)
                self.table.setItem(row, 3, dept_item)

                # Son Giriş
                son_giris = user.get('son_giris', '')
                if son_giris:
                    son_giris = son_giris.strftime('%d.%m.%Y %H:%M') if hasattr(son_giris, 'strftime') else str(son_giris)
                else:
                    son_giris = 'Hiç giriş yok'
                login_item = QTableWidgetItem(son_giris)
                login_item.setForeground(Qt.darkGray)
                self.table.setItem(row, 4, login_item)

                # Actions - Compact buttons aligned left
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(4, 2, 4, 2)
                action_layout.setSpacing(6)

                edit_btn = QPushButton("Düzenle")
                edit_btn.setFixedHeight(32)
                edit_btn.setFixedWidth(75)
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #10b981;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-weight: 600;
                        font-size: 11px;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        background-color: #059669;
                    }
                """)
                edit_btn.setCursor(Qt.PointingHandCursor)
                edit_btn.clicked.connect(lambda checked=False, u=user: self.edit_user(u))

                password_btn = QPushButton("Şifre")
                password_btn.setFixedHeight(32)
                password_btn.setFixedWidth(60)
                password_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3b82f6;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-weight: 600;
                        font-size: 11px;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        background-color: #2563eb;
                    }
                """)
                password_btn.setCursor(Qt.PointingHandCursor)
                password_btn.clicked.connect(lambda checked=False, u=user: self.change_password(u))

                delete_btn = QPushButton("Sil")
                delete_btn.setFixedHeight(32)
                delete_btn.setFixedWidth(50)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ef4444;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-weight: 600;
                        font-size: 11px;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        background-color: #dc2626;
                    }
                """)
                delete_btn.setCursor(Qt.PointingHandCursor)
                delete_btn.clicked.connect(lambda checked=False, u=user: self.delete_user(u))

                action_layout.addWidget(edit_btn)
                action_layout.addWidget(password_btn)
                action_layout.addWidget(delete_btn)
                action_layout.addStretch()

                self.table.setCellWidget(row, 5, action_widget)

            # Adjust columns after loading
            self.adjust_columns()

            logger.info(f"Loaded {len(users)} users")

        except Exception as e:
            logger.error(f"Error loading users: {e}")
            ModernMessageBox.error(self, "Hata", "Kullanıcılar yüklenirken oluştu", f"{str(e)}")

    def add_user(self):
        """Add new user"""
        try:
            # Get bolumler
            bolumler = self.bolum_model.get_all()

            dialog = KullaniciDialog(bolumler=bolumler, parent=self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()

                # Validation
                if not data['ad_soyad']:
                    ModernMessageBox.warning(self, "Uyarı", "⚠️ Ad Soyad giriniz!")
                    return

                if not data['email']:
                    ModernMessageBox.warning(self, "Uyarı", "⚠️ E-posta giriniz!")
                    return

                if not data['password']:
                    ModernMessageBox.warning(self, "Uyarı", "⚠️ Şifre giriniz!")
                    return

                if len(data['password']) < 6:
                    ModernMessageBox.warning(self, "Uyarı", "⚠️ Şifre en az 6 karakter olmalıdır!")
                    return

                if data['password'] != data['password_confirm']:
                    ModernMessageBox.warning(self, "Uyarı", "⚠️ Şifreler eşleşmiyor!")
                    return

                if data['role'] == 'Bölüm Koordinatörü' and not data['bolum_id']:
                    ModernMessageBox.warning(self, "Uyarı", "⚠️ Koordinatör için bölüm seçmelisiniz!")
                    return

                # Hash password
                hashed_password = PasswordUtils.hash_password(data['password'])

                # Insert user
                user_data = {
                    'ad_soyad': data['ad_soyad'],
                    'email': data['email'],
                    'password_hash': hashed_password,
                    'role': data['role'],
                    'bolum_id': data['bolum_id']
                }

                user_id = self.user_model.insert_user(user_data)

                ModernMessageBox.success(
                    self, "Başarılı", f"Kullanıcı başarıyla eklendi!", f"\n"
                    f"E-posta: {data['email']}\n"
                    f"Şifre: {data['password']}\n\n"
                    f"Bu bilgileri kullanıcıya iletin."
                )

                self.load_users()

        except Exception as e:
            logger.error(f"Error adding user: {e}")
            ModernMessageBox.error(self, "Hata", "Kullanıcı eklenirken oluştu", f"{str(e)}")

    def edit_user(self, user):
        """Edit user"""
        try:
            # Get bolumler
            bolumler = self.bolum_model.get_all()

            dialog = KullaniciDialog(user_data=user, bolumler=bolumler, parent=self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()

                # Validation
                if not data['ad_soyad']:
                    ModernMessageBox.warning(self, "Uyarı", "⚠️ Ad Soyad giriniz!")
                    return

                if not data['email']:
                    ModernMessageBox.warning(self, "Uyarı", "⚠️ E-posta giriniz!")
                    return

                if data['role'] == 'Bölüm Koordinatörü' and not data['bolum_id']:
                    ModernMessageBox.warning(self, "Uyarı", "⚠️ Koordinatör için bölüm seçmelisiniz!")
                    return

                # Update user
                self.user_model.update_user(user['user_id'], data)

                QMessageBox.information(
                    self,
                    "Başarılı",
                    "✅ Kullanıcı başarıyla güncellendi!"
                )

                self.load_users()

        except Exception as e:
            logger.error(f"Error editing user: {e}")
            ModernMessageBox.error(self, "Hata", "Kullanıcı güncellenirken oluştu", f"{str(e)}")

    def change_password(self, user):
        """Change user password"""
        try:
            dialog = SifreDialog(user['ad_soyad'], parent=self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_password()

                # Validation
                if not data['password']:
                    ModernMessageBox.warning(self, "Uyarı", "⚠️ Şifre giriniz!")
                    return

                if len(data['password']) < 6:
                    ModernMessageBox.warning(self, "Uyarı", "⚠️ Şifre en az 6 karakter olmalıdır!")
                    return

                if data['password'] != data['password_confirm']:
                    ModernMessageBox.warning(self, "Uyarı", "⚠️ Şifreler eşleşmiyor!")
                    return

                # Hash password
                hashed_password = PasswordUtils.hash_password(data['password'])

                # Update password
                self.user_model.update_password(user['user_id'], hashed_password)

                ModernMessageBox.success(
                    self, "Başarılı", f"Şifre başarıyla değiştirildi!", f"\n"
                    f"Kullanıcı: {user['ad_soyad']}\n"
                    f"E-posta: {user['email']}\n"
                    f"Yeni Şifre: {data['password']}\n\n"
                    f"Bu bilgileri kullanıcıya iletin."
                )

        except Exception as e:
            logger.error(f"Error changing password: {e}")
            ModernMessageBox.error(self, "Hata", "Şifre değiştirilirken oluştu", f"{str(e)}")

    def delete_user(self, user):
        """Delete user"""
        try:
            confirmed = ModernMessageBox.question(
                self,
                "Kullanıcı Sil",
                f"{user['ad_soyad']} kullanıcısını silmek istediğinizden emin misiniz?\n\n"
                f"E-posta: {user['email']}\n"
                f"Rol: {user['role']}\n\n"
                f"Bu işlem geri alınamaz!"
            )

            if confirmed:
                self.user_model.delete_user(user['user_id'])

                QMessageBox.information(
                    self,
                    "Başarılı",
                    "✅ Kullanıcı başarıyla silindi!"
                )

                self.load_users()

        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            ModernMessageBox.error(self, "Hata", "Kullanıcı silinirken hata oluştu!", str(e))

    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        self.adjust_columns()

    def adjust_columns(self):
        """Adjust column widths proportionally based on percentages"""
        try:
            if not hasattr(self, 'table'):
                return

            # Get available width
            viewport_width = self.table.viewport().width()
            if viewport_width <= 0:
                return

            # Check if vertical scrollbar is visible
            vbar = self.table.verticalScrollBar()
            scrollbar_width = vbar.width() if vbar and vbar.isVisible() else 0

            # Available width for columns
            available_width = viewport_width - scrollbar_width

            # Column percentages (total = 100%)
            # Ad Soyad: 18%, E-posta: 24%, Rol: 12%, Bölüm: 18%, Son Giriş: 16%, İşlemler: 12%
            percentages = [0.18, 0.24, 0.12, 0.18, 0.16, 0.12]

            # Calculate and set column widths
            for col, percentage in enumerate(percentages):
                width = int(available_width * percentage)
                self.table.setColumnWidth(col, width)

        except Exception as e:
            logger.error(f"Error adjusting columns: {e}")