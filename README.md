# 🎓 Kocaeli Üniversitesi Sınav Takvimi Yönetim Sistemi

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.0+-purple.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)
![License](https://img.shields.io/badge/license-Proprietary-red.svg)

**Profesyonel ve Akıllı Sınav Programı Yönetim Sistemi**

Kocaeli Üniversitesi için özel olarak geliştirilmiş, yapay zeka destekli otomatik sınav programı oluşturma ve yönetim sistemi. Modern arayüz, güçlü algoritmalar ve kapsamlı raporlama özellikleri ile sınav organizasyonunu kolaylaştırır.

---

## 📋 İçindekiler

- [Hakkında](#-hakkında)
- [Ana Özellikler](#-ana-özellikler)
- [Teknolojiler](#-teknolojiler)
- [Sistem Gereksinimleri](#-sistem-gereksinimleri)
- [Kurulum](#-kurulum)
- [Yapılandırma](#️-yapılandırma)
- [Kullanım Kılavuzu](#-kullanım-kılavuzu)
- [Proje Yapısı](#-proje-yapısı)
- [Algoritmalar](#-algoritmalar)
- [Veritabanı Şeması](#-veritabanı-şeması)
- [Güvenlik](#-güvenlik)
- [Sorun Giderme](#-sorun-giderme)

---

## 🚀 Hakkında

Bu sistem, üniversitelerin karşılaştığı en karmaşık sorunlardan biri olan **sınav programı oluşturma** sürecini otomatikleştiren kapsamlı bir masaüstü uygulamasıdır.

### 🎯 Çözülen Sorunlar

- ✅ **Çakışma Yönetimi**: Öğrencilerin aynı anda birden fazla sınava girmesini önler
- ✅ **Derslik Optimizasyonu**: Derslikleri kapasite ve özelliklerine göre dengeli dağıtır
- ✅ **Zaman Planlaması**: Öğrenci yükünü günlere dengeli dağıtır
- ✅ **Oturma Düzeni**: Her sınav için otomatik ve adaletli oturma planı oluşturur
- ✅ **Raporlama**: Detaylı Excel ve PDF raporları ile tüm süreçleri şeffaf hale getirir

### 👥 Kullanıcı Rolleri

- **👨‍💼 Admin**: Sistem yönetimi, kullanıcı ve bölüm yönetimi
- **👨‍🏫 Koordinatör**: Sınav programı oluşturma, derslik ve ders yönetimi
- **📚 Okuyucu**: Sadece görüntüleme yetkisi

---

## ✨ Ana Özellikler

### 🤖 Akıllı Sınav Programı Oluşturma

**Çok Stratejili Algoritma:**
- 🎯 **Strateji 1**: Balanced Round-Robin - Dengeli dağılım odaklı
- 🚀 **Strateji 2**: Greedy Packing - Hızlı yerleştirme
- 🔄 **Strateji 3**: Random Shuffle - Farklı kombinasyonlar
- ⚡ **Paralel Deneme**: 5 farklı deneme eş zamanlı çalışır
- 📊 **Akıllı Puanlama**: 8 farklı kriter ile program kalitesi değerlendirmesi

**Kısıtlamalar (Constraints):**
- ❌ **Hard Constraints**: Öğrenci çakışmaları (mutlaka uyulmalı)
- ⚠️ **Soft Constraints**: Günlük limitler, boşluklar, derslik kullanımı (optimize edilir)

**Özellikleri:**
- Vize, Final, Bütünleme sınavları için ayrı programlar
- Günlük sınav sayısı limiti (sınıf bazlı)
- Öğrenci günlük sınav limiti
- Paralel sınav kontrolü
- Sınav süreleri arası ara süresi yönetimi
- Derslik kapasite kontrolü

### 🪑 Oturma Planı Oluşturma

**Round-Robin Dağıtım Algoritması:**
- 🔄 Dersliklere dengeli öğrenci dağılımı
- 📏 Kapasite kontrolü ile over-capacity önleme
- 🎲 Adil ve dengeli yerleştirme
- 📊 Sıra yapısına uygun (2'li, 3'lü, 4'lü düzenler)

**Görselleştirme:**
- 🗺️ İnteraktif derslik haritası
- 👤 Öğrenci detay kartları
- 📈 Derslik doluluk istatistikleri
- 🖨️ PDF ve Excel export

### 📊 Derslik Yönetimi

**Özellikler:**
- ➕ Derslik ekleme/düzenleme/silme
- 📐 Kapasite ve yerleşim planı tanımlama
- 🏢 Bina ve kat bazlı organizasyon
- 🎨 Sıra yapısı seçenekleri (2'li, 3'lü, 4'lü)
- 📊 Görsel durum göstergeleri
- 🔍 Arama ve filtreleme

### 📚 Ders ve Öğrenci Yönetimi

**Toplu Veri Yükleme:**
- 📥 Excel ile ders listesi yükleme
- 📥 Excel ile öğrenci listesi yükleme
- 🔄 Otomatik veri doğrulama
- ⚠️ Hata raporlama ve log tutma
- ✏️ Tekli ekleme/düzenleme/silme
- 🔍 Gelişmiş arama ve filtreleme

### 📄 Raporlama ve Export

**Desteklenen Formatlar:**
- 📗 **Excel (.xlsx)**: Detaylı tablolar, çoklu sayfa
- 📕 **PDF**: Profesyonel formatlanmış raporlar

**Rapor Türleri:**
- 📅 Sınav programı (genel)
- 🏫 Sınıf bazlı programlar
- 🏢 Derslik bazlı programlar
- 🪑 Oturma planları (görsel ve liste)
- 📊 İstatistiksel raporlar

### 🎨 Modern Arayüz

**Tasarım Özellikleri:**
- 🎨 KOÜ kurumsal renkleri (Yeşil tema)
- 🌓 Dark/Light tema desteği
- 📱 Responsive tasarım
- ✨ Smooth animasyonlar
- 💳 Modern kart tasarımları
- 🔔 Bildirim sistemi (toast messages)

---

## 🛠 Teknolojiler

### **Backend & Core**
```
Python 3.8+              # Ana programlama dili
PostgreSQL 12+           # İlişkisel veritabanı
psycopg2-binary         # PostgreSQL Python adaptörü
python-dotenv           # Ortam değişkenleri yönetimi
```

### **GUI Framework**
```
PySide6 (Qt6)           # Modern GUI framework
QtCore, QtWidgets       # UI bileşenleri
QtGui                   # Grafik ve görselleştirme
```

### **Data Processing**
```
pandas                  # Veri işleme ve analiz
openpyxl               # Excel okuma/yazma
xlrd                   # Excel okuma (eski format)
```

### **Document Generation**
```
reportlab              # PDF oluşturma
Pillow (PIL)           # Görsel işleme
```

### **Security**
```
bcrypt                 # Şifre hashleme
hashlib                # Hash fonksiyonları
secrets                # Güvenli rastgele değer üretimi
```

### **Utilities**
```
logging                # Uygulama loglama
datetime               # Tarih/saat işlemleri
typing                 # Type hints
dataclasses            # Veri sınıfları
```

---

## 💻 Sistem Gereksinimleri

### **Yazılım Gereksinimleri**

| Bileşen | Minimum | Önerilen |
|---------|---------|----------|
| **Python** | 3.8 | 3.10+ |
| **PostgreSQL** | 12.0 | 14.0+ |
| **İşletim Sistemi** | Windows 10 | Windows 11 |
| | macOS 10.14 | macOS 12+ |
| | Ubuntu 20.04 | Ubuntu 22.04+ |

### **Donanım Gereksinimleri**

| Bileşen | Minimum | Önerilen |
|---------|---------|----------|
| **İşlemci** | Dual-core 2.0 GHz | Quad-core 2.5+ GHz |
| **RAM** | 4 GB | 8 GB+ |
| **Disk** | 1 GB boş alan | 5 GB (SSD) |
| **Ekran** | 1280x720 | 1920x1080+ |

### **Python Bağımlılıkları**

Tüm gerekli paketler `requirements.txt` dosyasında listelenmiştir:

```txt
PySide6>=6.5.0
psycopg2-binary>=2.9.0
pandas>=2.0.0
openpyxl>=3.1.0
reportlab>=4.0.0
python-dotenv>=1.0.0
bcrypt>=4.0.0
Pillow>=10.0.0
xlrd>=2.0.0
```

---

## 🚀 Kurulum

### **1. Depoyu Klonlayın**

```bash
git clone https://github.com/your-org/sinav-takvimi-sistemi.git
cd sinav-takvimi-sistemi
```

### **2. Python Sanal Ortamı Oluşturun**

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### **3. Bağımlılıkları Yükleyin**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### **4. PostgreSQL Veritabanını Kurun**

**PostgreSQL'e bağlanın:**
```bash
psql -U postgres
```

**Veritabanı oluşturun:**
```sql
CREATE DATABASE sinav_takvimi_db;
\c sinav_takvimi_db
```

**SQL şemasını yükleyin:**
```bash
# PostgreSQL komut satırında
\i sinav_takvimi_final.sql

# Veya terminal'den
psql -U postgres -d sinav_takvimi_db -f sinav_takvimi_final.sql
```

### **5. Ortam Değişkenlerini Ayarlayın**

**.env dosyası oluşturun:**
```bash
# Kök dizinde .env dosyası oluşturun
touch .env  # macOS/Linux
New-Item .env  # Windows PowerShell
```

**Gerekli değişkenleri ekleyin:**
```env
# Veritabanı Ayarları
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sinav_takvimi_db
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Uygulama Ayarları
APP_ENV=production
APP_DEBUG=False
LOG_LEVEL=INFO

# Güvenlik
SECRET_KEY=your_secret_key_here
PASSWORD_MIN_LENGTH=8
SESSION_TIMEOUT=480

# Email (Opsiyonel)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### **6. Uygulamayı Başlatın**

```bash
python main.py
```

---

## ⚙️ Yapılandırma

### **Veritabanı Ayarları**

Veritabanı bağlantı ayarları `.env` dosyasında yapılır:

```env
DB_HOST=localhost          # Veritabanı sunucu adresi
DB_PORT=5432              # PostgreSQL portu (varsayılan: 5432)
DB_NAME=sinav_takvimi_db  # Veritabanı adı
DB_USER=postgres          # Kullanıcı adı
DB_PASSWORD=your_password # Şifre
```

### **Uygulama Ayarları**

`config/system_settings.json` dosyası UI ayarlarını içerir:

```json
{
  "app": {
    "theme": 0,        // 0: Light, 1: Dark
    "log_level": 2     // 0: DEBUG, 1: INFO, 2: WARNING, 3: ERROR
  }
}
```

### **Sınav Parametreleri**

Sınav oluşturma sırasında ayarlanabilen parametreler:

| Parametre | Açıklama | Varsayılan |
|-----------|----------|------------|
| **Sınav Süresi** | Her sınavın süresi (dakika) | 120 |
| **Ara Süresi** | Sınavlar arası mola (dakika) | 30 |
| **Günlük Limit** | Bir sınıfın günlük max sınav sayısı | 3 |
| **Öğrenci Limiti** | Bir öğrencinin günlük max sınav sayısı | 2 |
| **Paralel Sınav** | Aynı sınıfın paralel sınavı | Hayır |

---

## 📖 Kullanım Kılavuzu

### **İlk Giriş**

1. Uygulamayı başlatın: `python main.py`
2. Varsayılan kullanıcılardan biriyle giriş yapın:

| Rol | Email | Şifre |
|-----|-------|-------|
| **Admin** | admin@kocaeli.edu.tr | admin123 |
| **Koordinatör** | koordinator.bmu@kocaeli.edu.tr | koordinator123 |

⚠️ **ÖNEMLİ**: İlk girişten sonra mutlaka şifrenizi değiştirin!

### **Bölüm Seçimi**

Koordinatör olarak giriş yaptıktan sonra:
1. Yönetmek istediğiniz bölümü seçin
2. Bölüm bilgileri ana sayfada gösterilir
3. Bölüm değiştirmek için sol menüden "Bölüm Değiştir" seçeneğini kullanın

### **Derslik Ekleme**

**Adım adım:**
1. Sol menüden **"Derslikler"** sekmesine tıklayın
2. Sağ üstten **"Yeni Derslik Ekle"** butonuna basın
3. Formu doldurun:
   - **Derslik Adı**: Örn. "AMF-A102"
   - **Bina**: Örn. "AMF Blok"
   - **Kat**: Örn. "1"
   - **Kapasite**: Örn. "100"
   - **Sıra Yapısı**: 2'li, 3'lü veya 4'lü
   - **Durum**: Aktif/Pasif
4. **"Kaydet"** butonuna tıklayın

### **Ders Listesi Yükleme**

**Excel Formatı:**
```
| Ders Kodu | Ders Adı                  | Kredi | Yarıyıl | Sınıf | Ders Yapısı |
|-----------|---------------------------|-------|---------|-------|-------------|
| BMU101    | Programlamaya Giriş       | 3     | 1       | 1     | Zorunlu     |
| BMU102    | Matematik I               | 4     | 1       | 1     | Zorunlu     |
| BMU201    | Veri Yapıları             | 4     | 3       | 2     | Zorunlu     |
```

**Adımlar:**
1. **"Ders Yükle"** sekmesine gidin
2. **"Excel Seç"** ile dosyanızı seçin
3. **"Yükle"** butonuna tıklayın
4. Sonuçları inceleyin (başarılı/hatalı kayıtlar)

### **Öğrenci Listesi Yükleme**

**Excel Formatı:**
```
| Öğrenci No | Ad Soyad       | Sınıf | E-posta                   | Telefon     |
|------------|----------------|-------|---------------------------|-------------|
| 210101001  | Ahmet Yılmaz   | 2     | ahmet@kocaeli.edu.tr     | 5551234567  |
| 210101002  | Ayşe Demir     | 2     | ayse@kocaeli.edu.tr      | 5559876543  |
```

**Not:** Öğrenci-Ders ilişkileri ayrı bir Excel sayfasında veya farklı bir tabloda yüklenir.

### **Sınav Programı Oluşturma**

**Adım adım:**

1. **"Sınav Programı"** sekmesine gidin

2. **Parametreleri ayarlayın:**
   - 📅 **Sınav Tipi**: Vize / Final / Bütünleme
   - 📅 **Tarih Aralığı**: Başlangıç - Bitiş tarihi
   - ⏰ **Sınav Saatleri**: Başlangıç saati ve süre
   - ⏱️ **Ara Süresi**: Sınavlar arası mola
   - 📊 **Limitler**: 
     - Sınıf günlük limit (örn: 3 sınav)
     - Öğrenci günlük limit (örn: 2 sınav)
   - ⚙️ **Özel Ayarlar**:
     - ☑️ Paralel sınav yasağı
     - ☑️ Minimum çakışma eşiği

3. **"Programı Oluştur"** butonuna tıklayın

4. **Sonuçları inceleyin:**
   - 🎯 En iyi strateji
   - 📊 Puan detayları
   - ⚠️ Uyarılar ve öneriler
   - 📅 Günlük dağılım

5. **Programı kaydedin:**
   - ✅ **"Programı Kaydet"** ile veritabanına kaydedin
   - 📥 **"Excel'e Aktar"** ile dosya indirin
   - 📄 **"PDF Oluştur"** ile PDF rapor alın

### **Oturma Planı Oluşturma**

**Adım adım:**

1. **"Oturma Planı"** sekmesine gidin

2. **Sınav seçin:**
   - Açılır listeden ilgili sınavı seçin
   - Sınav detayları (tarih, saat, öğrenci sayısı) gösterilir

3. **Derslikleri seçin:**
   - Kullanılacak derslikleri işaretleyin
   - Toplam kapasite otomatik hesaplanır

4. **"Oturma Planı Oluştur"** butonuna tıklayın

5. **Sonuçları görüntüleyin:**
   - 🗺️ **Görsel Harita**: Derslik yerleşimlerini görün
   - 📋 **Liste Görünümü**: Tablo formatında öğrenci listesi
   - 📊 **İstatistikler**: Derslik doluluk oranları

6. **Planı kaydedin ve dışa aktarın:**
   - ✅ **"Planı Kaydet"**: Veritabanına kaydet
   - 📄 **"PDF İndir"**: Görsel oturma planı
   - 📗 **"Excel İndir"**: Liste formatında

---

## 📁 Proje Yapısı

```
PythonProject/
│
├── 📁 algorithms/              # Algoritma modülleri
│   ├── __init__.py
│   ├── attempt_manager.py     # Deneme yönetimi ve paralel işleme
│   ├── oturma_planlama.py     # Round-robin oturma planı algoritması
│   ├── scoring_system.py      # Program puanlama sistemi
│   └── sinav_planlama.py      # Çok stratejili sınav programı algoritması
│
├── 📁 config/                  # Yapılandırma dosyaları
│   ├── __init__.py
│   ├── system_settings.json   # UI ayarları (tema, log level)
│   └── user_preferences.json  # Kullanıcı tercihleri
│
├── 📁 controllers/             # İş mantığı katmanı (Business Logic)
│   ├── __init__.py
│   ├── ders_controller.py     # Ders CRUD işlemleri
│   ├── login_controller.py    # Kimlik doğrulama ve session
│   ├── ogrenci_controller.py  # Öğrenci CRUD işlemleri
│   └── sinav_controller.py    # Sınav CRUD işlemleri
│
├── 📁 models/                  # Veri erişim katmanı (Data Access Layer)
│   ├── __init__.py
│   ├── bolum_model.py         # Bölüm veritabanı işlemleri
│   ├── database.py            # Veritabanı bağlantı havuzu (Connection Pool)
│   ├── ders_model.py          # Ders veritabanı işlemleri
│   ├── derslik_model.py       # Derslik veritabanı işlemleri
│   ├── ogrenci_model.py       # Öğrenci veritabanı işlemleri
│   ├── oturma_model.py        # Oturma planı veritabanı işlemleri
│   ├── sinav_model.py         # Sınav veritabanı işlemleri
│   └── user_model.py          # Kullanıcı veritabanı işlemleri
│
├── 📁 styles/                  # UI Tema ve stiller
│   ├── __init__.py
│   ├── kou_theme.py           # KOÜ yeşil tema (koordinatör görünümleri)
│   └── theme.py               # Genel tema sistemi (login, main)
│
├── 📁 utils/                   # Yardımcı fonksiyonlar ve araçlar
│   ├── __init__.py
│   ├── edit_dialogs.py        # Düzenleme dialog'ları
│   ├── email_utils.py         # Email gönderme (şifre sıfırlama)
│   ├── excel_parser.py        # Excel okuma ve parsing
│   ├── export_utils.py        # PDF ve Excel export işlemleri
│   ├── modern_dialogs.py      # Modern bildirim ve onay dialog'ları
│   ├── password_utils.py      # Şifre güvenliği ve hashing
│   ├── validators.py          # Veri doğrulama fonksiyonları
│   └── view_helpers.py        # View yardımcı fonksiyonları
│
├── 📁 views/                   # Kullanıcı arayüzü (Presentation Layer)
│   ├── __init__.py
│   ├── login_view.py          # Giriş ekranı
│   ├── main_window.py         # Ana pencere ve dashboard
│   │
│   ├── 📁 admin/              # Admin görünümleri
│   │   ├── __init__.py
│   │   ├── bolum_yonetimi_view.py      # Bölüm yönetimi
│   │   ├── duyuru_yonetimi_view.py     # Duyuru yönetimi
│   │   └── kullanici_yonetimi_view.py  # Kullanıcı yönetimi
│   │
│   └── 📁 koordinator/        # Koordinatör görünümleri
│       ├── __init__.py
│       ├── ayarlar_view.py             # Ayarlar ve profil
│       ├── bolum_secim_view.py         # Bölüm seçim ekranı
│       ├── ders_yukle_view.py          # Ders yükleme ve yönetimi
│       ├── derslik_view.py             # Derslik yönetimi
│       ├── ogrenci_yukle_view.py       # Öğrenci yükleme ve yönetimi
│       ├── oturma_plani_view.py        # Oturma planı oluşturma
│       ├── program_result_dialog.py    # Program sonuç gösterimi
│       └── sinav_olustur_view.py       # Sınav programı oluşturma
│
├── 📁 logs/                    # Uygulama logları
│   └── app_YYYYMMDD.log       # Günlük log dosyaları
│
├── 📄 .env                     # Ortam değişkenleri (GİT'e eklenmez!)
├── 📄 main.py                  # Uygulama giriş noktası
├── 📄 requirements.txt         # Python bağımlılıkları
├── 📄 sinav_takvimi_final.sql # PostgreSQL veritabanı şeması
└── 📄 README.md               # Bu dosya
```

### **Mimari Katmanlar**

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │  ← views/
│  (PySide6 UI, User Interaction)         │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        Business Logic Layer             │  ← controllers/
│  (Validation, Processing, Rules)        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│       Data Access Layer                 │  ← models/
│  (Database Queries, CRUD)               │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│           Database                      │  ← PostgreSQL
│  (Data Storage)                         │
└─────────────────────────────────────────┘
```

---

## 🧮 Algoritmalar

### **1. Sınav Programı Oluşturma**

**Dosya**: `algorithms/sinav_planlama.py`

**Çok Stratejili Yaklaşım:**

```python
Stratejiler:
├── 1️⃣ BALANCED_ROUND_ROBIN
│   └── Dersleri günlere ve saatlere dengeli dağıt
│       ├── Öğrenci yükü dengeleme
│       └── Derslik kullanım optimizasyonu
│
├── 2️⃣ GREEDY_PACKING
│   └── İlk uygun yere hızlı yerleştirme
│       ├── Hızlı çözüm
│       └── Minimum boşluk
│
└── 3️⃣ RANDOM_SHUFFLE
    └── Rastgele sıralama ile farklı kombinasyonlar
        └── Lokal optimumdan kaçış
```

**Algoritma Akışı:**

```
1. BAŞLANGIÇ
   ├── Dersleri ve öğrencileri yükle
   ├── Çakışma matrisi oluştur
   └── Parametreleri al

2. PARALEl DENEME (5 farklı deneme)
   ├── Strateji 1: Balanced Round-Robin
   ├── Strateji 2: Greedy Packing  
   ├── Strateji 3: Random Shuffle
   ├── Strateji 1 (farklı seed)
   └── Strateji 2 (farklı seed)

3. HER DENEME İÇİN
   ├── Dersleri sırala (stratejiye göre)
   │
   ├── HER DERS İÇİN
   │   ├── Uygun zaman dilimlerini bul
   │   │   ├── ❌ Hard constraint kontrolü
   │   │   │   └── Öğrenci çakışması var mı?
   │   │   │
   │   │   ├── ⚠️ Soft constraint kontrolü
   │   │   │   ├── Günlük sınav limiti
   │   │   │   ├── Öğrenci günlük limiti
   │   │   │   ├── Ara süreleri
   │   │   │   └── Paralel sınav kuralı
   │   │   │
   │   │   └── En iyi zamanı seç
   │   │
   │   ├── Derslik ata
   │   │   ├── Kapasite kontrolü
   │   │   └── Dengeli dağılım
   │   │
   │   └── Yerleştir ve kaydet
   │
   └── Programı puanla (scoring_system)

4. EN İYİ PROGRAMI SEÇ
   ├── Tüm denemeleri karşılaştır
   ├── En yüksek puanı al
   └── Sonucu döndür
```

**Puanlama Kriterleri:**

| Kriter | Ağırlık | Açıklama |
|--------|---------|----------|
| **Öğrenci Günlük Limit** | 25% | Bir öğrencinin günlük max sınav sayısı |
| **Sınıf Günlük Limit** | 15% | Bir sınıfın günlük max sınav sayısı |
| **Öğrenci Boşlukları** | 20% | Öğrenci sınavları arası zaman boşlukları |
| **Sınıf Boşlukları** | 15% | Sınıf sınavları arası zaman boşlukları |
| **Derslik Kullanımı** | 10% | Dersliklerin dengeli kullanımı |
| **Dengeli Dağılım** | 10% | Sınavların günlere dengeli yayılması |
| **Sınav Süresi Opt** | 5% | Sınav sürelerinin optimizasyonu |

### **2. Oturma Planı Oluşturma**

**Dosya**: `algorithms/oturma_planlama.py`

**Round-Robin Dağıtım Algoritması:**

```
1. GİRİŞ
   ├── Sınav bilgilerini al
   ├── Öğrenci listesini al
   └── Derslik listesini al

2. DERSLİK BİLGİLERİNİ HAZIRLA
   ├── Her derslik için
   │   ├── Kapasite hesapla (satır × sütun)
   │   ├── Sıra yapısını belirle (2'li, 3'lü, 4'lü)
   │   └── current_seat_index = 0

3. ROUND-ROBIN DAĞITIM
   ├── classroom_index = 0
   │
   ├── HER ÖĞRENCİ İÇİN
   │   ├── Mevcut derslikteki boş yeri kontrol et
   │   │   ├── ✅ Boş yer var
   │   │   │   ├── Öğrenciyi yerleştir
   │   │   │   ├── current_seat_index++
   │   │   │   └── Sonraki derslİğe geç
   │   │   │
   │   │   └── ❌ Derslik dolu
   │   │       ├── Sonraki derslİğe geç
   │   │       └── Tüm derslikler dolu mu? → HATA
   │   │
   │   └── classroom_index = (index + 1) % derslik_sayısı

4. ÇIKIŞ
   └── Tüm öğrenciler yerleştirildi ✅
```

**Avantajları:**
- ✅ Dengeli dağılım (her derslik eşit sayıda öğrenci)
- ✅ Kapasite kontrolü (over-capacity önlenir)
- ✅ Hızlı çalışma (O(n) kompleksitesi)
- ✅ Adil yerleştirme

---

## 🗄 Veritabanı Şeması

### **Ana Tablolar**

```sql
📁 users                    -- Kullanıcılar
├── user_id (PK)
├── username
├── email
├── password_hash          -- BCrypt hash
├── role                   -- admin, koordinator, okuyucu
├── bolum_id (FK)
├── is_active
└── created_at

📁 bolumler                 -- Bölümler
├── bolum_id (PK)
├── bolum_kodu
├── bolum_adi
├── fakulte
└── created_at

📁 dersler                  -- Dersler
├── ders_id (PK)
├── ders_kodu
├── ders_adi
├── kredi
├── sinif
├── yarisil
├── ders_yapisi            -- zorunlu, secmeli
├── bolum_id (FK)
└── created_at

📁 derslikler               -- Derslikler
├── derslik_id (PK)
├── derslik_adi
├── bina
├── kat
├── kapasite
├── sira_yapisi            -- 2, 3, 4 (kişilik)
├── satir_sayisi
├── sutun_sayisi
├── durum                  -- aktif, pasif
├── bolum_id (FK)
└── created_at

📁 ogrenciler               -- Öğrenciler
├── ogrenci_id (PK)
├── ogrenci_no
├── ad_soyad
├── sinif
├── email
├── telefon
├── bolum_id (FK)
└── created_at

📁 ogrenci_dersler          -- Öğrenci-Ders İlişkisi
├── ogrenci_ders_id (PK)
├── ogrenci_id (FK)
├── ders_id (FK)
└── kayit_tarihi

📁 sinav_programlari        -- Sınav Programları (Header)
├── program_id (PK)
├── bolum_id (FK)
├── sinav_tipi             -- Vize, Final, Butunleme
├── donem_yil
├── donem_adi
├── olusturma_tarihi
├── olusturan_user_id (FK)
└── aciklama

📁 sinavlar                 -- Sınavlar (Detail)
├── sinav_id (PK)
├── program_id (FK)
├── ders_id (FK)
├── tarih
├── baslangic_saati
├── bitis_saati
├── sure_dakika
├── ogrenci_sayisi
└── created_at

📁 sinav_derslikleri        -- Sınav-Derslik İlişkisi
├── sinav_derslik_id (PK)
├── sinav_id (FK)
├── derslik_id (FK)
└── ogrenci_sayisi

📁 oturma_planlari          -- Oturma Planları
├── oturma_id (PK)
├── sinav_id (FK)
├── ogrenci_no
├── derslik_id (FK)
├── satir                  -- Sıra numarası
├── sutun                  -- Sütun numarası
└── created_at
```

### **İlişki Diyagramı**

```
┌──────────┐         ┌──────────┐
│  users   │────────>│ bolumler │
└──────────┘         └─────┬────┘
                           │
      ┌────────────────────┼────────────────────┐
      │                    │                    │
      ▼                    ▼                    ▼
┌──────────┐         ┌──────────┐         ┌──────────┐
│ dersler  │         │derslikler│         │ogrenciler│
└────┬─────┘         └────┬─────┘         └────┬─────┘
     │                    │                    │
     │    ┌───────────────┘                    │
     │    │               ┌────────────────────┘
     │    │               │
     ▼    ▼               ▼
┌────────────────────────────┐
│  sinav_programlari         │
└──────────┬─────────────────┘
           │
           ▼
     ┌──────────┐
     │ sinavlar │<────────┐
     └────┬─────┘         │
          │               │
     ┌────┴─────┬─────────┴───────┐
     ▼          ▼                 ▼
┌─────────────┐ ┌─────────────────┐
│sinav_       │ │oturma_planlari  │
│derslikleri  │ └─────────────────┘
└─────────────┘
```

---

## 🔐 Güvenlik

### **Şifreleme ve Hashing**

```python
# BCrypt ile şifre hashleme
import bcrypt

# Şifre oluşturma
password = "user_password"
salt = bcrypt.gensalt(rounds=12)  # 12 rounds (güvenli)
hashed = bcrypt.hashpw(password.encode(), salt)

# Şifre doğrulama
is_valid = bcrypt.checkpw(password.encode(), hashed)
```

### **SQL Injection Koruması**

```python
# ❌ YANLIŞ - SQL Injection riski
query = f"SELECT * FROM users WHERE email = '{user_email}'"

# ✅ DOĞRU - Parametreli sorgu
query = "SELECT * FROM users WHERE email = %s"
cursor.execute(query, (user_email,))
```

### **Güvenlik Kontrol Listesi**

- ✅ Şifreler BCrypt ile hashlenmiş (salt rounds: 12)
- ✅ SQL injection koruması (parametreli sorgular)
- ✅ Session timeout mekanizması (8 saat)
- ✅ Role-based access control (RBAC)
- ✅ `.env` dosyası git'e eklenmemiş (`.gitignore`)
- ✅ Minimum şifre gereksinimleri (8 karakter, büyük/küçük harf, rakam)
- ✅ Başarısız giriş denemeleri loglanıyor
- ✅ Hassas bilgiler loglanmıyor
- ✅ Database connection pooling (kaynak yönetimi)

---

## 🐛 Sorun Giderme

### **1. Veritabanı Bağlantı Hatası**

**Hata:**
```
psycopg2.OperationalError: could not connect to server
```

**Çözüm:**
```bash
# 1. PostgreSQL servisini kontrol edin
sudo systemctl status postgresql  # Linux
Get-Service postgresql*           # Windows

# 2. PostgreSQL'i başlatın
sudo systemctl start postgresql   # Linux
Start-Service postgresql-x64-12   # Windows

# 3. .env dosyasını kontrol edin
cat .env | grep DB_

# 4. Bağlantıyı test edin
psql -h localhost -U postgres -d sinav_takvimi_db
```

### **2. Import Hatası**

**Hata:**
```
ModuleNotFoundError: No module named 'PySide6'
```

**Çözüm:**
```bash
# 1. Sanal ortamın aktif olduğundan emin olun
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# 2. Bağımlılıkları yeniden yükleyin
pip install --upgrade pip
pip install -r requirements.txt
```

### **3. Excel Yükleme Hatası**

**Çözüm:**
```
1. Excel dosyasının .xlsx formatında olduğundan emin olun
2. İlk satırda sütun başlıklarının olduğundan emin olun
3. Boş satırları silin
4. Özel karakterleri kontrol edin
```

---

## 📞 İletişim ve Destek

**Kocaeli Üniversitesi**
- 🌐 Website: [www.kocaeli.edu.tr](https://www.kocaeli.edu.tr)
- 📧 Email: bilgiislem@kocaeli.edu.tr
- ☎️ Telefon: +90 (262) 303 10 00

---

## 📜 Lisans

Bu proje **Kocaeli Üniversitesi**'ne aittir ve özel lisans altındadır.  
**Tüm hakları saklıdır © 2025 Kocaeli Üniversitesi**

---

## 🔄 Versiyon Geçmişi

### **v2.0.0** (2025-01-30)
- ✨ Çok stratejili sınav programı algoritması
- ✨ Round-robin oturma planı algoritması
- ✨ Dengeli derslik dağıtımı
- 🔒 Güvenlik iyileştirmeleri (.env kullanımı)
- 🧹 Kod temizliği (~200 satır azaltma)
- 📊 Geliştirilmiş puanlama sistemi
- 🎨 UI/UX iyileştirmeleri

### **v1.0.0** (2024-12-15)
- 🎉 İlk stabil sürüm
- ✅ Temel CRUD işlemleri
- ✅ Excel import/export
- ✅ PDF rapor oluşturma

---

**Son Güncelleme:** 30 Ocak 2025  
**Dokümantasyon Versiyonu:** 2.0.0

---

<div align="center">

**⭐ Bu proje Kocaeli Üniversitesi'nin dijital dönüşüm yolculuğunun bir parçasıdır ⭐**

</div>
