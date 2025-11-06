DROP DATABASE IF EXISTS sinav_takvimi_db;
CREATE DATABASE sinav_takvimi_db
    ENCODING = 'UTF8'
    LC_COLLATE = 'tr_TR.UTF-8'
    LC_CTYPE = 'tr_TR.UTF-8';
\c sinav_takvimi_db;
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
SELECT pg_reload_conf();
CREATE TYPE role_enum AS ENUM ('Admin', 'Bölüm Koordinatörü');
CREATE TYPE sinav_tipi_enum AS ENUM ('Vize', 'Final', 'Bütünleme');
CREATE TYPE ders_yapisi_enum AS ENUM ('Zorunlu', 'Seçmeli');
CREATE TYPE import_tipi_enum AS ENUM ('Ders Listesi', 'Öğrenci Listesi');
CREATE TABLE password_reset_tokens (
    token_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_reset_token ON password_reset_tokens(token) WHERE used = FALSE;
CREATE INDEX idx_reset_user ON password_reset_tokens(user_id);
CREATE INDEX idx_reset_expires ON password_reset_tokens(expires_at) WHERE used = FALSE;
CREATE TABLE login_attempts (
    attempt_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    user_id INT REFERENCES users(user_id) ON DELETE SET NULL,
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(100),
    ip_address VARCHAR(45),
    user_agent TEXT,
    attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_login_email_time ON login_attempts(email, attempt_time DESC);
CREATE INDEX idx_login_ip ON login_attempts(ip_address, attempt_time DESC);
CREATE INDEX idx_login_success ON login_attempts(success, attempt_time DESC);
CREATE TABLE active_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    CONSTRAINT chk_session_expire CHECK (expires_at > created_at)
);
CREATE INDEX idx_session_user ON active_sessions(user_id);
CREATE INDEX idx_session_activity ON active_sessions(last_activity);
CREATE TYPE audit_action_enum AS ENUM (
    'INSERT', 'UPDATE', 'DELETE',
    'LOGIN', 'LOGOUT',
    'PASSWORD_CHANGE', 'PASSWORD_RESET',
    'EXPORT', 'IMPORT'
);
CREATE TABLE audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE SET NULL,
    action audit_action_enum NOT NULL,
    table_name VARCHAR(50),
    record_id INT,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_audit_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_table ON audit_logs(table_name, created_at DESC);
CREATE INDEX idx_audit_action ON audit_logs(action, created_at DESC);
CREATE TYPE email_status_enum AS ENUM ('pending', 'sent', 'failed', 'cancelled');
CREATE TABLE email_queue (
    email_id SERIAL PRIMARY KEY,
    to_email VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body_text TEXT,
    body_html TEXT,
    email_type VARCHAR(50),
    priority INT DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    status email_status_enum DEFAULT 'pending',
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    last_error TEXT,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scheduled_for TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_email_status ON email_queue(status, priority DESC, scheduled_for);
CREATE INDEX idx_email_type ON email_queue(email_type, created_at DESC);
CREATE TABLE system_settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value TEXT NOT NULL,
    data_type VARCHAR(20) DEFAULT 'string',
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    updated_by INT REFERENCES users(user_id) ON DELETE SET NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO system_settings (setting_key, setting_value, data_type, description) VALUES
('max_login_attempts', '5', 'int', 'Maksimum başarısız giriş denemesi'),
('account_lock_duration', '15', 'int', 'Hesap kilitleme süresi (dakika)'),
('password_reset_expiry', '15', 'int', 'Şifre sıfırlama token süresi (dakika)'),
('session_timeout', '480', 'int', 'Oturum zaman aşımı (dakika)'),
('min_password_length', '8', 'int', 'Minimum şifre uzunluğu');
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS son_sifre_degisimi TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INT DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS account_locked_until TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE users ADD CONSTRAINT chk_failed_attempts
CHECK (failed_login_attempts >= 0 AND failed_login_attempts <= 10);
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
CREATE OR REPLACE FUNCTION log_login_attempt(
    p_email VARCHAR,
    p_success BOOLEAN,
    p_failure_reason VARCHAR DEFAULT NULL,
    p_ip_address VARCHAR DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
) RETURNS void AS $$
DECLARE
    v_user_id INT;
BEGIN
    SELECT user_id INTO v_user_id FROM users WHERE email = p_email;
    INSERT INTO login_attempts (email, user_id, success, failure_reason, ip_address, user_agent)
    VALUES (p_email, v_user_id, p_success, p_failure_reason, p_ip_address, p_user_agent);
    IF NOT p_success AND v_user_id IS NOT NULL THEN
        UPDATE users
        SET failed_login_attempts = failed_login_attempts + 1
        WHERE user_id = v_user_id;
        IF (SELECT failed_login_attempts FROM users WHERE user_id = v_user_id) >= 5 THEN
            UPDATE users
            SET account_locked_until = CURRENT_TIMESTAMP + INTERVAL '15 minutes'
            WHERE user_id = v_user_id;
        END IF;
    END IF;
    IF p_success AND v_user_id IS NOT NULL THEN
        UPDATE users
        SET failed_login_attempts = 0,
            account_locked_until = NULL,
            son_giris = CURRENT_TIMESTAMP
        WHERE user_id = v_user_id;
    END IF;
END;
$$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    DELETE FROM password_reset_tokens
    WHERE expires_at < CURRENT_TIMESTAMP
       OR (used = TRUE AND used_at < CURRENT_TIMESTAMP - INTERVAL '7 days');
    DELETE FROM login_attempts
    WHERE attempt_time < CURRENT_TIMESTAMP - INTERVAL '90 days';
    DELETE FROM active_sessions
    WHERE expires_at < CURRENT_TIMESTAMP;
    RAISE NOTICE 'Expired tokens and old logs cleaned up';
END;
$$ LANGUAGE plpgsql;
CREATE TABLE bolumler (
    bolum_id SERIAL PRIMARY KEY,
    bolum_adi VARCHAR(100) NOT NULL UNIQUE,
    bolum_kodu VARCHAR(20) NOT NULL UNIQUE,
    aktif BOOLEAN DEFAULT TRUE
);
CREATE INDEX idx_bolumler_aktif ON bolumler(aktif) WHERE aktif = TRUE;
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role role_enum NOT NULL,
    bolum_id INT REFERENCES bolumler(bolum_id) ON DELETE SET NULL,
    ad_soyad VARCHAR(150) NOT NULL,
    aktif BOOLEAN DEFAULT TRUE,
    son_giris TIMESTAMP,
    CONSTRAINT chk_admin_bolum CHECK (
        (role = 'Admin' AND bolum_id IS NULL) OR
        (role = 'Bölüm Koordinatörü' AND bolum_id IS NOT NULL)
    )
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_aktif_role ON users(aktif, role) WHERE aktif = TRUE;
CREATE TABLE derslikler (
    derslik_id SERIAL PRIMARY KEY,
    bolum_id INT NOT NULL REFERENCES bolumler(bolum_id) ON DELETE CASCADE,
    derslik_kodu VARCHAR(20) NOT NULL,
    derslik_adi VARCHAR(100) NOT NULL,
    kapasite INT NOT NULL CHECK (kapasite > 0),
    satir_sayisi INT NOT NULL CHECK (satir_sayisi > 0),
    sutun_sayisi INT NOT NULL CHECK (sutun_sayisi > 0),
    sira_yapisi INT NOT NULL CHECK (sira_yapisi > 0),
    aktif BOOLEAN DEFAULT TRUE,
    UNIQUE(bolum_id, derslik_kodu)
);
CREATE INDEX idx_derslikler_bolum_aktif ON derslikler(bolum_id, aktif) WHERE aktif = TRUE;
CREATE TABLE dersler (
    ders_id SERIAL PRIMARY KEY,
    bolum_id INT NOT NULL REFERENCES bolumler(bolum_id) ON DELETE CASCADE,
    ders_kodu VARCHAR(20) NOT NULL UNIQUE,
    ders_adi VARCHAR(100) NOT NULL,
    ogretim_elemani VARCHAR(150) NOT NULL,
    sinif INT NOT NULL CHECK (sinif BETWEEN 1 AND 5),
    ders_yapisi ders_yapisi_enum NOT NULL,
    aktif BOOLEAN DEFAULT TRUE
);
CREATE INDEX idx_dersler_bolum_aktif ON dersler(bolum_id, aktif) WHERE aktif = TRUE;
CREATE INDEX idx_dersler_kodu_trgm ON dersler USING GIN(ders_kodu gin_trgm_ops);
CREATE TABLE ogrenciler (
    ogrenci_no VARCHAR(20) PRIMARY KEY,
    bolum_id INT NOT NULL REFERENCES bolumler(bolum_id) ON DELETE CASCADE,
    ad_soyad VARCHAR(150) NOT NULL,
    sinif INT CHECK (sinif BETWEEN 1 AND 5),
    aktif BOOLEAN DEFAULT TRUE
);
CREATE INDEX idx_ogrenciler_bolum_aktif ON ogrenciler(bolum_id) WHERE aktif = TRUE;
CREATE INDEX idx_ogrenciler_ad_soyad_trgm ON ogrenciler USING GIN(ad_soyad gin_trgm_ops);
CREATE TABLE ders_kayitlari (
    kayit_id SERIAL PRIMARY KEY,
    ogrenci_no VARCHAR(20) NOT NULL REFERENCES ogrenciler(ogrenci_no) ON DELETE CASCADE,
    ders_id INT NOT NULL REFERENCES dersler(ders_id) ON DELETE CASCADE,
    UNIQUE(ogrenci_no, ders_id)
);
CREATE INDEX idx_kayit_ders ON ders_kayitlari(ders_id);
CREATE INDEX idx_kayit_ogrenci ON ders_kayitlari(ogrenci_no);
CREATE TABLE sinav_programi (
    program_id SERIAL PRIMARY KEY,
    bolum_id INT NOT NULL REFERENCES bolumler(bolum_id) ON DELETE CASCADE,
    program_adi VARCHAR(200) NOT NULL UNIQUE,
    sinav_tipi sinav_tipi_enum NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE NOT NULL,
    varsayilan_sinav_suresi INT DEFAULT 75 NOT NULL,
    bekleme_suresi INT DEFAULT 15 NOT NULL,
    CONSTRAINT chk_tarih_sirasi CHECK (bitis_tarihi >= baslangic_tarihi)
);
CREATE INDEX idx_program_bolum ON sinav_programi(bolum_id);
CREATE TABLE ders_sinav_sureleri (
    id SERIAL PRIMARY KEY,
    program_id INT NOT NULL REFERENCES sinav_programi(program_id) ON DELETE CASCADE,
    ders_id INT NOT NULL REFERENCES dersler(ders_id) ON DELETE CASCADE,
    sinav_suresi INT NOT NULL CHECK (sinav_suresi > 0),
    UNIQUE(program_id, ders_id)
);
CREATE TABLE sinavlar (
    sinav_id SERIAL PRIMARY KEY,
    program_id INT NOT NULL REFERENCES sinav_programi(program_id) ON DELETE CASCADE,
    ders_id INT NOT NULL REFERENCES dersler(ders_id) ON DELETE CASCADE,
    tarih DATE NOT NULL,
    baslangic_saati TIME NOT NULL,
    bitis_saati TIME NOT NULL,
    ogrenci_sayisi INT DEFAULT 0,
    UNIQUE(program_id, ders_id),
    CONSTRAINT chk_saat_sirasi CHECK (bitis_saati > baslangic_saati)
);
CREATE INDEX idx_sinav_program_tarih ON sinavlar(program_id, tarih, baslangic_saati);
CREATE TABLE sinav_derslikleri (
    id SERIAL PRIMARY KEY,
    sinav_id INT NOT NULL REFERENCES sinavlar(sinav_id) ON DELETE CASCADE,
    derslik_id INT NOT NULL REFERENCES derslikler(derslik_id) ON DELETE CASCADE,
    yerlesim_sayisi INT DEFAULT 0 NOT NULL CHECK (yerlesim_sayisi >= 0),
    UNIQUE(sinav_id, derslik_id)
);
CREATE INDEX idx_sinav_derslik_sinav ON sinav_derslikleri(sinav_id);
CREATE INDEX idx_sinav_derslik_derslik ON sinav_derslikleri(derslik_id);
CREATE INDEX idx_sinav_derslik_yerlesim ON sinav_derslikleri(sinav_id, derslik_id, yerlesim_sayisi);
CREATE TABLE oturma_planlari (
    oturma_id SERIAL PRIMARY KEY,
    sinav_id INT NOT NULL REFERENCES sinavlar(sinav_id) ON DELETE CASCADE,
    derslik_id INT NOT NULL REFERENCES derslikler(derslik_id) ON DELETE CASCADE,
    ogrenci_no VARCHAR(20) NOT NULL REFERENCES ogrenciler(ogrenci_no) ON DELETE CASCADE,
    satir_no INT NOT NULL CHECK (satir_no > 0),
    sutun_no INT NOT NULL CHECK (sutun_no > 0),
    UNIQUE(sinav_id, derslik_id, satir_no, sutun_no),
    UNIQUE(sinav_id, ogrenci_no)
);
CREATE INDEX idx_oturma_sinav_derslik ON oturma_planlari(sinav_id, derslik_id);
CREATE INDEX idx_oturma_ogrenci ON oturma_planlari(ogrenci_no);
CREATE TABLE import_logs (
    log_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    dosya_adi VARCHAR(255) NOT NULL,
    dosya_tipi import_tipi_enum NOT NULL,
    basarili_kayit INT DEFAULT 0,
    basarisiz_kayit INT DEFAULT 0,
    hata_detay TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_import_logs_user ON import_logs(user_id);
CREATE INDEX idx_import_logs_created ON import_logs(created_at DESC);
CREATE OR REPLACE FUNCTION trg_sinav_ogrenci_sayisi()
RETURNS TRIGGER AS $
BEGIN
    NEW.ogrenci_sayisi := (
        SELECT COUNT(*) FROM ders_kayitlari WHERE ders_id = NEW.ders_id
    );
    RETURN NEW;
END;
$ LANGUAGE plpgsql;
CREATE TRIGGER trg_set_ogrenci_sayisi
BEFORE INSERT OR UPDATE OF ders_id ON sinavlar
FOR EACH ROW EXECUTE FUNCTION trg_sinav_ogrenci_sayisi();
CREATE OR REPLACE FUNCTION trg_derslik_cakisma_kontrol()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM sinav_derslikleri sd
        INNER JOIN sinavlar s1 ON sd.sinav_id = s1.sinav_id
        INNER JOIN sinavlar s2 ON s2.sinav_id = NEW.sinav_id
        WHERE sd.derslik_id = NEW.derslik_id
          AND s1.tarih = s2.tarih
          AND s1.sinav_id != NEW.sinav_id
          AND (s1.baslangic_saati, s1.bitis_saati) OVERLAPS (s2.baslangic_saati, s2.bitis_saati)
    ) THEN
        RAISE EXCEPTION 'Derslik çakışması tespit edildi!';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_derslik_cakisma
BEFORE INSERT OR UPDATE ON sinav_derslikleri
FOR EACH ROW EXECUTE FUNCTION trg_derslik_cakisma_kontrol();
CREATE OR REPLACE FUNCTION trg_ogrenci_cakisma_kontrol()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM oturma_planlari op
        INNER JOIN sinavlar s1 ON op.sinav_id = s1.sinav_id
        INNER JOIN sinavlar s2 ON s2.sinav_id = NEW.sinav_id
        WHERE op.ogrenci_no = NEW.ogrenci_no
          AND s1.tarih = s2.tarih
          AND s1.sinav_id != NEW.sinav_id
          AND (s1.baslangic_saati, s1.bitis_saati) OVERLAPS (s2.baslangic_saati, s2.bitis_saati)
    ) THEN
        RAISE EXCEPTION 'Öğrenci % sınav çakışması!', NEW.ogrenci_no;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_ogrenci_cakisma
BEFORE INSERT ON oturma_planlari
FOR EACH ROW EXECUTE FUNCTION trg_ogrenci_cakisma_kontrol();
CREATE OR REPLACE FUNCTION trg_derslik_kapasite_kontrol()
RETURNS TRIGGER AS $$
DECLARE
    v_kapasite INT;
    v_yerlesim_sayisi INT;
BEGIN
    SELECT d.kapasite, COALESCE(sd.yerlesim_sayisi, 0)
    INTO v_kapasite, v_yerlesim_sayisi
    FROM derslikler d
    LEFT JOIN sinav_derslikleri sd ON sd.sinav_id = NEW.sinav_id AND sd.derslik_id = NEW.derslik_id
    WHERE d.derslik_id = NEW.derslik_id;
    IF v_yerlesim_sayisi >= v_kapasite THEN
        RAISE EXCEPTION 'Derslik kapasitesi dolu! (Kapasite: %, Mevcut: %)',
            v_kapasite, v_yerlesim_sayisi;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_kapasite_kontrol
BEFORE INSERT ON oturma_planlari
FOR EACH ROW EXECUTE FUNCTION trg_derslik_kapasite_kontrol();
CREATE OR REPLACE FUNCTION trg_update_yerlesim_sayaci()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE sinav_derslikleri
        SET yerlesim_sayisi = yerlesim_sayisi + 1
        WHERE sinav_id = NEW.sinav_id AND derslik_id = NEW.derslik_id;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE sinav_derslikleri
        SET yerlesim_sayisi = yerlesim_sayisi - 1
        WHERE sinav_id = OLD.sinav_id AND derslik_id = OLD.derslik_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_yerlesim_sayaci_guncelle
AFTER INSERT OR DELETE ON oturma_planlari
FOR EACH ROW EXECUTE FUNCTION trg_update_yerlesim_sayaci();
CREATE OR REPLACE FUNCTION set_current_user_id(p_user_id INT)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_user_id', p_user_id::TEXT, false);
END;
$$ LANGUAGE plpgsql;
ALTER TABLE derslikler ENABLE ROW LEVEL SECURITY;
ALTER TABLE dersler ENABLE ROW LEVEL SECURITY;
ALTER TABLE ogrenciler ENABLE ROW LEVEL SECURITY;
ALTER TABLE sinavlar ENABLE ROW LEVEL SECURITY;
ALTER TABLE sinav_programi ENABLE ROW LEVEL SECURITY;
ALTER TABLE oturma_planlari ENABLE ROW LEVEL SECURITY;
CREATE POLICY pol_derslikler_erisim ON derslikler FOR ALL USING (
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.user_id = COALESCE(current_setting('app.current_user_id', TRUE)::INT, 0)
        AND u.aktif = TRUE
        AND (u.role = 'Admin' OR u.bolum_id = derslikler.bolum_id)
    )
);
CREATE POLICY pol_dersler_erisim ON dersler FOR ALL USING (
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.user_id = COALESCE(current_setting('app.current_user_id', TRUE)::INT, 0)
        AND u.aktif = TRUE
        AND (u.role = 'Admin' OR u.bolum_id = dersler.bolum_id)
    )
);
CREATE POLICY pol_ogrenciler_erisim ON ogrenciler FOR ALL USING (
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.user_id = COALESCE(current_setting('app.current_user_id', TRUE)::INT, 0)
        AND u.aktif = TRUE
        AND (u.role = 'Admin' OR u.bolum_id = ogrenciler.bolum_id)
    )
);
CREATE POLICY pol_program_erisim ON sinav_programi FOR ALL USING (
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.user_id = COALESCE(current_setting('app.current_user_id', TRUE)::INT, 0)
        AND u.aktif = TRUE
        AND (u.role = 'Admin' OR u.bolum_id = sinav_programi.bolum_id)
    )
);
CREATE POLICY pol_sinavlar_erisim ON sinavlar FOR ALL USING (
    EXISTS (
        SELECT 1 FROM users u
        JOIN sinav_programi sp ON sp.program_id = sinavlar.program_id
        WHERE u.user_id = COALESCE(current_setting('app.current_user_id', TRUE)::INT, 0)
        AND u.aktif = TRUE
        AND (u.role = 'Admin' OR u.bolum_id = sp.bolum_id)
    )
);
CREATE POLICY pol_oturma_erisim ON oturma_planlari FOR ALL USING (
    EXISTS (
        SELECT 1 FROM users u
        JOIN sinavlar s ON s.sinav_id = oturma_planlari.sinav_id
        JOIN sinav_programi sp ON sp.program_id = s.program_id
        WHERE u.user_id = COALESCE(current_setting('app.current_user_id', TRUE)::INT, 0)
        AND u.aktif = TRUE
        AND (u.role = 'Admin' OR u.bolum_id = sp.bolum_id)
    )
);
CREATE MATERIALIZED VIEW mv_ders_detaylari AS
SELECT
    d.ders_id,
    d.ders_kodu,
    d.ders_adi,
    d.ogretim_elemani,
    d.sinif,
    d.ders_yapisi,
    b.bolum_adi,
    b.bolum_id,
    COUNT(DISTINCT dk.ogrenci_no) as ogrenci_sayisi
