"""
Sınav Programı Puanlama Sistemi
Her deneme için kalite puanı hesaplar
"""

import logging
from typing import Dict, List, Set
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class SinavProgramScorer:
    """Sınav programı kalite puanlama sistemi"""

    def __init__(self):
        # Puanlama ağırlıkları (0-100 arası normalize edilecek)
        # Çakışma kontrolü placement algoritmasında hard constraint olarak zaten var
        self.weights = {
            'student_daily_limit': 25.0,
            'class_daily_limit': 15.0,
            'student_gaps': 20.0,
            'class_gaps': 15.0,
            'classroom_reuse': 10.0,
            'balanced_distribution': 10.0,
            'exam_duration_opt': 5.0,
        }

    def score_schedule(
            self,
            schedule: List[Dict],
            course_students: Dict[int, Set[str]],
            course_info: Dict[int, Dict],
            params: Dict
    ) -> Dict:
        """
        Sınav programı için toplam kalite puanı hesapla

        Returns:
            {
                'total_score': float (0-100),
                'breakdown': {...},
                'penalties': [...],
                'bonuses': [...],
                'metrics': {...}
            }
        """
        try:
            if not schedule:
                return {
                    'total_score': 0.0,
                    'breakdown': {},
                    'penalties': [],
                    'bonuses': [],
                    'metrics': {}
                }

            # Temel metrikler
            metrics = self._calculate_metrics(schedule, course_students, course_info, params)

            # Her kriter için puan hesapla
            scores = {}
            penalties = []
            bonuses = []

            # NOT: Çakışma kontrolü placement algoritmasında hard constraint
            # Buraya gelen her schedule zaten çakışmasız, puanlamaya gerek yok

            # 1. Öğrenci günlük limit
            student_limit_score, student_details = self._score_student_daily_limit(
                metrics, params
            )
            scores['student_daily_limit'] = student_limit_score
            penalties.extend(student_details.get('penalties', []))
            bonuses.extend(student_details.get('bonuses', []))

            # 2. Sınıf günlük limit
            class_limit_score, class_details = self._score_class_daily_limit(
                metrics, params
            )
            scores['class_daily_limit'] = class_limit_score
            penalties.extend(class_details.get('penalties', []))
            bonuses.extend(class_details.get('bonuses', []))

            # 3. Öğrenci sınavları arası boşluk
            student_gap_score, student_gap_details = self._score_student_gaps(
                metrics, schedule
            )
            scores['student_gaps'] = student_gap_score
            bonuses.extend(student_gap_details.get('bonuses', []))

            # 4. Sınıf sınavları arası boşluk
            class_gap_score, class_gap_details = self._score_class_gaps(
                metrics, schedule
            )
            scores['class_gaps'] = class_gap_score
            bonuses.extend(class_gap_details.get('bonuses', []))

            # 5. Derslik yeniden kullanımı
            classroom_score, classroom_details = self._score_classroom_usage(
                metrics
            )
            scores['classroom_reuse'] = classroom_score
            bonuses.extend(classroom_details.get('bonuses', []))

            # 6. Dengeli dağılım
            balance_score, balance_details = self._score_balanced_distribution(
                metrics, params
            )
            scores['balanced_distribution'] = balance_score
            bonuses.extend(balance_details.get('bonuses', []))

            # 7. Sınav süresi optimizasyonu
            duration_score, duration_details = self._score_exam_duration(
                metrics
            )
            scores['exam_duration_opt'] = duration_score

            # Toplam puan hesapla (ağırlıklı ortalama)
            total_score = sum(
                scores[key] * (self.weights[key] / 100.0)
                for key in scores
            )

            # Breakdown - detaylı puanlama
            breakdown = {
                key: {
                    'score': scores[key],
                    'weight': self.weights[key],
                    'weighted_score': scores[key] * (self.weights[key] / 100.0)
                }
                for key in scores
            }

            return {
                'total_score': round(total_score, 2),
                'breakdown': breakdown,
                'penalties': penalties,
                'bonuses': bonuses,
                'metrics': metrics
            }

        except Exception as e:
            logger.error(f"Score calculation error: {e}", exc_info=True)
            return {
                'total_score': 0.0,
                'breakdown': {},
                'penalties': [f"Hata: {str(e)}"],
                'bonuses': [],
                'metrics': {}
            }

    def _extract_classroom_keys(self, exam: Dict) -> List:
        """Extract classroom identifiers for usage metrics.
        Priority: derslik_id -> derslik_ids -> derslikler -> derslik_adi -> derslik_kodu.
        Returns a list of identifiers (ints or strings).
        """
        keys: List = []
        try:
            # Single id
            if 'derslik_id' in exam and exam['derslik_id']:
                return [exam['derslik_id']]

            # Multiple ids
            if isinstance(exam.get('derslik_ids'), (list, tuple)):
                return [k for k in exam['derslik_ids'] if k]

            # Pre-normalized list field (e.g., from UI path)
            if isinstance(exam.get('derslikler'), (list, tuple)):
                return [k for k in exam['derslikler'] if k]

            # Aggregated strings from DB
            for field in ('derslik_adi', 'derslik_kodu'):
                val = exam.get(field)
                if isinstance(val, str) and val.strip():
                    if ',' in val:
                        parts = [p.strip() for p in val.split(',') if p.strip()]
                        if parts:
                            return parts
                    else:
                        return [val.strip()]
        except Exception:
            pass
        return keys

    def _calculate_metrics(
            self,
            schedule: List[Dict],
            course_students: Dict[int, Set[str]],
            course_info: Dict[int, Dict],
            params: Dict
    ) -> Dict:
        """Temel metrikleri hesapla"""
        metrics = {}

        # Öğrenci bazlı metrikler
        student_daily_exams = defaultdict(lambda: defaultdict(int))
        student_consecutive_days = defaultdict(set)

        # Sınıf bazlı metrikler
        class_daily_exams = defaultdict(lambda: defaultdict(int))
        class_consecutive_days = defaultdict(set)

        # Derslik kullanımı
        classroom_usage = defaultdict(int)
        classroom_daily_usage = defaultdict(lambda: defaultdict(int))

        # Günlere dağılım
        exams_per_day = defaultdict(int)
        class_exams_per_day = defaultdict(lambda: defaultdict(int))
        
        # Min gap violations tracking
        student_exam_times = defaultdict(list)  # student_no -> [(datetime, duration)]
        min_gap_violations = 0
        min_gap_violations_list = []

        # Track unique exams (ders_id, datetime) to avoid counting multi-room as multiple exams
        processed_exams = set()

        for exam in schedule:
            ders_id = exam['ders_id']
            classroom_keys = self._extract_classroom_keys(exam)

            # Tarih parse et
            if isinstance(exam['tarih_saat'], str):
                exam_datetime = datetime.fromisoformat(exam['tarih_saat'])
                exam_date = exam_datetime.date()
            else:
                exam_datetime = exam['tarih_saat']
                exam_date = exam_datetime.date()

            # Unique exam key (same course at same time = one exam, even if multiple rooms)
            exam_key = (ders_id, exam_datetime)
            is_first_room = exam_key not in processed_exams

            if is_first_room:
                processed_exams.add(exam_key)

                # Öğrenci metrikleri - only count once per unique exam
                exam_duration = exam.get('sure', 60)
                for student_no in course_students.get(ders_id, set()):
                    student_daily_exams[student_no][exam_date] += 1
                    student_consecutive_days[student_no].add(exam_date)
                    student_exam_times[student_no].append((exam_datetime, exam_duration))

                # Sınıf metrikleri - only count once per unique exam
                sinif = course_info.get(ders_id, {}).get('sinif', 0)
                if sinif:
                    class_daily_exams[sinif][exam_date] += 1
                    class_consecutive_days[sinif].add(exam_date)
                    class_exams_per_day[exam_date][sinif] += 1

                # Günlük sınav sayısı - only count once per unique exam
                exams_per_day[exam_date] += 1

            # Derslik metrikleri - count every classroom assignment
            if classroom_keys:
                for ck in classroom_keys:
                    classroom_usage[ck] += 1
                    classroom_daily_usage[exam_date][ck] += 1

        # Öğrenci maksimum günlük sınav
        max_student_daily = 0
        avg_student_daily = 0
        student_over_limit = 0
        # Prefer explicit student per-day limit; preserve 0 (means: no limit)
        if 'student_per_day_limit' in params:
            student_limit = params.get('student_per_day_limit')
        elif 'class_per_day_limit' in params:
            student_limit = params.get('class_per_day_limit', 0)
        else:
            student_limit = 4

        if student_daily_exams:
            daily_counts = []
            for student_no, daily_counts_dict in student_daily_exams.items():
                max_for_student = max(daily_counts_dict.values())
                daily_counts.append(max_for_student)
                # If limit == 0, treat as unlimited (no over-limit)
                if student_limit and max_for_student > student_limit:
                    student_over_limit += 1

            max_student_daily = max(daily_counts)
            avg_student_daily = sum(daily_counts) / len(daily_counts)

        # Sınıf maksimum günlük sınav
        max_class_daily = 0
        avg_class_daily = 0
        class_over_limit = 0
        class_limit = params.get('class_per_day_limit', 0) or 3

        if class_daily_exams:
            daily_counts = []
            for sinif, daily_counts_dict in class_daily_exams.items():
                max_for_class = max(daily_counts_dict.values())
                daily_counts.append(max_for_class)
                if max_for_class > class_limit:
                    class_over_limit += 1

            max_class_daily = max(daily_counts)
            avg_class_daily = sum(daily_counts) / len(daily_counts)

        # Peş peşe gün sayıları
        student_consecutive_counts = {
            student_no: self._count_consecutive_days(sorted(days))
            for student_no, days in student_consecutive_days.items()
        }

        class_consecutive_counts = {
            sinif: self._count_consecutive_days(sorted(days))
            for sinif, days in class_consecutive_days.items()
        }
        
        # Calculate min gap violations
        required_gap_minutes = params.get('ara_suresi', 15)
        for student_no, exam_list in student_exam_times.items():
            # Sort by time
            sorted_exams = sorted(exam_list, key=lambda x: x[0])
            
            for i in range(len(sorted_exams) - 1):
                exam1_start, exam1_duration = sorted_exams[i]
                exam2_start, exam2_duration = sorted_exams[i + 1]
                
                exam1_end = exam1_start + timedelta(minutes=exam1_duration)
                gap_minutes = (exam2_start - exam1_end).total_seconds() / 60
                
                if gap_minutes < required_gap_minutes:
                    min_gap_violations += 1
                    min_gap_violations_list.append({
                        'student': student_no,
                        'gap_minutes': gap_minutes,
                        'required': required_gap_minutes
                    })

        # Derslik dengeli kullanım
        classroom_balance = 0
        if classroom_usage:
            avg_usage = sum(classroom_usage.values()) / len(classroom_usage)
            variance = sum((count - avg_usage) ** 2 for count in classroom_usage.values()) / len(classroom_usage)
            classroom_balance = 100 - min(100, variance)  # Düşük varyans = yüksek puan

        # Günlere dengeli dağılım
        day_balance = 0
        if exams_per_day:
            avg_per_day = sum(exams_per_day.values()) / len(exams_per_day)
            variance = sum((count - avg_per_day) ** 2 for count in exams_per_day.values()) / len(exams_per_day)
            day_balance = 100 - min(100, variance * 5)  # Düşük varyans = yüksek puan

        metrics['student_daily_exams'] = dict(student_daily_exams)
        metrics['max_student_daily'] = max_student_daily
        metrics['avg_student_daily'] = avg_student_daily
        metrics['student_over_limit'] = student_over_limit
        metrics['student_consecutive_counts'] = student_consecutive_counts
        metrics['min_gap_violations'] = min_gap_violations
        metrics['min_gap_violations_list'] = min_gap_violations_list[:10]  # First 10 for details

        metrics['class_daily_exams'] = dict(class_daily_exams)
        metrics['max_class_daily'] = max_class_daily
        metrics['avg_class_daily'] = avg_class_daily
        metrics['class_over_limit'] = class_over_limit
        metrics['class_consecutive_counts'] = class_consecutive_counts

        metrics['classroom_usage'] = dict(classroom_usage)
        metrics['classroom_daily_usage'] = dict(classroom_daily_usage)
        metrics['classroom_balance'] = classroom_balance

        metrics['exams_per_day'] = dict(exams_per_day)
        metrics['day_balance'] = day_balance
        metrics['class_exams_per_day'] = dict(class_exams_per_day)

        return metrics

    def _count_consecutive_days(self, sorted_dates: List) -> int:
        """Peş peşe gün sayısını hesapla"""
        if not sorted_dates:
            return 0

        max_consecutive = 1
        current_consecutive = 1

        for i in range(1, len(sorted_dates)):
            diff = (sorted_dates[i] - sorted_dates[i - 1]).days
            if diff == 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1

        return max_consecutive

    def _score_conflicts(
            self,
            schedule: List[Dict],
            course_students: Dict[int, Set[str]],
            params: Dict
    ) -> tuple:
        """Çakışma puanı (100 = hiç çakışma yok)"""
        penalties = []

        # Aynı zamandaki sınavları grupla
        time_slots = defaultdict(list)
        for exam in schedule:
            time_key = exam['tarih_saat']
            time_slots[time_key].append(exam)

        total_conflicts = 0

        for time_key, exams in time_slots.items():
            # Aynı anda birden fazla sınav varsa
            if len(exams) > 1:
                # Get unique courses in this time slot
                unique_courses = {}
                for exam in exams:
                    ders_id = exam['ders_id']
                    if ders_id not in unique_courses:
                        unique_courses[ders_id] = exam
                
                # Only check conflicts between different courses
                unique_exam_list = list(unique_courses.values())
                
                # Öğrenci çakışması kontrolü
                for i, exam1 in enumerate(unique_exam_list):
                    for exam2 in unique_exam_list[i + 1:]:
                        ders_id1 = exam1['ders_id']
                        ders_id2 = exam2['ders_id']

                        students1 = course_students.get(ders_id1, set())
                        students2 = course_students.get(ders_id2, set())

                        overlap = len(students1 & students2)
                        if overlap > 0:
                            total_conflicts += overlap
                            penalties.append(
                                f"❌ {exam1.get('ders_kodu', '?')} ve {exam2.get('ders_kodu', '?')} "
                                f"aynı anda: {overlap} öğrenci çakışması"
                            )

        # Çakışma yoksa 100, her çakışma için -10 puan
        score = max(0, 100 - (total_conflicts * 10))

        return score, {'penalties': penalties}

    def _score_student_daily_limit(self, metrics: Dict, params: Dict) -> tuple:
        """Öğrenci günlük sınav limiti puanı - HARD CONSTRAINT"""
        max_daily = metrics.get('max_student_daily', 0)
        avg_daily = metrics.get('avg_student_daily', 0)
        over_limit = metrics.get('student_over_limit', 0)

        # Prefer explicit student per-day limit if provided
        # Preserve 0 (no limit) and avoid truthiness fallbacks
        if 'student_per_day_limit' in params:
            limit = params.get('student_per_day_limit')
        elif 'class_per_day_limit' in params:
            limit = params.get('class_per_day_limit', 0)
        else:
            limit = 4

        penalties = []
        bonuses = []

        # If limit == 0 (no limit), award full score for this criterion
        if limit == 0:
            bonuses.append("✅ Öğrenci günlük limit uygulanmıyor (sınırsız)")
            return 100, {'penalties': penalties, 'bonuses': bonuses}

        # HARD CONSTRAINT: Limit exceeded should NOT happen (algorithm blocks it)
        # But if it somehow occurs, heavily penalize
        if over_limit > 0:
            penalties.append(f"❌ UYARI: {over_limit} öğrenci günlük limiti ({limit}) aştı!")
            # This shouldn't happen with hard constraint - heavy penalty
            score = max(0, 100 - (over_limit * 50))
        # Perfect: max 2, average <= 1.5
        elif max_daily <= 2 and avg_daily <= 1.5:
            bonuses.append(f"✅ Öğrenci yükü mükemmel (Max: {max_daily}, Ort: {avg_daily:.1f})")
            score = 100
        # Very good: max 2
        elif max_daily <= 2:
            bonuses.append(f"✅ Öğrenci yükü çok iyi (Max: {max_daily})")
            score = 95
        # Good: max 3, average reasonable
        elif max_daily <= 3 and avg_daily <= 2.0:
            score = 85
        # Acceptable: at limit
        elif max_daily <= limit:
            score = 70 - ((max_daily - 3) * 10)
        # Bad: over ideal but under hard limit
        else:
            score = max(30, 70 - ((max_daily - limit) * 20))

        return max(0, score), {'penalties': penalties, 'bonuses': bonuses}

    def _score_class_daily_limit(self, metrics: Dict, params: Dict) -> tuple:
        """Sınıf günlük sınav limiti puanı - STRICT VERSION"""
        max_daily = metrics.get('max_class_daily', 0)
        avg_daily = metrics.get('avg_class_daily', 0)
        over_limit = metrics.get('class_over_limit', 0)

        limit = params.get('class_per_day_limit', 0) or 3

        penalties = []
        bonuses = []

        # STRICTER: Limit aşımı ciddi ceza
        if over_limit > 0:
            penalties.append(f"❌ {over_limit} sınıf günlük limiti ({limit}) aşıyor!")
            score = max(0, 100 - (over_limit * 30))
        # Perfect: max 2, avg low
        elif max_daily <= 2 and avg_daily <= 1.5:
            bonuses.append(f"✅ Sınıf dağılımı mükemmel (Max: {max_daily}, Ort: {avg_daily:.1f})")
            score = 100
        # Very good: max 2
        elif max_daily <= 2:
            score = 95
        # Good: at limit with good average
        elif max_daily <= limit and avg_daily <= 2.0:
            bonuses.append(f"✅ Sınıf dağılımı iyi (Max: {max_daily})")
            score = 85
        # Acceptable: at limit
        elif max_daily <= limit:
            score = 70
        # Bad
        else:
            score = max(20, 70 - ((max_daily - limit) * 25))

        return max(0, score), {'penalties': penalties, 'bonuses': bonuses}

    def _score_student_gaps(self, metrics: Dict, schedule: List[Dict]) -> tuple:
        """Öğrenci sınavları arası boşluk puanı - includes min gap violations"""
        consecutive_counts = metrics.get('student_consecutive_counts', {})
        min_gap_violations = metrics.get('min_gap_violations', 0)
        min_gap_violations_list = metrics.get('min_gap_violations_list', [])
        penalties = []
        bonuses = []

        if not consecutive_counts:
            return 100, {'bonuses': [], 'penalties': []}

        # Calculate consecutive days statistics
        avg_consecutive = sum(consecutive_counts.values()) / len(consecutive_counts)
        max_consecutive = max(consecutive_counts.values())
        
        # Count how many students have back-to-back exams
        students_with_consecutive = sum(1 for count in consecutive_counts.values() if count > 1)
        total_students = len(consecutive_counts)
        consecutive_ratio = students_with_consecutive / total_students if total_students > 0 else 0

        # BASE SCORING from consecutive days
        if max_consecutive == 1 and avg_consecutive == 1.0:
            # Perfect: no student has exams on consecutive days
            bonuses.append(f"✅ HİÇ öğrenci peş peşe sınava girmiyor!")
            base_score = 100
        elif max_consecutive <= 2 and avg_consecutive <= 1.3 and consecutive_ratio < 0.3:
            # Very good: max 2 consecutive days, very few students affected
            bonuses.append(f"✅ Çok az öğrenci peş peşe ({int(consecutive_ratio*100)}%)")
            base_score = 95
        elif max_consecutive <= 2 and avg_consecutive <= 1.5:
            # Good: max 2 consecutive, moderate average
            base_score = 85
        elif max_consecutive == 3:
            # Acceptable: some students have 3 consecutive days
            penalties.append(f"⚠️ Bazı öğrenciler 3 gün peş peşe sınava giriyor")
            base_score = 70
        elif max_consecutive == 4:
            penalties.append(f"⚠️ Bazı öğrenciler 4 gün peş peşe sınava giriyor")
            base_score = 50
        else:
            # Poor: too many consecutive days
            penalties.append(f"❌ {max_consecutive} gün peş peşe sınav var!")
            base_score = max(20, 100 - (max_consecutive * 15))
        
        # PENALIZE MIN GAP VIOLATIONS
        if min_gap_violations > 0:
            penalty = min(40, min_gap_violations * 2)  # Max -40 points
            penalties.append(
                f"⚠️ {min_gap_violations} öğrenci minimum ara süresinden önce sınava giriyor!"
            )
            base_score = max(0, base_score - penalty)

        return base_score, {'bonuses': bonuses, 'penalties': penalties}

    def _score_class_gaps(self, metrics: Dict, schedule: List[Dict]) -> tuple:
        """Sınıf sınavları arası boşluk puanı - STRICT VERSION"""
        consecutive_counts = metrics.get('class_consecutive_counts', {})
        penalties = []
        bonuses = []

        if not consecutive_counts:
            return 100, {'bonuses': [], 'penalties': []}

        avg_consecutive = sum(consecutive_counts.values()) / len(consecutive_counts)
        max_consecutive = max(consecutive_counts.values())
        
        # Count classes with back-to-back exams
        classes_with_consecutive = sum(1 for count in consecutive_counts.values() if count > 1)
        total_classes = len(consecutive_counts)
        consecutive_ratio = classes_with_consecutive / total_classes if total_classes > 0 else 0

        # STRICTER SCORING
        if max_consecutive == 1 and avg_consecutive == 1.0:
            # Perfect: no class has exams on consecutive days
            bonuses.append(f"✅ HİÇ sınıf peş peşe sınava girmiyor!")
            score = 100
        elif max_consecutive <= 2 and avg_consecutive <= 1.3 and consecutive_ratio < 0.3:
            # Very good
            bonuses.append(f"✅ Çok az sınıf peş peşe ({int(consecutive_ratio*100)}%)")
            score = 90
        elif max_consecutive <= 2 and avg_consecutive <= 1.5:
            # Good
            score = 80
        elif max_consecutive == 3:
            penalties.append(f"⚠️ Bazı sınıflar 3 gün peş peşe sınava giriyor")
            score = 65
        elif max_consecutive == 4:
            penalties.append(f"⚠️ Bazı sınıflar 4 gün peş peşe sınava giriyor")
            score = 45
        else:
            penalties.append(f"❌ {max_consecutive} gün peş peşe sınıf sınavı var!")
            score = max(20, 100 - (max_consecutive * 20))

        return score, {'bonuses': bonuses, 'penalties': penalties}

    def _score_classroom_usage(self, metrics: Dict) -> tuple:
        """Derslik kullanım dengesi puanı"""
        classroom_balance = metrics.get('classroom_balance', 0)
        bonuses = []

        if classroom_balance >= 90:
            bonuses.append("✅ Derslikler dengeli kullanılmış")

        return classroom_balance, {'bonuses': bonuses}

    def _score_balanced_distribution(self, metrics: Dict, params: Dict) -> tuple:
        """Dengeli günlere dağılım puanı"""
        class_exams_per_day = metrics.get('class_exams_per_day', {})
        bonuses = []

        # Her sınıf için günlere dengeli dağılım kontrolü
        if class_exams_per_day:
            class_balance_scores = []

            for date, class_counts in class_exams_per_day.items():
                for sinif, count in class_counts.items():
                    # Sınıf için toplam sınav sayısı
                    # Bu kısım params'tan alınabilir ama şimdilik count'u kullan
                    class_balance_scores.append(count)

            if class_balance_scores:
                avg = sum(class_balance_scores) / len(class_balance_scores)
                variance = sum((c - avg) ** 2 for c in class_balance_scores) / len(class_balance_scores)

                # Düşük varyans = dengeli dağılım
                if variance <= 1:
                    bonuses.append("✅ Sınavlar günlere çok dengeli dağılmış")
                    score = 100
                elif variance <= 2:
                    score = 85
                else:
                    score = max(50, 100 - (variance * 10))
            else:
                score = 100
        else:
            score = 100

        return score, {'bonuses': bonuses}

    def _score_exam_duration(self, metrics: Dict) -> tuple:
        """Sınav süresi optimizasyon puanı"""
        # Bu kısım daha detaylı olabilir, şimdilik basit bir hesap
        # Uzun sınavlar gün sonu varsa puan düşer

        # Şimdilik sabit puan
        return 80, {}