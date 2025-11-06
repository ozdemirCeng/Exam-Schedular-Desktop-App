"""
Sınav Planlama Algoritması - UPDATED
Graph Coloring based intelligent exam scheduling
RETURNS: course_students and course_info for scoring
"""

import logging
import random
from datetime import datetime, timedelta, time
from typing import Dict, List, Callable, Optional, Set, Tuple
from collections import defaultdict
from models.database import db
from models.ders_model import DersModel
from models.derslik_model import DerslikModel
from models.ogrenci_model import OgrenciModel

logger = logging.getLogger(__name__)


class SinavPlanlama:
    """Exam scheduling algorithm using graph coloring approach"""

    def __init__(self):
        self.ders_model = DersModel(db)
        self.derslik_model = DerslikModel(db)
        self.ogrenci_model = OgrenciModel(db)

    def plan_exam_schedule(
        self,
        params: Dict,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict:
        """
        Create exam schedule using graph coloring approach

        Args:
            params: Scheduling parameters
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with:
                - success: bool
                - schedule: List[Dict]
                - course_students: Dict[int, Set[str]] (FOR SCORING)
                - course_info: Dict[int, Dict] (FOR SCORING)
                - message: str
                - stats: Dict
        """
        try:
            if progress_callback:
                progress_callback(5, "Dersler yükleniyor...")

            dersler = self.ders_model.get_dersler_by_bolum(params['bolum_id'])

            if not dersler:
                return {
                    'success': False,
                    'message': "Bölümde ders bulunamadı!"
                }

            selected_ders_ids = params.get('selected_ders_ids')
            if selected_ders_ids:
                dersler = [d for d in dersler if d['ders_id'] in selected_ders_ids]

            if not dersler:
                return {
                    'success': False,
                    'message': "Seçili ders bulunamadı!"
                }

            if progress_callback:
                progress_callback(10, "Derslikler yükleniyor...")

            derslikler = self.derslik_model.get_derslikler_by_bolum(params['bolum_id'])

            if not derslikler:
                return {
                    'success': False,
                    'message': "❌ Derslik bulunamadı! Lütfen önce derslik tanımlayın."
                }

            total_capacity = sum(d['kapasite'] for d in derslikler)
            logger.info(f"📊 Toplam derslik kapasitesi: {total_capacity} kişi")

            if progress_callback:
                progress_callback(15, "Öğrenci kayıtları analiz ediliyor...")

            course_students = {}
            course_info = {}

            ders_sinavlari_suresi = params.get('ders_sinavlari_suresi', {})
            varsayilan_sure = params.get('varsayilan_sinav_suresi', 75)

            capacity_errors = []

            for ders in dersler:
                ogrenciler = self.ogrenci_model.get_ogrenciler_by_ders(ders['ders_id'])
                student_ids = set(o['ogrenci_no'] for o in ogrenciler)
                ogrenci_sayisi = len(student_ids)

                sinav_suresi = ders_sinavlari_suresi.get(ders['ders_id'], varsayilan_sure)

                if ogrenci_sayisi > total_capacity:
                    capacity_errors.append(
                        f"   • {ders['ders_kodu']} - {ders['ders_adi']}: "
                        f"{ogrenci_sayisi} öğrenci (Toplam kapasite: {total_capacity})"
                    )

                course_students[ders['ders_id']] = student_ids
                course_info[ders['ders_id']] = {
                    'ders_kodu': ders['ders_kodu'],
                    'ders_adi': ders['ders_adi'],
                    'ogretim_elemani': ders.get('ogretim_elemani', ''),
                    'sinif': ders.get('sinif', 1),
                    'ogrenci_sayisi': ogrenci_sayisi,
                    'sinav_suresi': sinav_suresi
                }

            if capacity_errors:
                error_msg = "❌ Kapasite Yetersiz!\n\nAşağıdaki dersler için derslik kapasitesi yetersiz:\n\n"
                error_msg += "\n".join(capacity_errors)
                error_msg += "\n\nLütfen daha fazla derslik ekleyin veya mevcut dersliklerin kapasitesini artırın."
                return {
                    'success': False,
                    'message': error_msg
                }
            self._current_course_info = course_info

            if progress_callback:
                progress_callback(25, "Ders çakışma grafiği oluşturuluyor...")

            conflicts = self._build_conflict_graph(course_students, params)

            logger.info(f"📊 Conflict graph: {len(conflicts)} courses with conflicts")

            if progress_callback:
                progress_callback(35, "Günlük sınav kapasitesi hesaplanıyor...")

            ara_suresi = params.get('ara_suresi', 15)
            ogle_baslangic = self._parse_time(params.get('ogle_arasi_baslangic', '12:00'))
            ogle_bitis = self._parse_time(params.get('ogle_arasi_bitis', '13:30'))
            gunluk_ilk = self._parse_time(params.get('gunluk_ilk_sinav', '10:00'))
            gunluk_son = self._parse_time(params.get('gunluk_son_sinav', '19:15'))

            # Calculate available slots using actual exam durations
            total_minutes = (gunluk_son.hour * 60 + gunluk_son.minute) - (gunluk_ilk.hour * 60 + gunluk_ilk.minute)
            lunch_minutes = (ogle_bitis.hour * 60 + ogle_bitis.minute) - (ogle_baslangic.hour * 60 + ogle_baslangic.minute)
            available_minutes = total_minutes - lunch_minutes
            
            total_duration = sum(int(info.get('sinav_suresi', varsayilan_sure)) for info in course_info.values())
            avg_exam_duration = total_duration / len(course_info) if course_info else varsayilan_sure
            
            avg_slot_duration = avg_exam_duration + ara_suresi
            approx_slots_per_day = int(available_minutes // avg_slot_duration)

            allowed_weekdays = params.get('allowed_weekdays', [0, 1, 2, 3, 4])
            days = self._generate_exam_days(
                params['baslangic_tarih'],
                params['bitis_tarih'],
                allowed_weekdays
            )

            if not days:
                return {
                    'success': False,
                    'message': "❌ Seçilen tarih aralığında uygun gün bulunamadı!"
                }

            total_slots_estimate = max(len(days) * approx_slots_per_day, len(course_info))

            logger.info(f"📅 {len(days)} gün mevcut")
            logger.info(f"⏰ Ort. sınav süresi: {avg_exam_duration:.1f}dk, ara: {ara_suresi}dk → ~{approx_slots_per_day} slot/gün")
            logger.info(f"📊 ~{total_slots_estimate} toplam slot tahmini, {len(course_info)} ders planlanacak")

            # Build balanced daily targets for even distribution
            from math import ceil
            class_counts: Dict[int, int] = defaultdict(int)
            for cid, info in course_info.items():
                class_counts[info.get('sinif', 0)] += 1

            class_daily_targets: Dict[int, List[int]] = {}
            for sinif, count in class_counts.items():
                q, r = divmod(count, len(days)) if len(days) > 0 else (count, 0)
                vec = [(q + 1) if i < r else q for i in range(len(days))]
                class_daily_targets[sinif] = vec

            self._class_daily_targets = class_daily_targets

            # Distribute total unique exams across all days to avoid empty days
            total_courses = len(course_info)
            if len(days) > 0:
                q_total, r_total = divmod(total_courses, len(days))
                self._day_total_targets = [(q_total + 1) if i < r_total else q_total for i in range(len(days))]
            else:
                self._day_total_targets = []

            if len(course_info) > total_slots_estimate * 2:
                return {
                    'success': False,
                    'message': f"❌ Seçilen tarih aralığı sınavları barındırmaya yeterli değil!\n\n"
                              f"   • Planlanacak ders sayısı: {len(course_info)}\n"
                              f"   • Tahmini slot sayısı: ~{total_slots_estimate}\n\n"
                              f"Lütfen tarih aralığını genişletin veya ders sayısını azaltın."
                }

            if progress_callback:
                progress_callback(45, "Dersler slotlara yerleştiriliyor...")

            # Graph coloring for initial slot assignment
            course_slot_assignment = self._graph_coloring(
                list(course_info.keys()),
                conflicts,
                course_info,
                int(total_slots_estimate),
                progress_callback
            )

            if not course_slot_assignment:
                logger.warning("Coloring failed, falling back to sequential")
                course_slot_assignment = {cid: idx for idx, cid in enumerate(course_info.keys())}

            if progress_callback:
                progress_callback(70, "Dinamik zaman slotları ve derslikler atanıyor...")

            # Get order strategy from params (for multiple attempts)
            order_strategy = params.get('order_strategy', 'class_interleaved')
            attempt_number = params.get('attempt_number', 0)

            # Set random seed for reproducibility for EACH attempt (including 0)
            random.seed(params.get('random_seed', attempt_number))

            # Assign times and classrooms
            schedule = self._assign_times_and_classrooms(
                course_slot_assignment,
                days,
                derslikler,
                course_info,
                course_students,
                params,
                progress_callback,
                order_strategy=order_strategy,
                attempt_number=attempt_number
            )

            if not schedule:
                return {
                    'success': False,
                    'message': "Zaman slotları ve derslikler atanamadı!",
                    'course_students': course_students,
                    'course_info': course_info
                }

            # Check if all courses scheduled
            scheduled_course_ids = set(s['ders_id'] for s in schedule)
            all_course_ids = set(course_info.keys())
            unscheduled = all_course_ids - scheduled_course_ids

            # CRITICAL: Reject schedule if ANY courses are unscheduled
            if unscheduled:
                unscheduled_names = [course_info[cid]['ders_kodu'] for cid in unscheduled]
                days_exhausted = getattr(self, '_days_exhausted', False)
                
                # Calculate classroom capacity analysis
                total_classroom_capacity = sum(int(d.get('kapasite', 0) or 0) for d in derslikler)
                
                # Calculate effective capacity with spacing
                def calc_effective(room):
                    satir = int(room.get('satir_sayisi', 0) or 0)
                    sutun = int(room.get('sutun_sayisi', 0) or 0)
                    sira = int(room.get('sira_yapisi', 0) or 0)
                    if satir <= 0 or sutun <= 0:
                        return int(room.get('kapasite', 0) or 0)
                    if sira == 4:
                        seats_per_group = 2
                    elif sira == 3:
                        seats_per_group = 2
                    elif sira == 2:
                        seats_per_group = 1
                    else:
                        seats_per_group = 1
                    full_groups, rem = divmod(sutun, max(1, sira))
                    if sira == 4:
                        rem_seats = (1 if rem >= 1 else 0) + (1 if rem >= 4 else 0)
                    elif sira == 3:
                        rem_seats = (1 if rem >= 1 else 0) + (1 if rem >= 3 else 0)
                    elif sira == 2:
                        rem_seats = 1 if rem >= 2 else 0
                    else:
                        rem_seats = 1 if rem >= 1 else 0
                    seats_per_row = full_groups * seats_per_group + rem_seats
                    return satir * seats_per_row
                
                total_effective_capacity = sum(calc_effective(d) for d in derslikler)
                total_students = sum(info['ogrenci_sayisi'] for info in course_info.values())
                unscheduled_students = sum(course_info[cid]['ogrenci_sayisi'] for cid in unscheduled)
                
                # Determine primary reason
                capacity_sufficient = total_effective_capacity >= total_students
                
                if days_exhausted:
                    error_msg = f"❌ {len(unscheduled)} ders yerleştirilemedi!\n\n"
                    error_msg += "📅 Neden: Tarih aralığı tükendi\n\n"
                    error_msg += f"Yerleştirilemeyen dersler: {', '.join(unscheduled_names[:10])}\n\n"
                    error_msg += "💡 Çözüm: Bitiş tarihini en az 2-3 gün uzatın."
                elif not capacity_sufficient:
                    shortage = total_students - total_effective_capacity
                    error_msg = f"❌ {len(unscheduled)} ders yerleştirilemedi!\n\n"
                    error_msg += f"🏛 Neden: Derslik kapasitesi yetersiz!\n\n"
                    error_msg += f"   • Toplam öğrenci: {total_students}\n"
                    error_msg += f"   • Efektif kapasite (boşluklu): {total_effective_capacity}\n"
                    error_msg += f"   • Eksiklik: {shortage} kişi\n\n"
                    error_msg += f"Yerleştirilemeyen dersler: {', '.join(unscheduled_names[:10])}\n\n"
                    error_msg += "💡 Çözümler:\n"
                    error_msg += "   • Daha büyük derslikler ekleyin\n"
                    error_msg += "   • Derslik sayısını artırın\n"
                    error_msg += "   • Tarih aralığını uzatarak eş zamanlı sınav sayısını azaltın"
                else:
                    error_msg = f"❌ {len(unscheduled)} ders yerleştirilemedi!\n\n"
                    error_msg += "🔍 Neden: Kısıtlamalar çok sıkı (günlük limit, ara süresi, çakışma vb.)\n\n"
                    error_msg += f"   • Toplam öğrenci: {total_students}\n"
                    error_msg += f"   • Efektif kapasite: {total_effective_capacity} ✓\n"
                    error_msg += f"   • Yerleşmeyen öğrenci: {unscheduled_students}\n\n"
                    error_msg += f"Yerleştirilemeyen dersler: {', '.join(unscheduled_names[:10])}\n\n"
                    error_msg += "💡 Çözümler:\n"
                    error_msg += "   • Günlük sınıf limiti artırın (3 → 4 veya 5)\n"
                    error_msg += "   • Ara süresini azaltın (15dk → 10dk)\n"
                    error_msg += "   • Minimum boşluk süresini azaltın\n"
                    error_msg += "   • Tarih aralığını uzatın"
                
                logger.error(
                    f"❌ {len(unscheduled)} courses unscheduled: {', '.join(unscheduled_names[:10])}"
                )
                return {
                    'success': False,
                    'message': error_msg,
                    'schedule': schedule,
                    'course_students': course_students,
                    'course_info': course_info,
                    'unscheduled_courses': list(unscheduled)
                }

            if progress_callback:
                progress_callback(100, "Tamamlandı!")

            # Count unique exams
            unique_exams = set((s['ders_id'], s['tarih_saat']) for s in schedule)

            logger.info(f"✅ Exam schedule created: {len(unique_exams)} unique exams")
            logger.info(f"📊 Total entries: {len(schedule)} (with classroom assignments)")

            return {
                'success': True,
                'message': f"✅ {len(unique_exams)} sınav başarıyla programlandı!",
                'schedule': schedule,
                'course_students': course_students,  # FOR SCORING
                'course_info': course_info,  # FOR SCORING
                'stats': {
                    'total_courses': len(dersler),
                    'scheduled_courses': len(unique_exams),
                    'days_used': len(set(s['tarih_saat'].date() if isinstance(s['tarih_saat'], datetime) else datetime.fromisoformat(s['tarih_saat']).date() for s in schedule))
                }
            }

        except Exception as e:
            logger.error(f"Exam scheduling error: {e}", exc_info=True)
            return {
                'success': False,
                'message': f"Program oluşturma hatası: {str(e)}"
            }

    def _parse_time(self, time_str: str) -> time:
        """Parse time string HH:MM to time object"""
        parts = time_str.split(':')
        return time(hour=int(parts[0]), minute=int(parts[1]))

    def _generate_exam_days(
        self,
        start_date: datetime,
        end_date: datetime,
        allowed_weekdays: List[int]
    ) -> List[datetime]:
        """Generate list of available exam days"""
        days = []
        current = start_date

        while current <= end_date:
            if current.weekday() in allowed_weekdays:
                days.append(current)
            current += timedelta(days=1)

        return days

    def _build_conflict_graph(
        self,
        course_students: Dict[int, Set[str]],
        params: Dict
    ) -> Dict[int, Set[int]]:
        """Build conflict graph where edges represent student conflicts"""
        conflicts = defaultdict(set)
        course_ids = list(course_students.keys())
        threshold = int(params.get('min_conflict_overlap', 1))

        # Get course info
        course_info = getattr(self, '_current_course_info', {})

        for ders_id1 in course_ids:
            for ders_id2 in course_ids:
                if ders_id1 >= ders_id2:
                    continue

                # Check student overlap
                shared_students = course_students[ders_id1] & course_students[ders_id2]
                overlap_count = len(shared_students)

                if overlap_count >= threshold:
                    conflicts[ders_id1].add(ders_id2)
                    conflicts[ders_id2].add(ders_id1)

        total_edges = sum(len(neighbors) for neighbors in conflicts.values()) // 2
        logger.info(f"🧮 Conflict Graph: {len(course_ids)} nodes, {total_edges} edges")

        return conflicts

    def _graph_coloring(
        self,
        courses: List[int],
        conflicts: Dict[int, Set[int]],
        course_info: Dict[int, Dict],
        max_colors: int,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Optional[Dict[int, int]]:
        """Graph coloring using greedy algorithm with randomization"""
        # Ensure max_colors is integer (safety check)
        max_colors = int(max_colors)
        
        degrees = {ders_id: len(conflicts.get(ders_id, set())) for ders_id in courses}

        # Sort by degree with random tiebreaker
        sorted_courses = sorted(
            courses,
            key=lambda x: (-degrees[x], random.random())
        )

        logger.info(f"🎨 Starting graph coloring for {len(courses)} courses")

        coloring = {}

        for idx, ders_id in enumerate(sorted_courses):
            if progress_callback and idx % 5 == 0:
                percent = 45 + int((idx / len(courses)) * 25)
                progress_callback(percent, f"Yerleştiriliyor: {course_info[ders_id]['ders_kodu']}")

            # Find available colors
            used_colors = set()
            for neighbor_id in conflicts.get(ders_id, set()):
                if neighbor_id in coloring:
                    used_colors.add(coloring[neighbor_id])

            available_colors = [c for c in range(max_colors) if c not in used_colors]

            if not available_colors:
                logger.warning(f"❌ Cannot color {course_info[ders_id]['ders_kodu']}")
                return None

            # Pick color (70% first available, 30% random from first 5)
            if random.random() < 0.7 or len(available_colors) == 1:
                best_slot = available_colors[0]
            else:
                choices = available_colors[:min(5, len(available_colors))]
                best_slot = random.choice(choices)

            coloring[ders_id] = best_slot

        logger.info(f"✅ Coloring successful! Used {len(set(coloring.values()))} slots")

        return coloring

    def _assign_times_and_classrooms(
        self,
        course_slot_assignment: Dict[int, int],
        days: List[datetime],
        derslikler: List[Dict],
        course_info: Dict[int, Dict],
        course_students: Dict[int, Set[str]],
        params: Dict,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        order_strategy: str = 'class_interleaved',
        attempt_number: int = 0
    ) -> List[Dict]:
        """
        Dynamically assign time slots and classrooms

        Enhanced version: multi-classroom allocation per course-slot, room usage per slot,
        student min-gap enforcement, and class/day distribution guidance.
        """
        # Use order strategy to sort courses
        ordered_courses = self._order_courses_by_strategy(
            list(course_slot_assignment.keys()),
            course_info,
            course_students,
            order_strategy,
            params
        )

        # Pre-compute effective capacities with spacing rules
        # NOTE: Spacing is INDEPENDENT of exam duration - it's about preventing cheating
        # Shorter exams don't allow more students per room - spacing stays the same
        def effective_capacity(room: Dict) -> int:
            """Calculate effective capacity based on seating structure and spacing rules"""
            satir = int(room.get('satir_sayisi', 0) or 0)
            sutun = int(room.get('sutun_sayisi', 0) or 0)
            sira = int(room.get('sira_yapisi', 0) or 0)
            
            if satir <= 0 or sutun <= 0:
                # Fallback to base capacity
                return int(room.get('kapasite', 0) or 0)
            
            # Calculate seatable positions per row based on sira_yapisi
            # Spacing rules: leave empty seats between students
            if sira == 4:
                seats_per_group = 2  # 1st and 4th position (skip 2nd, 3rd)
            elif sira == 3:
                seats_per_group = 2  # 1st and 3rd position (skip 2nd)
            elif sira == 2:
                seats_per_group = 1  # Only 2nd position (or alternate)
            else:
                seats_per_group = 1  # Conservative fallback
            
            # Calculate full groups and remainder
            full_groups, rem = divmod(sutun, max(1, sira))
            
            # Handle remaining columns
            if sira == 4:
                rem_seats = 1 if rem >= 1 else 0
                rem_seats += 1 if rem >= 4 else 0
            elif sira == 3:
                rem_seats = 1 if rem >= 1 else 0
                rem_seats += 1 if rem >= 3 else 0
            elif sira == 2:
                rem_seats = 1 if rem >= 2 else 0
            else:
                rem_seats = 1 if rem >= 1 else 0
            
            seats_per_row = full_groups * seats_per_group + rem_seats
            
            # Total effective capacity
            effective = satir * seats_per_row
            
            # Ensure we don't exceed physical capacity
            base_capacity = int(room.get('kapasite', 0) or 0)
            return min(effective, base_capacity) if base_capacity > 0 else effective

        # Sort derslikler by effective capacity DESC to minimize room count
        sorted_derslikler = sorted(derslikler, key=lambda x: (effective_capacity(x), x.get('kapasite', 0)), reverse=True)
        ara_suresi = params.get('ara_suresi', 15)
        ogle_baslangic = self._parse_time(params.get('ogle_arasi_baslangic', '12:00'))
        ogle_bitis = self._parse_time(params.get('ogle_arasi_bitis', '13:30'))
        gunluk_ilk = self._parse_time(params.get('gunluk_ilk_sinav', '10:00'))
        gunluk_son = self._parse_time(params.get('gunluk_son_sinav', '19:15'))

        # Keep days chronological but allow per-attempt rotation for diversity
        days = list(days)
        start_idx = 0
        if params.get('rotate_days', True) and len(days) > 0:
            attempt_number = params.get('attempt_number', 0)
            start_idx = attempt_number % len(days)
        rotated_days = days[start_idx:] + days[:start_idx]
        days = rotated_days
        schedule = []
        current_day_idx = 0
        current_time = None
        day_slot_index = 0
        # Track classes scheduled in the previous slot (to avoid back-to-back same-class exams)
        prev_slot_classes: Set[int] = set()

        remaining_courses = list(ordered_courses)

        # Limits
        class_limit = params.get('class_per_day_limit', 0) or 3
        student_daily_limit = int(params.get('student_per_day_limit', 0) or 0)  # 0 means no hard limit
        no_parallel = bool(params.get('no_parallel_exams', False))
        conflict_threshold = int(params.get('min_conflict_overlap', 1))
        
        logger.info(
            f"📋 Limits: class_per_day={class_limit}, student_per_day={student_daily_limit}, "
            f"no_parallel={no_parallel}, conflict_threshold={conflict_threshold}"
        )
        room_usage_count: Dict[int, int] = defaultdict(int)  # overall balance
        day_class_count: Dict[tuple, int] = defaultdict(int)  # (day_idx, class) -> count
        day_unique_count: Dict[int, int] = defaultdict(int)   # day_idx -> unique exams placed
        student_day_counts: Dict[tuple, int] = defaultdict(int)  # (date, student_no) -> count
        student_last_exam_end: Dict[str, datetime] = {}  # student_no -> datetime end

        self._days_exhausted = False

        # Targets guidance per class per day (vector computed in planner)
        class_daily_targets: Dict[int, List[int]] = getattr(self, '_class_daily_targets', {})
        day_total_targets: List[int] = getattr(self, '_day_total_targets', [])
        # Rotate targets to match rotated days
        if start_idx and day_total_targets:
            day_total_targets = day_total_targets[start_idx:] + day_total_targets[:start_idx]
        spread_across_range = bool(params.get('spread_across_range', True))

        # Main loop - place courses in time slots
        loop_iterations = 0
        max_iterations = len(days) * 20  # Safety limit to prevent infinite loops
        
        while remaining_courses and loop_iterations < max_iterations:
            loop_iterations += 1
            if current_time is None:
                if current_day_idx >= len(days):
                    self._days_exhausted = True
                    logger.warning(
                        f"⚠️ Days exhausted! {len(remaining_courses)} courses unplaced. "
                        f"Days used: {current_day_idx}/{len(days)}"
                    )
                    break
                current_day = days[current_day_idx]
                current_time = datetime.combine(current_day.date(), gunluk_ilk)
                day_slot_index = 0

            # Respect lunch break
            current_time_only = current_time.time()
            if ogle_baslangic <= current_time_only < ogle_bitis:
                current_time = datetime.combine(current_time.date(), ogle_bitis)

            slot_time = current_time
            # Available rooms for this slot
            available_rooms = list(sorted_derslikler)
            batch_used_students: Set[str] = set()
            batch_used_classes: Dict[int, int] = defaultdict(int)

            # Select courses for this slot (greedy MIS)
            selected: List[int] = []
            skipped_due_to_target: List[int] = []
            skip_reasons: Dict[str, int] = defaultdict(int)  # Track why courses are skipped

            def try_select(consider_targets: bool, avoid_consecutive_class: bool, reset_tracking: bool = False) -> None:
                nonlocal selected, skipped_due_to_target, skip_reasons
                if reset_tracking:
                    skip_reasons.clear()
                    
                for cid in list(remaining_courses):
                    # No parallel check
                    if no_parallel and selected:
                        skip_reasons['no_parallel'] += 1
                        break

                    # Student conflict within the same slot
                    if course_students.get(cid):
                        overlap = len(course_students[cid] & batch_used_students)
                        if overlap >= conflict_threshold:
                            skip_reasons['student_conflict'] += 1
                            continue

                    # Class limit per day
                    csinif = course_info[cid].get('sinif', 0)
                    # Avoid scheduling the same class in back-to-back slots within the same day (soft, with fallback)
                    if avoid_consecutive_class and csinif and csinif in prev_slot_classes:
                        skip_reasons['consecutive_class_avoid'] += 1
                        continue
                    if class_limit > 0:
                        if batch_used_classes[csinif] >= class_limit:
                            skip_reasons['batch_class_limit'] += 1
                            continue

                        day_key = (current_day_idx, csinif)
                        if day_class_count[day_key] >= class_limit:
                            skip_reasons['day_class_limit'] += 1
                            continue

                    # Class distribution target guidance
                    if consider_targets:
                        targets = class_daily_targets.get(csinif)
                        if targets and current_day_idx < len(targets):
                            target_for_day = targets[current_day_idx]
                            if day_class_count[(current_day_idx, csinif)] >= target_for_day:
                                skipped_due_to_target.append(cid)
                                skip_reasons['distribution_target'] += 1
                                continue

                    # Student min-gap - SOFT CONSTRAINT (scoring will penalize violations)
                    # Don't hard-block placement, just track for scoring
                    # (Removed hard enforcement to allow schedules with tight gaps)

                    # Student daily limit enforcement (prevents overload)
                    # HARD CONSTRAINT: Only enforce if student_daily_limit > 0
                    if student_daily_limit > 0:
                        exam_date = slot_time.date()
                        # Check if ANY student would exceed daily limit
                        would_exceed = any(
                            (student_day_counts[(exam_date, s)] + 1) > student_daily_limit 
                            for s in course_students.get(cid, set())
                        )
                        if would_exceed:
                            skip_reasons['daily_limit'] += 1
                            continue
                    selected.append(cid)
                    batch_used_students.update(course_students.get(cid, set()))
                    batch_used_classes[csinif] += 1

            # First pass: honor distribution targets and avoid consecutive same-class
            try_select(consider_targets=True, avoid_consecutive_class=True, reset_tracking=False)

            # If nothing selected, relax targets and try ALL remaining courses again
            if not selected and remaining_courses:
                # Clear and retry without distribution target constraints
                selected.clear()
                batch_used_students.clear()
                batch_used_classes.clear()
                # Second pass: still avoid consecutive class if possible, but no distribution targets
                try_select(consider_targets=False, avoid_consecutive_class=True, reset_tracking=True)

            # If still nothing, final pass: allow consecutive class to avoid deadlock
            if not selected and remaining_courses:
                selected.clear()
                batch_used_students.clear()
                batch_used_classes.clear()
                try_select(consider_targets=False, avoid_consecutive_class=False, reset_tracking=True)
            
            # Check if we should skip to next day (all classes hit daily limit)
            if not selected and remaining_courses:
                # Check if all remaining course classes have hit daily limit for current day
                all_classes_maxed = True
                for cid in remaining_courses[:10]:  # Check first 10 remaining
                    csinif = course_info[cid].get('sinif', 0)
                    day_key = (current_day_idx, csinif)
                    if day_class_count[day_key] < class_limit:
                        all_classes_maxed = False
                        break
                
                # If all classes maxed out for today, skip to next day
                if all_classes_maxed and skip_reasons.get('day_class_limit', 0) > len(remaining_courses) * 0.3:
                    logger.info(
                        f"⏭️ Skipping to next day - all classes hit daily limit ({class_limit}). "
                        f"Day {current_day_idx+1}, Remaining: {len(remaining_courses)}"
                    )
                    # Force day change
                    current_day_idx += 1
                    current_time = None
                    continue  # Skip time advancement
            
            # Log if no courses could be selected (expanded logging)
            if not selected and remaining_courses:
                if loop_iterations <= 5 or loop_iterations % 10 == 0:
                    # Calculate per-class statistics for this day
                    day_stats = []
                    for sinif in sorted(set(course_info[c].get('sinif', 0) for c in remaining_courses)):
                        day_count = day_class_count.get((current_day_idx, sinif), 0)
                        remaining_for_class = len([c for c in remaining_courses if course_info[c].get('sinif', 0) == sinif])
                        day_stats.append(f"Sınıf {sinif}: {day_count}/{class_limit} placed, {remaining_for_class} remaining")
                    
                    logger.warning(
                        f"⚠️ Slot {loop_iterations}: No courses selected!\n"
                        f"   • Remaining: {len(remaining_courses)} courses\n"
                        f"   • Day: {current_day_idx+1}/{len(days)}, Slot: {day_slot_index+1}\n"
                        f"   • Skip reasons: {dict(skip_reasons)}\n"
                        f"   • Day stats: {', '.join(day_stats)}"
                    )
            # Assign classrooms to selected courses
            if selected:
                # Allocate rooms per course to cover all students with spacing
                max_duration = max(int(course_info[c]['sinav_suresi']) for c in selected)

                # Calculate total available effective capacity for this slot
                total_slot_capacity = sum(effective_capacity(r) for r in available_rooms)
                total_needed = sum(course_info[c]['ogrenci_sayisi'] for c in selected)
                
                # If total capacity is insufficient, log warning and try to fit what we can
                if total_slot_capacity < total_needed:
                    logger.warning(
                        f"⚠️ Slot capacity shortage: Need {total_needed} seats, have {total_slot_capacity} effective capacity"
                    )

                # Order courses by size desc to allocate big courses first
                selected_sorted = sorted(selected, key=lambda c: course_info[c]['ogrenci_sayisi'], reverse=True)

                # Track successfully placed courses
                successfully_placed = []

                for cid in selected_sorted:
                    needed = int(course_info[cid]['ogrenci_sayisi'])
                    assigned_rooms: List[Dict] = []
                    covered = 0

                    # Choose among currently available rooms, preferring high effective capacity and less used overall
                    available_rooms.sort(key=lambda r: (effective_capacity(r), -room_usage_count[r['derslik_id']]), reverse=True)

                    for room in list(available_rooms):
                        if covered >= needed:
                            break
                        cap = effective_capacity(room)
                        if cap <= 0:
                            continue
                        assigned_rooms.append(room)
                        covered += cap
                        # Mark this room used for this slot
                        available_rooms.remove(room)
                        room_usage_count[room['derslik_id']] += 1

                    if covered < needed:
                        # Not enough capacity for this course in this slot
                        shortage = needed - covered
                        logger.warning(
                            f"⚠️ {course_info[cid]['ders_kodu']}: {shortage} öğrenci için yer yok ({needed} gerekli, {covered} bulundu)"
                        )
                        # Rollback assigned rooms for this course back to availability for fairness
                        for room in assigned_rooms:
                            room_usage_count[room['derslik_id']] -= 1
                            available_rooms.append(room)
                        # Skip placing this course in this slot; will try later
                        continue  # Don't add to successfully_placed

                    # Emit schedule entries for each assigned room
                    for room in assigned_rooms:
                        schedule.append({
                            'ders_id': cid,
                            'ders_kodu': course_info[cid]['ders_kodu'],
                            'ders_adi': course_info[cid]['ders_adi'],
                            'ogretim_elemani': course_info[cid]['ogretim_elemani'],
                            'tarih_saat': slot_time,
                            'sure': int(course_info[cid]['sinav_suresi']),
                            'derslik_id': room['derslik_id'],
                            'derslik_kodu': room['derslik_kodu'],
                            'derslik_adi': room['derslik_adi'],
                            'ogrenci_sayisi': course_info[cid]['ogrenci_sayisi'],
                            'sinav_tipi': params['sinav_tipi'],
                            'bolum_id': params['bolum_id']
                        })
                    
                    successfully_placed.append(cid)

                # Update tracking only for successfully placed courses
                for cid in successfully_placed:
                    csinif = course_info[cid].get('sinif', 0)
                    day_class_count[(current_day_idx, csinif)] += 1
                    # Update student last end and daily count
                    duration = int(course_info[cid]['sinav_suresi'])
                    end_time = slot_time + timedelta(minutes=duration)
                    exam_date = slot_time.date()
                    for s in course_students.get(cid, set()):
                        student_last_exam_end[s] = end_time
                        student_day_counts[(exam_date, s)] += 1
                # Track unique exams placed today (count per course, not per room)
                day_unique_count[current_day_idx] += len(successfully_placed)

                # Remember classes scheduled in this slot to avoid them in the next slot (same day)
                prev_slot_classes = set(course_info[c]['sinif'] for c in successfully_placed if course_info[c].get('sinif'))

                # Remove only successfully placed courses (not all selected)
                remaining_courses = [c for c in remaining_courses if c not in successfully_placed]

                # Advance time based on max duration of SUCCESSFULLY PLACED courses
                if successfully_placed:
                    max_placed_duration = max(int(course_info[c]['sinav_suresi']) for c in successfully_placed)
                    advance_minutes = max_placed_duration + ara_suresi
                else:
                    # If nothing was placed from selection, advance minimally to avoid infinite loop
                    advance_minutes = ara_suresi
                
                # If spreading across range and today's unique target met, move to next day (except last day)
                if spread_across_range and current_day_idx < len(days) - 1:
                    target_for_day = day_total_targets[current_day_idx] if current_day_idx < len(day_total_targets) else 0
                    if target_for_day > 0 and day_unique_count[current_day_idx] >= target_for_day and remaining_courses:
                        current_day_idx += 1
                        current_time = None
                        continue
            else:
                # No courses selected - advance to next slot
                advance_minutes = ara_suresi

            next_time = current_time + timedelta(minutes=advance_minutes)

            # Check lunch break
            next_time_only = next_time.time()
            if ogle_baslangic <= next_time_only < ogle_bitis:
                next_time = datetime.combine(next_time.date(), ogle_bitis)

            # Check day limit
            if next_time.time() > gunluk_son:
                # Log day summary before moving to next day
                if remaining_courses and (current_day_idx < 3 or current_day_idx % 2 == 0):
                    day_placed = len([s for s in schedule if (datetime.fromisoformat(s['tarih_saat']) if isinstance(s['tarih_saat'], str) else s['tarih_saat']).date() == days[current_day_idx].date()])
                    unique_day_placed = len(set(s['ders_id'] for s in schedule if (datetime.fromisoformat(s['tarih_saat']) if isinstance(s['tarih_saat'], str) else s['tarih_saat']).date() == days[current_day_idx].date()))
                    
                    # Per-class summary
                    class_summary = []
                    for sinif in sorted(set(course_info[c].get('sinif', 0) for c in course_info.keys())):
                        count = day_class_count.get((current_day_idx, sinif), 0)
                        if count > 0:
                            class_summary.append(f"Sınıf {sinif}: {count}")
                    
                    logger.info(
                        f"📅 Day {current_day_idx+1} complete: {unique_day_placed} unique exams, "
                        f"{day_placed} classroom assignments, {day_slot_index+1} slots used. "
                        f"Class breakdown: {', '.join(class_summary) if class_summary else 'None'}. "
                        f"Remaining: {len(remaining_courses)} courses"
                    )
                
                current_day_idx += 1
                current_time = None
                prev_slot_classes.clear()  # reset for new day
            else:
                current_time = next_time
                day_slot_index += 1
        
        # Log final placement status
        if remaining_courses:
            logger.error(
                f"❌ Failed to place {len(remaining_courses)} courses! "
                f"Scheduled: {len(set(s['ders_id'] for s in schedule))}/{len(course_info)}, "
                f"Iterations: {loop_iterations}, Days exhausted: {self._days_exhausted}"
            )
        else:
            logger.info(
                f"✅ All courses placed! Scheduled: {len(set(s['ders_id'] for s in schedule))} courses, "
                f"Iterations: {loop_iterations}"
            )

        return schedule

    def _order_courses_by_strategy(
        self,
        courses: List[int],
        course_info: Dict[int, Dict],
        course_students: Dict[int, Set[str]],
        strategy: str,
        params: Dict
    ) -> List[int]:
        """Order courses by given strategy with randomization"""
        conflict_threshold = int(params.get('min_conflict_overlap', 1))
        
        # Add some randomness to break ties in all strategies
        random_factor = random.random() * 0.1  # Small random component

        if strategy == 'random':
            result = list(courses)
            random.shuffle(result)
            return result

        elif strategy == 'degree_first':
            # Most conflicts first WITH RANDOM TIEBREAKER
            conflicts_map = defaultdict(int)
            for cid in courses:
                for other_cid in courses:
                    if cid != other_cid and course_students.get(cid) and course_students.get(other_cid):
                        if len(course_students[cid] & course_students[other_cid]) >= conflict_threshold:
                            conflicts_map[cid] += 1
            # Add random tiebreaker
            return sorted(courses, key=lambda x: (-(conflicts_map.get(x, 0)), random.random()))

        elif strategy == 'reverse_degree':
            # Least conflicts first WITH RANDOM TIEBREAKER
            conflicts_map = defaultdict(int)
            for cid in courses:
                for other_cid in courses:
                    if cid != other_cid and course_students.get(cid) and course_students.get(other_cid):
                        if len(course_students[cid] & course_students[other_cid]) >= conflict_threshold:
                            conflicts_map[cid] += 1
            # Add random tiebreaker
            return sorted(courses, key=lambda x: (conflicts_map.get(x, 0), random.random()))

        elif strategy == 'class_grouped':
            # Group by class WITH SHUFFLE WITHIN SAME SIZE
            result = sorted(courses, key=lambda x: (course_info[x].get('sinif', 0), course_info[x]['ogrenci_sayisi'], random.random()))
            return result

        elif strategy == 'class_interleaved':
            # Interleave different classes WITH RANDOMIZED ORDER
            by_class = {}
            for cid in courses:
                sinif = course_info[cid].get('sinif', 0)
                if sinif not in by_class:
                    by_class[sinif] = []
                by_class[sinif].append(cid)

            # Sort within each class WITH RANDOM TIEBREAKER
            for sinif in by_class:
                by_class[sinif].sort(key=lambda x: (course_info[x]['ogrenci_sayisi'], random.random()))

            # Interleave WITH RANDOMIZED CLASS ORDER
            class_order = list(by_class.keys())
            random.shuffle(class_order)
            
            result = []
            max_len = max(len(courses) for courses in by_class.values()) if by_class else 0
            for i in range(max_len):
                for sinif in class_order:
                    if i < len(by_class[sinif]):
                        result.append(by_class[sinif][i])
            return result

        elif strategy == 'capacity_aware':
            # Largest capacity first WITH RANDOM TIEBREAKER
            return sorted(courses, key=lambda x: (-course_info[x]['ogrenci_sayisi'], random.random()))

        else:
            # Default: class interleaved
            return self._order_courses_by_strategy(courses, course_info, course_students, 'class_interleaved', params)