"""
Sınav (Exam) Controller - REFACTORED
Business logic for exam schedule management
Separated concerns: validation, orchestration, data transformation
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SinavController:
    """Exam schedule business logic controller"""

    def __init__(self, sinav_model, ders_model, derslik_model):
        self.sinav_model = sinav_model
        self.ders_model = ders_model
        self.derslik_model = derslik_model

    # ==================== PROGRAM MANAGEMENT ====================

    def create_exam_program(self, program_data: Dict) -> Dict:
        """
        Create exam program

        Args:
            program_data: Program bilgileri
                - program_adi (required)
                - bolum_id
                - sinav_tipi
                - baslangic_tarihi
                - bitis_tarihi

        Returns:
            {'success': bool, 'message': str, 'program_id': int}
        """
        try:
            # Validate
            validation = self._validate_program_data(program_data)
            if not validation['valid']:
                return {
                    'success': False,
                    'message': validation['message']
                }

            # Create program
            program_id = self.sinav_model.create_program(program_data)

            logger.info(f"✅ Exam program created: ID={program_id}")

            return {
                'success': True,
                'message': f"Sınav programı başarıyla oluşturuldu!",
                'program_id': program_id
            }

        except Exception as e:
            logger.error(f"Error creating exam program: {e}", exc_info=True)
            return {
                'success': False,
                'message': f"Program oluşturma hatası: {str(e)}"
            }

    def get_program_by_id(self, program_id: int) -> Optional[Dict]:
        """Get program details"""
        try:
            return self.sinav_model.get_program_by_id(program_id)
        except Exception as e:
            logger.error(f"Error getting program: {e}")
            return None

    def get_programs_by_bolum(self, bolum_id: int) -> List[Dict]:
        """Get all programs for department"""
        try:
            return self.sinav_model.get_programs_by_bolum(bolum_id)
        except Exception as e:
            logger.error(f"Error getting programs: {e}")
            return []

    def delete_program(self, program_id: int) -> Dict:
        """Delete exam program"""
        try:
            result = self.sinav_model.delete_program(program_id)

            if result:
                return {
                    'success': True,
                    'message': "Program başarıyla silindi!"
                }
            else:
                return {
                    'success': False,
                    'message': "Program silinemedi!"
                }

        except Exception as e:
            logger.error(f"Error deleting program: {e}", exc_info=True)
            return {
                'success': False,
                'message': f"Silme hatası: {str(e)}"
            }

    # ==================== SCHEDULE MANAGEMENT ====================

    def save_exam_schedule(self, schedule: List[Dict], program_name: Optional[str] = None) -> Dict:
        """
        Save exam schedule to database

        Args:
            schedule: List of exam entries
            program_name: Optional custom program name

        Returns:
            {'success': bool, 'message': str, 'program_id': int}
        """
        try:
            if not schedule:
                return {
                    'success': False,
                    'message': "Boş program kaydedilemez!"
                }

            # Validate schedule
            validation = self._validate_schedule_data(schedule)
            if not validation['valid']:
                return {
                    'success': False,
                    'message': validation['message'],
                    'details': validation.get('details', '')
                }

            # Create program first
            program_data = self._prepare_program_data(schedule, program_name)
            program_result = self.create_exam_program(program_data)

            if not program_result['success']:
                return program_result

            program_id = program_result['program_id']

            # Group exams by (ders_id, tarih_saat)
            grouped_exams = self._group_exams_by_course_time(schedule)

            logger.info(
                f"📊 Saving schedule: {len(schedule)} entries → "
                f"{len(grouped_exams)} unique exams"
            )

            # Insert exams
            success_count = 0
            error_count = 0

            for (ders_id, tarih_saat), exam_group in grouped_exams.items():
                try:
                    # Prepare exam data
                    exam_data = self._prepare_exam_data(
                        exam_group[0],
                        program_id
                    )

                    # Collect classrooms
                    derslik_ids = self._collect_classroom_ids(exam_group)

                    # Insert exam with classrooms atomically
                    sinav_id = self.sinav_model.insert_exam_with_classrooms(
                        exam_data,
                        derslik_ids
                    )

                    success_count += 1

                except Exception as e:
                    logger.error(
                        f"Error saving exam for ders_id {ders_id}: {e}",
                        exc_info=True
                    )
                    error_count += 1

            # Result
            success = error_count == 0 and success_count > 0

            if success:
                message = f"✅ {success_count} sınav başarıyla kaydedildi!"
            else:
                message = (
                    f"⚠️ Kısmen kaydedildi: "
                    f"{success_count} başarılı, {error_count} hatalı"
                )

            return {
                'success': success,
                'message': message,
                'program_id': program_id,
                'success_count': success_count,
                'error_count': error_count,
            }

        except Exception as e:
            logger.error(f"Error saving exam schedule: {e}", exc_info=True)
            return {
                'success': False,
                'message': f"Kaydetme hatası: {str(e)}"
            }

    def get_schedule_by_program(self, program_id: int) -> List[Dict]:
        """Get full schedule for a program"""
        try:
            return self.sinav_model.get_sinavlar_by_program(program_id)
        except Exception as e:
            logger.error(f"Error getting schedule: {e}")
            return []

    # ==================== VALIDATION ====================

    def _validate_program_data(self, program_data: Dict) -> Dict:
        """Validate program creation data"""
        if not program_data.get('program_adi'):
            return {
                'valid': False,
                'message': "Program adı gereklidir!"
            }

        if not program_data.get('bolum_id'):
            return {
                'valid': False,
                'message': "Bölüm ID gereklidir!"
            }

        # Date validation
        if program_data.get('baslangic_tarihi') and program_data.get('bitis_tarihi'):
            if program_data['baslangic_tarihi'] >= program_data['bitis_tarihi']:
                return {
                    'valid': False,
                    'message': "Bitiş tarihi başlangıçtan sonra olmalıdır!"
                }

        return {'valid': True}

    def _validate_schedule_data(self, schedule: List[Dict]) -> Dict:
        """Validate schedule data before saving"""
        # Check for required fields
        required_fields = ['ders_id', 'tarih_saat', 'sure', 'bolum_id']

        for idx, exam in enumerate(schedule):
            for field in required_fields:
                if field not in exam:
                    return {
                        'valid': False,
                        'message': f"Sınav {idx + 1}: '{field}' alanı eksik!",
                        'details': f"Gerekli alanlar: {', '.join(required_fields)}"
                    }

        # Check for duplicates
        duplicate_check = self._check_duplicate_exams(schedule)
        if not duplicate_check['valid']:
            return duplicate_check

        return {'valid': True}

    def _check_duplicate_exams(self, schedule: List[Dict]) -> Dict:
        """Check for problematic duplicates"""
        from collections import Counter

        ders_ids = [exam.get('ders_id') for exam in schedule]
        ders_counts = Counter(ders_ids)
        duplicates = {ders_id: count for ders_id, count in ders_counts.items() if count > 1}

        if not duplicates:
            return {'valid': True}

        # Group by time to check if duplicates are at different times
        for ders_id, count in duplicates.items():
            times = [
                str(exam.get('tarih_saat'))
                for exam in schedule
                if exam.get('ders_id') == ders_id
            ]
            unique_times = set(times)

            if len(unique_times) > 1:
                # Critical error: same course at different times
                logger.error(
                    f"❌ CRITICAL: ders_id {ders_id} scheduled at "
                    f"{len(unique_times)} different times"
                )

                return {
                    'valid': False,
                    'message': f"Ders {ders_id} farklı zamanlarda planlanmış!",
                    'details': f"Zaman sayısı: {len(unique_times)}"
                }
            else:
                # OK: same course at same time (multi-classroom)
                logger.info(
                    f"✅ OK: ders_id {ders_id} appears {count} times "
                    f"at same time (multi-classroom)"
                )

        return {'valid': True}

    # ==================== DATA PREPARATION ====================

    def _prepare_program_data(self, schedule: List[Dict], program_name: Optional[str]) -> Dict:
        """Prepare program data from schedule"""
        # Extract date range
        all_dates = [exam.get('tarih_saat') for exam in schedule]
        all_dates = [
            d if isinstance(d, datetime) else datetime.fromisoformat(d)
            for d in all_dates
        ]

        baslangic_tarihi = min(all_dates).date()
        bitis_tarihi = max(all_dates).date()

        # Generate program name if not provided
        if not program_name:
            program_name = f"Sınav Programı - {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"

        return {
            'bolum_id': schedule[0].get('bolum_id'),
            'program_adi': program_name,
            'sinav_tipi': schedule[0].get('sinav_tipi', 'Final'),
            'baslangic_tarihi': baslangic_tarihi,
            'bitis_tarihi': bitis_tarihi,
            'aktif': True
        }

    def _group_exams_by_course_time(self, schedule: List[Dict]) -> Dict:
        """Group exams by (ders_id, tarih_saat)"""
        from collections import defaultdict

        exam_groups = defaultdict(list)

        for exam in schedule:
            key = (exam.get('ders_id'), exam.get('tarih_saat'))
            exam_groups[key].append(exam)

        logger.info(
            f"📊 Grouped {len(schedule)} exams into "
            f"{len(exam_groups)} unique course-time combinations"
        )

        return exam_groups

    def _prepare_exam_data(self, exam: Dict, program_id: int) -> Dict:
        """Prepare single exam data for database"""
        sure = exam.get('sure', 120)
        tarih_saat = exam.get('tarih_saat')

        # Convert to datetime if string
        if isinstance(tarih_saat, str):
            tarih_saat = datetime.fromisoformat(tarih_saat)

        # Calculate end time
        bitis_saat = tarih_saat + timedelta(minutes=sure)

        return {
            'program_id': program_id,
            'ders_id': exam.get('ders_id'),
            'tarih': tarih_saat.date(),
            'baslangic_saati': tarih_saat.time(),
            'bitis_saati': bitis_saat.time()
        }

    def _collect_classroom_ids(self, exam_group: List[Dict]) -> List[int]:
        """Collect valid classroom IDs from exam group"""
        derslik_ids = []

        for exam in exam_group:
            derslik_id = exam.get('derslik_id')
            if derslik_id and isinstance(derslik_id, int):
                derslik_ids.append(derslik_id)

        # Remove duplicates while preserving order
        seen = set()
        unique_ids = []
        for did in derslik_ids:
            if did not in seen:
                seen.add(did)
                unique_ids.append(did)

        return unique_ids