FROM dersler d
JOIN bolumler b ON d.bolum_id = b.bolum_id
LEFT JOIN ders_kayitlari dk ON d.ders_id = dk.ders_id
WHERE d.aktif = TRUE
GROUP BY d.ders_id, b.bolum_adi, b.bolum_id;
CREATE UNIQUE INDEX ON mv_ders_detaylari(ders_id);
CREATE INDEX ON mv_ders_detaylari(bolum_id);
CREATE VIEW v_ogrenci_dersleri AS
SELECT
    o.ogrenci_no,
    o.ad_soyad,
    o.sinif,
    b.bolum_adi,
    d.ders_kodu,
    d.ders_adi
FROM ogrenciler o
JOIN bolumler b ON o.bolum_id = b.bolum_id
JOIN ders_kayitlari dk ON o.ogrenci_no = dk.ogrenci_no
JOIN dersler d ON dk.ders_id = d.ders_id
WHERE o.aktif = TRUE AND d.aktif = TRUE;
CREATE VIEW v_sinav_programi_ozet AS
SELECT
    s.sinav_id,
    sp.program_adi,
    sp.sinav_tipi,
    d.ders_kodu,
    d.ders_adi,
    s.tarih,
    s.baslangic_saati,
    s.bitis_saati,
    s.ogrenci_sayisi,
    STRING_AGG(dr.derslik_adi, ', ' ORDER BY dr.derslik_adi) as derslikler
