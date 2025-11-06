"""
Kocaeli Üniversitesi Sınav Takvimi Sistemi
Tek Pencere Mimarisi - Login ve Ana Ekran
"""
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMessageBox, QStackedWidget
from PySide6.QtCore import Qt

from views.login_view import LoginView
from views.main_window import MainWindow
from styles.theme import KocaeliTheme
from models.database import db
from utils.modern_dialogs import ModernMessageBox


def setup_logging():
    """Setup application logging"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 70)
    logger.info("Kocaeli Üniversitesi Sınav Takvimi Sistemi - Başlatılıyor")
    logger.info("=" * 70)
    
    return logger


class SingleWindowApp(QStackedWidget):
    """Single window application - Login and Main screens"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Window setup
        self.setWindowTitle("KOÜ Sınav Takvimi Sistemi")
        self.setMinimumSize(1400, 800)
        
        if not self.check_database():
            return
        
        # Create login page
        self.login_page = LoginView()
        self.login_page.login_success.connect(self.on_login_success)
        self.addWidget(self.login_page)
        
        # Main window will be created after login
        self.main_page = None
        
        # Show login page
        self.setCurrentWidget(self.login_page)
        self.showMaximized()
        
        self.logger.info("✅ Uygulama başlatıldı - Login ekranı")
    
    def check_database(self):
        """Check database connection"""
        try:
            if db.test_connection():
                self.logger.info("✅ Veritabanı bağlantısı başarılı")
                return True
            else:
                self.logger.error("❌ Veritabanı bağlantısı başarısız")
                self.show_database_error()
                return False
        except Exception as e:
            self.logger.error(f"❌ Veritabanı hatası: {e}")
            self.show_database_error(str(e))
            return False
    
    def show_database_error(self, error_msg=""):
        """Show database connection error"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Veritabanı Bağlantı Hatası")
        msg.setText("Veritabanına bağlanılamadı!")
        
        if error_msg:
            msg.setInformativeText(
                f"Hata: {error_msg}\n\n"
                "Lütfen veritabanı ayarlarınızı kontrol edin (.env dosyası)."
            )
        else:
            msg.setInformativeText(
                "PostgreSQL servisinin çalıştığından ve .env dosyasının "
                "doğru yapılandırıldığından emin olun."
            )
        
        msg.setStandardButtons(QMessageBox.Retry | QMessageBox.Close)
        msg.setDefaultButton(QMessageBox.Retry)
        
        result = msg.exec()
        
        if result == QMessageBox.Retry:
            if self.check_database():
                QMessageBox.information(
                    self,
                    "Başarılı",
                    "Veritabanı bağlantısı başarılı!"
                )
        else:
            sys.exit(1)
    
    def on_login_success(self, user_data):
        """Handle successful login - Switch to main window"""
        self.logger.info(f"✅ Kullanıcı girişi başarılı: {user_data['email']}")
        
        # Create main page if not exists
        if not self.main_page:
            self.main_page = MainWindow(user_data)
            self.main_page.logout_requested.connect(self.on_logout)
            self.addWidget(self.main_page)
        
        # Switch to main page
        self.setCurrentWidget(self.main_page)
        self.logger.info("Ana ekran gösteriliyor")
    
    def on_logout(self):
        """Handle logout - Switch back to login"""
        self.logger.info("Kullanıcı çıkış yaptı")
        
        # Remove main page
        if self.main_page:
            self.removeWidget(self.main_page)
            self.main_page.deleteLater()
            self.main_page = None
        
        # Create fresh login page
        self.login_page = LoginView()
        self.login_page.login_success.connect(self.on_login_success)
        self.insertWidget(0, self.login_page)
        
        # Switch to login page
        self.setCurrentWidget(self.login_page)
        self.logger.info("Login ekranına dönüldü")
    
    def closeEvent(self, event):
        """Handle window close"""
        try:
            # Close database connections
            db.close_all_connections()
            self.logger.info("Veritabanı bağlantıları kapatıldı")
            
            self.logger.info("=" * 70)
            self.logger.info("Uygulama kapatıldı")
            self.logger.info("=" * 70)
            
            event.accept()
        except Exception as e:
            self.logger.error(f"Cleanup hatası: {e}")
            event.accept()


class Application:
    """Main application class"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.logger = setup_logging()
        self.main_window = None
        
        # Set application properties
        self.app.setApplicationName("KOÜ Sınav Takvimi Sistemi")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("Kocaeli Üniversitesi")
        
        # Apply theme
        self.app.setStyle("Fusion")
        self.app.setPalette(KocaeliTheme.get_color_palette())
        
        # Apply global stylesheet for oval borders and no focus outlines
        self.app.setStyleSheet("""
            /* Global oval borders and no focus outlines */
            * {
                outline: none;
                border: none;
            }
            
            QWidget:focus {
                outline: none;
                border: none;
            }
            
            QPushButton {
                border-radius: 12px;
                outline: none;
            }
            
            QPushButton:focus {
                outline: none;
                border: 2px solid transparent;
            }
            
            QLineEdit {
                border-radius: 10px;
                outline: none;
            }
            
            QLineEdit:focus {
                outline: none;
            }
            
            QComboBox {
                border-radius: 10px;
                outline: none;
            }
            
            QComboBox:focus {
                outline: none;
            }
            
            QSpinBox, QDoubleSpinBox {
                border-radius: 8px;
                outline: none;
            }
            
            QSpinBox:focus, QDoubleSpinBox:focus {
                outline: none;
            }
            
            QTableWidget {
                border-radius: 12px;
                outline: none;
            }
            
            QTableWidget:focus {
                outline: none;
            }
            
            QFrame {
                border-radius: 16px;
            }
            
            QGroupBox {
                border-radius: 12px;
            }
            
            QTabWidget::pane {
                border-radius: 12px;
            }
            
            QDialog {
                border-radius: 16px;
            }
            
            QMessageBox {
                border-radius: 16px;
            }
            
            /* Menu items - no extra borders */
            QMenu {
                border-radius: 12px;
                outline: none;
            }
            
            QMenu::item:selected {
                border-radius: 8px;
                outline: none;
            }
        """)

    def run(self):
        """Run application"""
        try:
            # Create and show main window
            self.main_window = SingleWindowApp()

            # Run app
            exit_code = self.app.exec()
            return exit_code

        except Exception as e:
            self.logger.error(f"❌ Kritik hata: {e}", exc_info=True)

            ModernMessageBox.error(
                None, "Kritik Hata", "Uygulama beklenmeyen biryla karşılaştı", f"\n{str(e)}\n\n"
                "Detaylar log dosyasında bulunabilir."
            )

            return 1


def main():
    """Main entry point"""
    # Set high DPI scaling (Qt6 has this enabled by default)
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        try:
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        except AttributeError:
            pass  # Qt6 doesn't need this

    # Create and run application
    app = Application()
    sys.exit(app.run())


if __name__ == "__main__":
    main()