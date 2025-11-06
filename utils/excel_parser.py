"""
Excel Parser Utilities - Improved Version
Parse Excel files for course and student data with flexible formatting
"""

import logging
import re
from pathlib import Path
from typing import List, Dict
import openpyxl
import pandas as pd

logger = logging.getLogger(__name__)


class ExcelParser:
    """Excel file parser for importing data"""

    @staticmethod
    def parse_ders_listesi(file_path: str) -> List[Dict]:
        """
        Parse course list from Excel file
        Supports multiple formats including section-based layout

        Args:
            file_path: Path to Excel file

        Returns:
            List of course dictionaries
        """
        try:
            # Read Excel file without assuming header row
            df = pd.read_excel(file_path, header=None, sheet_name=0)

            # Try to detect the format
            # Check if it has standard column headers in first few rows
            has_header = False
            header_row = 0

            for i in range(min(5, len(df))):
                row_text = ' '.join([str(x).lower() for x in df.iloc[i].values if pd.notna(x)])
                if 'ders kodu' in row_text or 'ders kod' in row_text:
                    has_header = True
                    header_row = i
                    break

            if has_header:
                return ExcelParser._parse_with_repeating_headers(file_path, header_row)
            else:
                # No header found - show helpful error
                first_rows = df.head(3).values.tolist()
                sample_text = "\n".join([" | ".join([str(x) for x in row if pd.notna(x)]) for row in first_rows])
                
                error_msg = (
                    "❌ Excel formatı tanınamadı!\n\n"
                    "Beklenen format:\n"
                    "  DERS KODU | DERSİN ADI | DERSİ VEREN ÖĞR. ELEMANI\n\n"
                    "Excel'in ilk satırında bu başlıklar olmalı.\n\n"
                    f"Dosyanızın ilk satırları:\n{sample_text}\n\n"
                    "Lütfen Excel'de 'DERS KODU', 'DERSİN ADI' ve 'DERSİ VEREN ÖĞR. ELEMANI' başlıklarını ekleyin."
                )
                raise ValueError(error_msg)

        except ValueError as ve:
            # Re-raise ValueError with our message
            raise ve
        except Exception as e:
            logger.error(f"Excel parse hatası: {e}", exc_info=True)
            raise ValueError(f"Excel dosyası okunamadı: {str(e)}")

    @staticmethod
    def _parse_with_repeating_headers(file_path: str, first_header_row: int) -> List[Dict]:
        """
        AKILLI DINAMIK PARSER - Kolon ve sınıf sırası değişebilir
        
        Format özellikleri:
          - Sınıf başlıkları: "1. Sınıf", "2. Sınıf", vb. (herhangi bir sırada olabilir)
          - Kolon başlıkları: DERS KODU | DERSİN ADI | DERSİ VEREN ÖĞR. ELEMANI (sıra değişebilir)
          - Alt başlıklar: SEÇMELİ DERS, SEÇMELİK DERS, vb.
        """
        df = pd.read_excel(file_path, header=None, sheet_name=0)

        dersler = []
        errors = []
        warnings = []
        current_sinif = None
        current_yapisi = 'Zorunlu'
        found_any_class = False
        
        # Column positions - will be detected dynamically for EACH header row
        col_map = {'ders_kodu': None, 'ders_adi': None, 'ogretim_elemani': None}
        
        # Statistics
        total_rows_checked = 0
        skipped_no_class = 0
        skipped_no_columns = 0
        skipped_empty = 0
        skipped_bad_code = 0

        for idx, row in df.iterrows():
            excel_row = idx + 1
            row_values = [str(x).strip() if pd.notna(x) else '' for x in row.values]
            row_text = ' '.join(row_values).lower()
            
            # Normalize for pattern matching
            row_text_norm = row_text.replace('ı', 'i').replace('ş', 's').replace('ğ', 'g')
            row_text_norm = row_text_norm.replace('ü', 'u').replace('ö', 'o').replace('ç', 'c')

            if not row_text.strip():
                continue

            # ═══════════════════════════════════════════════════════
            # 1. SINIF BAŞLIĞI KONTROLÜ (örn: "1. Sınıf", "4. Sınıf")
            # ═══════════════════════════════════════════════════════
            sinif_match = re.search(r'(\d+)\s*\.?\s*sinif', row_text_norm, re.IGNORECASE)
            has_secmeli = re.search(r'se[çc]mel[iİı]', row_text_norm, re.IGNORECASE)
            
            if sinif_match and not has_secmeli:
                current_sinif = int(sinif_match.group(1))
                current_yapisi = 'Zorunlu'
                found_any_class = True
                logger.info(f"📚 {current_sinif}. Sınıf (Satır {excel_row}) → Zorunlu dersler başladı")
                continue

            # ═══════════════════════════════════════════════════════
            # 2. SEÇMELİ BAŞLIK KONTROLÜ (SINIF BAŞLIĞI GİBİ)
            # ═══════════════════════════════════════════════════════
            # "SEÇMELİ DERS" veya "SEÇMELİK DERS" - sınıf başlığı gibi bir başlık satırı
            # Bu satırda "seçmeli" var AMA "ders kodu" gibi kolon başlıkları YOK
            if has_secmeli and current_sinif is not None:
                # Eğer "ders kodu" yoksa, bu bir başlık satırıdır (kolon başlığı değil)
                has_column_header = re.search(r'ders.*kod', row_text_norm, re.IGNORECASE)
                
                if not has_column_header:
                    # Bu bir seçmeli başlık satırı
                    old_yapisi = current_yapisi
                    current_yapisi = 'Seçmeli'
                    logger.info(f"📌 {current_sinif}. Sınıf → Seçmeli dersler başladı (Satır {excel_row})")
                    logger.info(f"   Önceki: {old_yapisi} → Yeni: {current_yapisi}")
                    logger.info(f"   Başlık içeriği: '{row_text[:60]}'")
                    continue
                else:
                    # "seçmeli" var AMA "ders kodu" da var - bu kolon başlığı olmalı
                    logger.debug(f"   Satır {excel_row}: 'seçmeli' var ama 'ders kodu' da var - kolon başlığı olarak işleniyor")

            # ═══════════════════════════════════════════════════════
            # 3. KOLON BAŞLIKLARI KONTROLÜ - ÇOK ESNEKİ DİNAMİK ALGILA
            # ═══════════════════════════════════════════════════════
            if re.search(r'ders.*kod', row_text_norm, re.IGNORECASE):
                # Bu bir kolon başlığı satırı - tüm kolonları tara
                new_col_map = {}
                
                logger.info(f"📋 Kolon başlık satırı bulundu (Satır {excel_row})")
                logger.info(f"   Mevcut mod: {current_sinif}. Sınıf - {current_yapisi}")
                
                for col_idx, val in enumerate(row_values):
                    if not val or val.strip() == '':
                        continue
                        
                    val_norm = val.lower()
                    val_norm = val_norm.replace('ı', 'i').replace('ş', 's').replace('ğ', 'g')
                    val_norm = val_norm.replace('ü', 'u').replace('ö', 'o').replace('ç', 'c')
                    
                    logger.debug(f"   Kolon {col_idx}: '{val}' → normalized: '{val_norm}'")
                    
                    # DERS KODU kolonu - çok esnek
                    if 'ders_kodu' not in new_col_map:
                        if re.search(r'ders.*kod', val_norm) or val_norm in ['kod', 'kodu', 'ders kod']:
                            new_col_map['ders_kodu'] = col_idx
                            logger.info(f"   ✓ Kolon {col_idx}: DERS KODU = '{val}'")
                            continue
                    
                    # DERSİN ADI kolonu - çok esnek
                    if 'ders_adi' not in new_col_map:
                        # "DERSİN ADI", "DERS ADI", "DERSIN ADI", "AD", "ADI", etc.
                        if re.search(r'(dersin|ders).*ad', val_norm) or val_norm in ['ad', 'adi', 'isim']:
                            new_col_map['ders_adi'] = col_idx
                            logger.info(f"   ✓ Kolon {col_idx}: DERSİN ADI = '{val}'")
                            continue
                    
                    # DERSİ VEREN / ÖĞRETİM ELEMANI kolonu - en esnek
                    if 'ogretim_elemani' not in new_col_map:
                        if re.search(r'(veren|elem|ogretim|hoca|ogr)', val_norm):
                            new_col_map['ogretim_elemani'] = col_idx
                            logger.info(f"   ✓ Kolon {col_idx}: ÖĞRETİM ELEMANI = '{val}'")
                            continue
                
                # Validate all columns found
                missing = []
                if 'ders_kodu' not in new_col_map:
                    missing.append("DERS KODU")
                if 'ders_adi' not in new_col_map:
                    missing.append("DERSİN ADI")
                if 'ogretim_elemani' not in new_col_map:
                    missing.append("DERSİ VEREN ÖĞR. ELEMANI")
                
                if missing:
                    found_cols = []
                    for i, val in enumerate(row_values):
                        if val and val.strip():
                            found_cols.append(f"Kolon {i}: '{val}'")
                    
                    error_msg = (
                        f"❌ Satır {excel_row}: Kolon başlıkları tam algılanamadı!\n\n"
                        f"Eksik kolonlar: {', '.join(missing)}\n\n"
                        f"Excel'deki kolonlar:\n" + "\n".join([f"  • {c}" for c in found_cols]) + "\n\n"
                        f"KABUL EDİLEN İSİMLER:\n"
                        f"  • Ders Kodu: 'DERS KODU', 'DERS KOD', 'KOD'\n"
                        f"  • Ders Adı: 'DERSİN ADI', 'DERS ADI', 'ADI'\n"
                        f"  • Öğretim Elemanı: 'DERSİ VEREN ÖĞR. ELEMANI', içinde 'VEREN', 'ELEM', 'HOCA' geçen"
                    )
                    errors.append(error_msg)
                    logger.error(error_msg)
                    # Don't raise, collect error and continue
                else:
                    col_map = new_col_map
                    logger.info(f"✅ Kolonlar eşleşti: Kod={col_map['ders_kodu']}, Ad={col_map['ders_adi']}, Eleman={col_map['ogretim_elemani']}")
                
                continue

            # ═══════════════════════════════════════════════════════
            # 4. DERS SATIRI PARSE ET
            # ═══════════════════════════════════════════════════════
            
            # Count total rows that reach this point
            total_rows_checked += 1
            
            # Prerequisites check
            if current_sinif is None:
                skipped_no_class += 1
                continue
            
            # Check if columns are mapped (use 'is not None' because column 0 is falsy!)
            if not all(v is not None for v in col_map.values()):
                skipped_no_columns += 1
                continue
            
            # Extract values using dynamic column positions
            try:
                ders_kodu = row_values[col_map['ders_kodu']] if col_map['ders_kodu'] < len(row_values) else ''
                ders_adi = row_values[col_map['ders_adi']] if col_map['ders_adi'] < len(row_values) else ''
                ogretim_elemani = row_values[col_map['ogretim_elemani']] if col_map['ogretim_elemani'] < len(row_values) else ''
            except (KeyError, IndexError) as e:
                logger.warning(f"⚠️ Satır {excel_row}: Kolon okuma hatası: {e}")
                continue

            # Clean values (remove extra spaces, nan, etc.)
            ders_kodu = str(ders_kodu).strip() if ders_kodu and ders_kodu != 'nan' else ''
            ders_adi = str(ders_adi).strip() if ders_adi and ders_adi != 'nan' else ''
            ogretim_elemani = str(ogretim_elemani).strip() if ogretim_elemani and ogretim_elemani != 'nan' else ''

            # Skip completely empty rows
            if not ders_kodu and not ders_adi and not ogretim_elemani:
                skipped_empty += 1
                continue

            # ÖNEMLİ: Ders kodu kontrolünden ÖNCE seçmeli başlık kontrolü!
            # Eğer ders_kodu "SEÇMELİ" veya "SEÇMELİK" veya "SEÇİMLİK" içeriyorsa, bu başlık olabilir
            
            # Aggressive normalization for Turkish characters
            ders_kodu_norm = ders_kodu.upper()  # First uppercase
            ders_kodu_norm = ders_kodu_norm.replace('İ', 'I').replace('Ş', 'S').replace('Ğ', 'G')
            ders_kodu_norm = ders_kodu_norm.replace('Ü', 'U').replace('Ö', 'O').replace('Ç', 'C')
            ders_kodu_norm = ders_kodu_norm.lower()  # Then lowercase
            ders_kodu_norm = ders_kodu_norm.replace('ı', 'i')  # ı → i
            
            if ders_kodu_norm.startswith('sec') and ('mel' in ders_kodu_norm or 'lik' in ders_kodu_norm):
                # İlk sütunda "seçmeli" var - bu bir başlık!
                old_yapisi = current_yapisi
                current_yapisi = 'Seçmeli'
                logger.info(f"📌 {current_sinif}. Sınıf → Seçmeli dersler başladı (Satır {excel_row})")
                logger.info(f"   Önceki: {old_yapisi} → Yeni: {current_yapisi}")
                logger.info(f"   İlk sütun: '{ders_kodu}' → normalized: '{ders_kodu_norm}'")
                skipped_bad_code += 1
                continue

            # Skip if not a course code
            if not re.match(r'^[A-Z]{3}\d{3}', ders_kodu.upper()):
                skipped_bad_code += 1
                if ders_kodu:  # Only log if there's something in the cell
                    logger.info(f"⏭️ Satır {excel_row}: '{ders_kodu}' ders kodu formatında değil, atlandı")
                continue

            # ═══════════════════════════════════════════════════════
            # 5. VALIDATION
            # ═══════════════════════════════════════════════════════
            row_errors = []
            
            if not ders_kodu:
                row_errors.append("Ders kodu eksik")
            elif not re.match(r'^[A-Z]{3}\d{3}$', ders_kodu.upper()):
                row_errors.append(f"Geçersiz format: '{ders_kodu}'")
            
            if not ders_adi or ders_adi.strip() == '' or ders_adi == 'nan':
                row_errors.append("Ders adı eksik")
            
            if not ogretim_elemani or ogretim_elemani.strip() == '' or ogretim_elemani == 'nan':
                row_errors.append("Öğretim elemanı eksik")
            
            if row_errors:
                error_detail = f"Satır {excel_row} ({ders_kodu}): {', '.join(row_errors)}"
                errors.append(error_detail)
                logger.warning(f"⚠️ {error_detail}")
                continue

            # ═══════════════════════════════════════════════════════
            # 6. BAŞARILI - DERS EKLE
            # ═══════════════════════════════════════════════════════
            ders = {
                'ders_kodu': ders_kodu.upper(),
                'ders_adi': ders_adi.strip(),
                'ogretim_elemani': ogretim_elemani.strip(),
                'sinif': current_sinif,
                'ders_yapisi': current_yapisi
            }
            dersler.append(ders)
            logger.info(f"✅ {ders_kodu.upper()} → {current_sinif}. Sınıf, {current_yapisi}")

        # ═══════════════════════════════════════════════════════
        # 7. VALIDATION & SUMMARY REPORT
        # ═══════════════════════════════════════════════════════
        
        # Log parsing statistics
        logger.info("═══════════════════════════════════════════════")
        logger.info("📊 PARSING İSTATİSTİKLERİ:")
        logger.info(f"  Toplam kontrol edilen satır: {total_rows_checked}")
        logger.info(f"  ✅ Başarıyla eklenen: {len(dersler)}")
        logger.info(f"  ❌ Hatalı satır: {len(errors)}")
        logger.info(f"  ⏭️ Atlanan (sınıf yok): {skipped_no_class}")
        logger.info(f"  ⏭️ Atlanan (kolon yok): {skipped_no_columns}")
        logger.info(f"  ⏭️ Atlanan (boş): {skipped_empty}")
        logger.info(f"  ⏭️ Atlanan (kod formatı): {skipped_bad_code}")
        logger.info("═══════════════════════════════════════════════")
        
        if not found_any_class:
            raise ValueError(
                "❌ Excel'de sınıf başlığı bulunamadı!\n\n"
                "Aranılan format: '1. Sınıf', '2. Sınıf', '3. Sınıf', '4. Sınıf'\n\n"
                "Excel'inizde bu tür başlıklar olduğundan emin olun."
            )
        
        if not all(col_map.values()) and not dersler and not errors:
            raise ValueError(
                "❌ Excel'de kolon başlıkları bulunamadı!\n\n"
                "Her sınıf başlığından sonra şu satır olmalı:\n"
                "  DERS KODU | DERSİN ADI | DERSİ VEREN ÖĞR. ELEMANI\n\n"
                "Kolonların sırası değişebilir ama isimleri doğru olmalı."
            )
        
        if not dersler and not errors:
            raise ValueError(
                "❌ Excel'den hiç ders okunamadı!\n\n"
                "Kontrol edin:\n"
                "  • Ders kodları ABC123 formatında mı? (3 harf + 3 rakam)\n"
                "  • Satırlar dolu mu?\n"
                "  • Sınıf başlıkları var mı?"
            )
        
        # Create detailed summary
        summary = {}
        for ders in dersler:
            sinif = ders['sinif']
            yapisi = ders['ders_yapisi']
            key = (sinif, yapisi)
            summary[key] = summary.get(key, 0) + 1
        
        logger.info("╔═══════════════════════════════════════════════╗")
        logger.info("║           📊 YÜKLEME SONUCU ÖZET             ║")
        logger.info("╠═══════════════════════════════════════════════╣")
        
        for (sinif, yapisi), count in sorted(summary.items()):
            icon = "📗" if yapisi == "Zorunlu" else "📘"
            logger.info(f"║  {icon} {sinif}. Sınıf - {yapisi:8s} : {count:3d} ders    ║")
        
        logger.info("╠═══════════════════════════════════════════════╣")
        logger.info(f"║  ✅ Başarılı: {len(dersler):3d} ders                      ║")
        logger.info(f"║  ❌ Hatalı  : {len(errors):3d} satır                     ║")
        logger.info("╚═══════════════════════════════════════════════╝")
        
        # Handle errors
        if errors:
            error_summary = "\n\n❌ HATALI SATIRLAR:\n" + "\n".join([f"  • {e}" for e in errors[:20]])
            if len(errors) > 20:
                error_summary += f"\n  ... ve {len(errors) - 20} hata daha"
            
            logger.warning(error_summary)
            
            # If we have some successful courses, continue but warn
            if dersler:
                logger.warning(f"⚠️ {len(errors)} satır atlandı, {len(dersler)} ders yüklendi")
            else:
                # No successful courses at all
                raise ValueError(f"Tüm satırlar hatalı!{error_summary}")
        
        return dersler

    @staticmethod
    def _parse_text_based_ders_listesi(df: pd.DataFrame) -> List[Dict]:
        """Parse text-based format where courses are listed in rows"""
        dersler = []
        current_sinif = 1
        current_yapisi = 'Zorunlu'

        for idx, row in df.iterrows():
            # Convert row to string for pattern matching
            row_text = ' '.join([str(x) for x in row.values if pd.notna(x)]).strip()

            if not row_text or row_text == 'nan':
                continue

            # Check for class header (e.g., "1. Sınıf", "2. Sınıf")
            sinif_match = re.search(r'(\d+)\s*\.?\s*s[ıi]n[ıi]f', row_text, re.IGNORECASE)
            if sinif_match:
                current_sinif = int(sinif_match.group(1))
                current_yapisi = 'Zorunlu'
                continue

            # Check for elective course section
            if re.search(r'se[çc]meli|se[çc]imlik', row_text, re.IGNORECASE):
                current_yapisi = 'Seçmeli'
                continue

            # Skip header rows
            if re.search(r'ders\s+kodu|dersin\s+ad[ıi]', row_text, re.IGNORECASE):
                continue

            # Try to extract course information
            # Pattern: DERS_KODU Ders Adı Öğretim Elemanı
            kod_match = re.match(r'^([A-Z]{3}\d{3})', row_text)

            if kod_match:
                ders_kodu = kod_match.group(1)
                remaining = row_text[len(ders_kodu):].strip()

                # Split remaining text to get name and instructor
                instructor_pattern = r'((?:Prof\.|Doç\.|Dr\.|Öğr\.|Arş\.).*?)$'
                instructor_match = re.search(instructor_pattern, remaining)

                if instructor_match:
                    ogretim_elemani = instructor_match.group(1).strip()
                    ders_adi = remaining[:instructor_match.start()].strip()
                else:
                    ders_adi = remaining
                    ogretim_elemani = 'Belirtilmemiş'

                ders = {
                    'ders_kodu': ders_kodu,
                    'ders_adi': ders_adi if ders_adi else 'İsimsiz Ders',
                    'ogretim_elemani': ogretim_elemani,
                    'sinif': current_sinif,
                    'ders_yapisi': current_yapisi
                }
                dersler.append(ders)

        logger.info(f"✅ {len(dersler)} ders Excel'den yüklendi (metin formatı)")
        return dersler

    @staticmethod
    def parse_ogrenci_listesi(file_path: str) -> List[Dict]:
        """
        Parse student list from Excel file
        Supports standard tabular format: Öğrenci No | Ad Soyad | Sınıf | Ders

        Args:
            file_path: Path to Excel file

        Returns:
            List of student dictionaries with enrolled courses
        """
        try:
            # Try reading with first row as header
            df = pd.read_excel(file_path)

            # Normalize column names
            df.columns = df.columns.str.strip().str.lower()

            # Remove Turkish characters for matching
            df.columns = df.columns.str.replace('ı', 'i').str.replace('ş', 's').str.replace('ğ', 'g')
            df.columns = df.columns.str.replace('ü', 'u').str.replace('ö', 'o').str.replace('ç', 'c')

            # Check for common mistakes BEFORE mapping
            detected_issues = []
            for col in df.columns:
                if 'ders adi' in col or 'dersadi' in col or 'dersin adi' in col:
                    detected_issues.append(
                        f"❌ Yanlış kolon ismi: '{col}'\n"
                        f"   'Ders Adı' yerine 'Ders' veya 'Ders Kodu' kullanın!\n"
                        f"   Bu kolonda ders KODU olmalı (örn: MAT101, BLM205)"
                    )
            
            if detected_issues:
                raise ValueError("\n\n".join(detected_issues))
            
            # Column mapping - STRICT for course column
            column_mapping = {
                'ogrenci no': 'ogrenci_no',
                'ogrencino': 'ogrenci_no',
                'no': 'ogrenci_no',
                'numara': 'ogrenci_no',
                'ad soyad': 'ad_soyad',
                'adsoyad': 'ad_soyad',
                'ad': 'ad_soyad',
                'isim': 'ad_soyad',
                'sinif': 'sinif',
                'sinifi': 'sinif',
                'ders': 'ders',
                'ders kodu': 'ders',
                'derskodu': 'ders'
            }

            # Rename columns
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df.rename(columns={old_name: new_name}, inplace=True)

            # Validate required columns
            required = ['ogrenci_no', 'ad_soyad']
            missing = [col for col in required if col not in df.columns]

            if missing:
                # Provide helpful error message
                original_columns = list(df.columns)
                error_msg = f"❌ Eksik sütunlar: {', '.join(missing)}\n\n"
                error_msg += "Excel'deki mevcut sütunlar:\n"
                error_msg += "\n".join([f"  • {col}" for col in original_columns[:10]])
                if len(original_columns) > 10:
                    error_msg += f"\n  ... ve {len(original_columns) - 10} sütun daha"
                error_msg += "\n\nGerekli sütunlar:\n"
                error_msg += "  • Öğrenci No (veya No, Numara)\n"
                error_msg += "  • Ad Soyad (veya Ad, İsim)\n"
                error_msg += "  • Ders (veya Ders Kodu) - İSTEĞE BAĞLI\n"
                error_msg += "  • Sınıf - İSTEĞE BAĞLI"
                raise ValueError(error_msg)

            # Group by student to collect their courses
            ogrenciler_dict = {}
            errors = []
            warnings = []
            has_ders_column = 'ders' in df.columns

            for idx, row in df.iterrows():
                excel_row = idx + 2  # +2 because Excel starts from 1 and we have header
                
                row_errors = []
                row_warnings = []
                
                # Get values
                ogrenci_no = str(row['ogrenci_no']).strip() if pd.notna(row.get('ogrenci_no')) else ''
                ad_soyad = str(row['ad_soyad']).strip() if pd.notna(row.get('ad_soyad')) else ''

                # Validation
                if not ogrenci_no or ogrenci_no == 'nan':
                    row_errors.append("Öğrenci numarası eksik")
                elif not re.match(r'^\d+$', ogrenci_no):
                    row_errors.append(f"Geçersiz öğrenci no: '{ogrenci_no}' (Sadece rakam olmalı)")
                
                if not ad_soyad or ad_soyad == 'nan':
                    row_errors.append("Ad soyad eksik")
                elif len(ad_soyad.split()) < 2:
                    row_errors.append(f"Ad soyad eksik: '{ad_soyad}' (En az ad ve soyad olmalı)")
                
                # If there are errors, log and skip
                if row_errors:
                    error_msg = f"Satır {excel_row}: {', '.join(row_errors)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    continue

                # Extract class number
                sinif_val = str(row.get('sinif', '1')).strip()
                sinif_match = re.search(r'(\d+)', sinif_val)
                sinif = int(sinif_match.group(1)) if sinif_match else 1

                # Get course if exists - WITH VALIDATION
                ders = None
                if has_ders_column:
                    ders_val = str(row.get('ders', '')).strip() if pd.notna(row.get('ders')) else ''
                    if ders_val and ders_val != 'nan' and ders_val != '':
                        # Validate course code format (ABC123)
                        if re.match(r'^[A-Z]{3}\d{3}$', ders_val.upper()):
                            ders = ders_val.upper()
                        else:
                            row_warnings.append(f"Geçersiz ders kodu: '{ders_val}' (Beklenen format: ABC123)")
                
                # Log warnings
                if row_warnings:
                    warning_msg = f"Satır {excel_row} ({ogrenci_no}): {', '.join(row_warnings)}"
                    warnings.append(warning_msg)
                    logger.warning(warning_msg)

                # Add or update student
                if ogrenci_no not in ogrenciler_dict:
                    ogrenciler_dict[ogrenci_no] = {
                        'ogrenci_no': ogrenci_no,
                        'ad_soyad': ad_soyad,
                        'sinif': sinif,
                        'dersler': []
                    }

                # Add course if valid
                if ders:
                    ogrenciler_dict[ogrenci_no]['dersler'].append(ders)

            # Convert to list
            ogrenciler = list(ogrenciler_dict.values())

            # Check if ders column was expected but not found - MAKE IT AN ERROR
            if not has_ders_column:
                error_msg = (
                    "❌ 'Ders' kolonu bulunamadı!\n\n"
                    "Öğrenci-ders eşleştirmesi için 'Ders' veya 'Ders Kodu' kolonu gereklidir.\n\n"
                    "Excel'de şu kolon isimlerinden birini kullanın:\n"
                    "  • Ders\n"
                    "  • Ders Kodu\n"
                    "  • DersKodu\n\n"
                    "Bu kolonda ders KODLARI olmalı (örn: MAT101, BLM205, FIZ203)\n\n"
                    "NOT: 'Ders Adı' yerine 'Ders Kodu' kullanmalısınız!"
                )
                raise ValueError(error_msg)

            # Report results
            error_and_warning_summary = ""
            
            if errors:
                error_summary = f"\n\n❌ {len(errors)} satırda hata bulundu:\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    error_summary += f"\n... ve {len(errors) - 10} hata daha"
                error_and_warning_summary += error_summary
                logger.warning(error_summary)
            
            if warnings:
                warning_summary = f"\n\n⚠️ {len(warnings)} uyarı:\n" + "\n".join(warnings[:10])
                if len(warnings) > 10:
                    warning_summary += f"\n... ve {len(warnings) - 10} uyarı daha"
                error_and_warning_summary += warning_summary
                logger.warning(warning_summary)
            
            if errors and not ogrenciler:
                raise ValueError(f"Excel dosyasından öğrenci okunamadı!{error_and_warning_summary}")
            elif errors or warnings:
                # Both errors and/or warnings - create detailed message
                summary = f"✅ {len(ogrenciler)} öğrenci yüklendi"
                if errors:
                    summary += f", {len(errors)} satır atlandı"
                if warnings:
                    summary += f", {len(warnings)} uyarı var"
                logger.info(summary + error_and_warning_summary)
            else:
                logger.info(f"✅ {len(ogrenciler)} öğrenci Excel'den yüklendi")
            
            return ogrenciler

        except ValueError as ve:
            # Re-raise ValueError with our custom message
            raise ve
        except Exception as e:
            logger.error(f"Excel parse hatası: {e}")
            raise ValueError(f"Excel dosyası okunamadı: {str(e)}")

    @staticmethod
    def parse_derslik_listesi(file_path: str) -> List[Dict]:
        """
        Parse classroom list from Excel file

        Expected columns:
        - Derslik Kodu
        - Derslik Adı
        - Kapasite
        - Satır Sayısı
        - Sütun Sayısı
        - Sıra Yapısı

        Args:
            file_path: Path to Excel file

        Returns:
            List of classroom dictionaries
        """
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip().str.lower()

            # Remove Turkish characters
            df.columns = df.columns.str.replace('ı', 'i').str.replace('ş', 's').str.replace('ğ', 'g')
            df.columns = df.columns.str.replace('ü', 'u').str.replace('ö', 'o').str.replace('ç', 'c')

            column_mapping = {
                'derslik kodu': 'derslik_kodu',
                'derslik kod': 'derslik_kodu',
                'kod': 'derslik_kodu',
                'derslik adi': 'derslik_adi',
                'derslik ad': 'derslik_adi',
                'ad': 'derslik_adi',
                'adi': 'derslik_adi',
                'kapasite': 'kapasite',
                'satir sayisi': 'satir_sayisi',
                'satir': 'satir_sayisi',
                'sutun sayisi': 'sutun_sayisi',
                'sutun': 'sutun_sayisi',
                'sira yapisi': 'sira_yapisi',
                'sira': 'sira_yapisi'
            }

            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df.rename(columns={old_name: new_name}, inplace=True)

            required = ['derslik_kodu', 'derslik_adi', 'kapasite']
            missing = [col for col in required if col not in df.columns]

            if missing:
                raise ValueError(f"Eksik sütunlar: {', '.join(missing)}")

            derslikler = []
            for _, row in df.iterrows():
                kapasite = int(row['kapasite'])
                derslik = {
                    'derslik_kodu': str(row['derslik_kodu']).strip().upper(),
                    'derslik_adi': str(row['derslik_adi']).strip(),
                    'kapasite': kapasite,
                    'satir_sayisi': int(row.get('satir_sayisi', 10)),
                    'sutun_sayisi': int(row.get('sutun_sayisi', 6)),
                    'sira_yapisi': int(row.get('sira_yapisi', 3))
                }
                derslikler.append(derslik)

            logger.info(f"✅ {len(derslikler)} derslik Excel'den yüklendi")
            return derslikler

        except Exception as e:
            logger.error(f"Excel parse hatası: {e}")
            raise ValueError(f"Excel dosyası okunamadı: {str(e)}")

    @staticmethod
    def validate_excel_file(file_path: str) -> bool:
        """
        Validate Excel file

        Args:
            file_path: Path to Excel file

        Returns:
            True if valid, False otherwise
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return False

            if path.suffix.lower() not in ['.xlsx', '.xls']:
                return False

            pd.read_excel(file_path, nrows=1)

            return True

        except Exception as e:
            logger.error(f"Excel validation error: {e}")
            return False