FROM sinavlar s
JOIN sinav_programi sp ON s.program_id = sp.program_id
JOIN dersler d ON s.ders_id = d.ders_id
LEFT JOIN sinav_derslikleri sd ON s.sinav_id = sd.sinav_id
LEFT JOIN derslikler dr ON sd.derslik_id = dr.derslik_id
GROUP BY s.sinav_id, sp.program_adi, sp.sinav_tipi, d.ders_kodu, d.ders_adi,
         s.tarih, s.baslangic_saati, s.bitis_saati, s.ogrenci_sayisi;
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_ders_detaylari;
END;
$$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION update_statistics()
RETURNS void AS $$
BEGIN
    ANALYZE dersler;
    ANALYZE ogrenciler;
    ANALYZE ders_kayitlari;
    ANALYZE sinavlar;
    ANALYZE oturma_planlari;
END;
$$ LANGUAGE plpgsql;
INSERT INTO bolumler (bolum_adi, bolum_kodu) VALUES
    ('Bilgisayar Mühendisliği', 'BMU'),
    ('Yazılım Mühendisliği', 'YMU'),
    ('Elektrik Mühendisliği', 'EMU'),
    ('Elektronik Mühendisliği', 'ELM'),
    ('İnşaat Mühendisliği', 'INS');
INSERT INTO users (email, password_hash, role, ad_soyad) VALUES
('admin@kocaeli.edu.tr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIYMXqnW5u',
 'Admin', 'Sistem Yöneticisi');
INSERT INTO users (email, password_hash, role, bolum_id, ad_soyad) VALUES
('koordinator.bmu@kocaeli.edu.tr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIYMXqnW5u',
 'Bölüm Koordinatörü', 1, 'Dr. BMU Koordinatör'),
('koordinator.ymu@kocaeli.edu.tr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIYMXqnW5u',
 'Bölüm Koordinatörü', 2, 'Dr. YMU Koordinatör');
INSERT INTO derslikler (bolum_id, derslik_kodu, derslik_adi, kapasite, satir_sayisi, sutun_sayisi, sira_yapisi) VALUES
(1, '3001', '301', 42, 7, 9, 3),
(1, '3002', 'Büyük Amfi', 48, 12, 8, 4),
(1, '3003', '303', 42, 8, 9, 3),
(1, '3004', 'EDA', 30, 10, 6, 2),
(1, '3005', '305', 42, 7, 9, 3);
REFRESH MATERIALIZED VIEW mv_ders_detaylari;
VACUUM ANALYZE;