"""
Sınav Programı Deneme Yöneticisi
Birden fazla deneme yapar ve en iyisini seçer
"""

import logging
import random
import hashlib
import json
from typing import Dict, List, Callable, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AttemptManager:
    """Çoklu deneme yönetimi ve en iyi sonuç seçimi"""

    def __init__(self, scorer):
        self.scorer = scorer
        self.attempts_history = []

    def run_multiple_attempts(
            self,
            planning_function: Callable,
            params: Dict,
            max_attempts: int = 50,
            progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict:
        """
        Birden fazla deneme yap ve en iyisini döndür

        Args:
            planning_function: Planlama algoritması fonksiyonu
            params: Planlama parametreleri
            max_attempts: Maksimum deneme sayısı
            progress_callback: İlerleme callback'i

        Returns:
            En iyi sonuç dict'i
        """
        try:
            self.attempts_history = []
            best_result = None
            best_score = -1

            logger.info(f"🎯 {max_attempts} deneme başlatılıyor...")

            # Compute deterministic base seed by default from params (so same inputs => same results)
            # If params['randomize'] is True, use time-based seed to explore new spaces.
            base_seed = self._compute_base_seed(params)
            logger.info(f"🎲 Base seed: {base_seed} (randomize={bool(params.get('randomize', False))})")

            # Farklı stratejilerle denemeler
            strategies = [
                'class_interleaved',
                'reverse_degree',
                'degree_first',
                'random',
                'class_grouped',
                'capacity_aware'
            ]
            # Shuffle strategies deterministically per run to avoid fixed first strategy bias
            rnd = random.Random(base_seed)
            rnd.shuffle(strategies)

            attempts_without_improvement = 0
            max_no_improvement = 50  # Allow more attempts without improvement for thorough search

            for attempt in range(max_attempts):
                try:
                    # Strateji seç (döngüsel + rastgele)
                    if attempt < len(strategies):
                        strategy = strategies[attempt]
                    else:
                        strategy = random.choice(strategies)

                    # İlerleme güncelle
                    if progress_callback:
                        progress = 50 + int((attempt / max_attempts) * 45)
                        progress_callback(
                            progress,
                            f"Deneme {attempt + 1}/{max_attempts} - Strateji: {strategy}"
                        )

                    # Parametreleri kopyala ve strateji ekle
                    attempt_params = params.copy()
                    attempt_params['order_strategy'] = strategy
                    attempt_params['attempt_number'] = attempt

                    # Rastgelelik ekle (her denemede FARKLI sonuç için)
                    # Different attempts = different seeds, same click = same results
                    random_seed = base_seed + attempt * 1000
                    random.seed(random_seed)
                    attempt_params['random_seed'] = random_seed
                    # Rotate days per attempt to increase diversity while preserving spread
                    attempt_params['rotate_days'] = True

                    # Planlama yap
                    result = planning_function(attempt_params, progress_callback=None)

                    if not result.get('success') or not result.get('schedule'):
                        logger.warning(f"Attempt {attempt + 1}: Failed to generate schedule")
                        # Store failed attempt with error details
                        attempt_record = {
                            'attempt_number': attempt + 1,
                            'strategy': strategy,
                            'score': 0,
                            'schedule': [],
                            'score_details': {},
                            'timestamp': datetime.now(),
                            'result': result,
                            'failed': True,
                            'error_message': result.get('message', 'Bilinmeyen hata')
                        }
                        self.attempts_history.append(attempt_record)
                        continue

                    schedule = result['schedule']

                    # Puanlama yap
                    score_result = self.scorer.score_schedule(
                        schedule,
                        result.get('course_students', {}),
                        result.get('course_info', {}),
                        params
                    )

                    total_score = score_result['total_score']

                    # Kaydet
                    attempt_record = {
                        'attempt_number': attempt + 1,
                        'strategy': strategy,
                        'score': total_score,
                        'schedule': schedule,
                        'score_details': score_result,
                        'timestamp': datetime.now(),
                        'result': result
                    }

                    self.attempts_history.append(attempt_record)

                    # En iyi kontrol
                    if total_score > best_score:
                        best_score = total_score
                        best_result = attempt_record
                        attempts_without_improvement = 0

                        logger.info(
                            f"✨ Yeni en iyi! Deneme {attempt + 1}: "
                            f"Puan={total_score:.2f}, Strateji={strategy}"
                        )
                    else:
                        attempts_without_improvement += 1

                    # Mükemmel puan bulunduysa dur (threshold raised to 98 for more thorough optimization)
                    if total_score >= 98:
                        logger.info(f"🎉 Mükemmel puan bulundu! ({total_score:.2f})")
                        break

                    # İyileşme yoksa dur (only after minimum 50 attempts for diversity)
                    if attempts_without_improvement >= max_no_improvement and attempt > 150:
                        logger.info(
                            f"⚠️ {max_no_improvement} denemedir iyileşme yok, durduruluyor..."
                        )
                        break

                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} error: {e}", exc_info=True)
                    continue

            if not best_result:
                # Analyze why all attempts failed
                failure_analysis = self._analyze_failures(self.attempts_history)
                
                return {
                    'success': False,
                    'message': failure_analysis['message'],
                    'details': failure_analysis['details'],
                    'suggestions': failure_analysis['suggestions'],
                    'attempts_count': len(self.attempts_history)
                }

            # En iyi sonucu döndür
            logger.info(f"✅ En iyi sonuç: Puan={best_score:.2f}, Deneme={best_result['attempt_number']}")

            # score_details'e attempt bilgisini ekle
            score_details_with_attempt = best_result['score_details'].copy()
            score_details_with_attempt['best_attempt'] = best_result['attempt_number']
            score_details_with_attempt['total_attempts'] = len(self.attempts_history)
            score_details_with_attempt['strategy_used'] = best_result['strategy']

            return {
                'success': True,
                'schedule': best_result['schedule'],
                'score': best_score,
                'score_details': score_details_with_attempt,
                'best_attempt': best_result['attempt_number'],
                'total_attempts': len(self.attempts_history),
                'strategy_used': best_result['strategy'],
                'attempts_history': self._get_summary_history(),
                'base_seed': base_seed,
                'message': self._format_success_message(best_result, len(self.attempts_history))
            }

        except Exception as e:
            logger.error(f"Multiple attempts error: {e}", exc_info=True)
            return {
                'success': False,
                'message': f"❌ Planlama sistemi hatası: {str(e)}",
                'details': f"Kritik hata oluştu:\n{str(e)}\n\nLütfen log dosyalarını kontrol edin.",
                'suggestions': [
                    "📋 Uygulama loglarını kontrol edin",
                    "🔄 Uygulamayı yeniden başlatın",
                    "📞 Teknik destek ile iletişime geçin"
                ],
                'attempts_count': len(self.attempts_history),
                'error': str(e)
            }

    def _get_summary_history(self) -> List[Dict]:
        """Özet deneme geçmişi"""
        return [
            {
                'attempt': h['attempt_number'],
                'strategy': h['strategy'],
                'score': h['score'],
                'timestamp': h['timestamp'].isoformat()
            }
            for h in self.attempts_history
        ]

    def _format_success_message(self, best_result: Dict, total_attempts: int) -> str:
        """Başarı mesajı formatla"""
        score = best_result['score']
        score_details = best_result['score_details']

        msg = f"✅ En iyi program oluşturuldu!\n\n"
        msg += f"📊 Toplam Puan: {score:.2f}/100\n"
        msg += f"🔄 Deneme: {best_result['attempt_number']}/{total_attempts}\n"
        msg += f"🎯 Strateji: {best_result['strategy']}\n\n"

        # Bonuslar
        bonuses = score_details.get('bonuses', [])
        if bonuses:
            msg += "✨ Artılar:\n"
            for bonus in bonuses[:5]:  # İlk 5 bonus
                msg += f"  {bonus}\n"
            msg += "\n"

        # Cezalar
        penalties = score_details.get('penalties', [])
        if penalties:
            msg += "⚠️ İyileştirme Alanları:\n"
            for penalty in penalties[:5]:  # İlk 5 ceza
                msg += f"  {penalty}\n"
            msg += "\n"

        # Metrikler
        metrics = score_details.get('metrics', {})
        if metrics:
            msg += "📈 Metrikler:\n"
            msg += f"  • Öğrenci max günlük: {metrics.get('max_student_daily', 0)}\n"
            msg += f"  • Sınıf max günlük: {metrics.get('max_class_daily', 0)}\n"
            msg += f"  • Derslik dengesi: {metrics.get('classroom_balance', 0):.0f}%\n"

        return msg

    def _normalize_params_for_seed(self, params: Dict) -> Dict:
        """Pick only seed-relevant keys and normalize values for stable hashing."""
        keys = [
            'bolum_id', 'sinav_tipi', 'baslangic_tarih', 'bitis_tarih',
            'allowed_weekdays', 'selected_ders_ids', 'gunluk_ilk_sinav', 'gunluk_son_sinav',
            'ogle_arasi_baslangic', 'ogle_arasi_bitis', 'no_parallel_exams',
            'class_per_day_limit', 'student_per_day_limit', 'ara_suresi', 'ders_sinavlari_suresi'
        ]
        norm: Dict = {}
        for k in keys:
            if k not in params:
                continue
            v = params[k]
            # Normalize datetime to isoformat
            if k in ('baslangic_tarih', 'bitis_tarih') and hasattr(v, 'isoformat'):
                norm[k] = v.isoformat()
            # Normalize list-like
            elif k in ('allowed_weekdays', 'selected_ders_ids') and isinstance(v, (list, tuple, set)):
                norm[k] = sorted(list(v))
            # Normalize dict of durations
            elif k == 'ders_sinavlari_suresi' and isinstance(v, dict):
                # keys to str, sort by key
                norm[k] = {str(kk): int(v[kk]) for kk in sorted(v.keys(), key=lambda x: str(x))}
            else:
                norm[k] = v
        return norm

    def _compute_base_seed(self, params: Dict) -> int:
        """Deterministic seed unless randomize=True; stable across identical params."""
        try:
            if params.get('randomize', False):
                import time
                return int(time.time() * 1000)
            normalized = self._normalize_params_for_seed(params)
            payload = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
            h = hashlib.sha256(payload.encode('utf-8')).hexdigest()
            # Use lower 12 hex digits for a large but int-sized seed
            return int(h[-12:], 16)
        except Exception:
            # Fallback to time if anything goes wrong
            import time
            return int(time.time() * 1000)

    def _analyze_failures(self, attempts_history: List[Dict]) -> Dict:
        """
        Analyze why all attempts failed and provide detailed feedback
        
        Returns:
            {
                'message': str - Main error message,
                'details': str - Detailed explanation,
                'suggestions': List[str] - Actionable suggestions
            }
        """
        if not attempts_history:
            return {
                'message': "❌ Hiçbir deneme yapılamadı!",
                'details': "Planlama başlatılamadı. Sistemde bir hata olabilir.",
                'suggestions': [
                    "Tüm derslerin öğrenci kayıtları olduğundan emin olun",
                    "En az bir derslik tanımlandığından emin olun",
                    "Tarih aralığında en az 3-5 gün olmasını sağlayın"
                ]
            }
        
        # Collect ALL unique error messages from failed attempts
        all_error_messages = []
        error_message_counts = {}
        
        for attempt in attempts_history:
            if attempt.get('failed'):
                error_msg = attempt.get('error_message', '')
                if error_msg and error_msg not in all_error_messages:
                    all_error_messages.append(error_msg)
                if error_msg:
                    error_message_counts[error_msg] = error_message_counts.get(error_msg, 0) + 1
        
        # If we have actual error messages, show them!
        if all_error_messages:
            most_common_error = max(error_message_counts, key=error_message_counts.get)
            error_count = error_message_counts[most_common_error]
            
            details = f"🔴 Tekrarlanan Hata ({error_count}/{len(attempts_history)} deneme):\n\n"
            details += f"{most_common_error}\n\n"
            
            # Show other unique errors if any
            other_errors = [msg for msg in all_error_messages if msg != most_common_error]
            if other_errors:
                details += f"📋 Diğer Hatalar:\n"
                for err in other_errors[:3]:  # Show max 3 other errors
                    count = error_message_counts.get(err, 0)
                    details += f"  • ({count}x) {err[:100]}...\n" if len(err) > 100 else f"  • ({count}x) {err}\n"
            
            # Parse error for specific suggestions
            suggestions = self._generate_suggestions_from_error(most_common_error)
            
            return {
                'message': "❌ Sınav programı oluşturulamadı!",
                'details': details,
                'suggestions': suggestions
            }
        
        # If no error messages but all failed, do pattern analysis
        return self._analyze_failure_patterns(attempts_history)

    def _generate_suggestions_from_error(self, error_message: str) -> List[str]:
        """Generate specific suggestions based on error message"""
        suggestions = []
        error_lower = error_message.lower()
        
        # Kapasite hataları
        if 'kapasite' in error_lower or 'capacity' in error_lower:
            suggestions.extend([
                "🏫 Daha fazla derslik ekleyin",
                "📊 Mevcut dersliklerin kapasitesini artırın",
                "👥 Sıra yapısını değiştirin (örn: 2'li yerine 3'lü)",
                "📅 Tarih aralığını genişletin (daha az yoğunluk)",
                "🔄 'Paralel sınav olmasın' kapalıysa açın"
            ])
        
        # Ders bulunamadı
        elif 'ders bulunamadı' in error_lower or 'no courses' in error_lower:
            suggestions.extend([
                "📚 En az bir ders seçtiğinizden emin olun",
                "✅ Seçili derslerin aktif olduğunu kontrol edin",
                "👥 Seçili derslere öğrenci kaydı yapıldığından emin olun"
            ])
        
        # Derslik bulunamadı
        elif 'derslik bulunamadı' in error_lower or 'no classroom' in error_lower:
            suggestions.extend([
                "🏫 Bölüm için en az bir derslik tanımlayın",
                "✅ Dersliklerin aktif olduğunu kontrol edin",
                "📊 Derslik kapasitelerini kontrol edin"
            ])
        
        # Tarih/gün sorunları
        elif 'gün' in error_lower or 'tarih' in error_lower or 'date' in error_lower:
            suggestions.extend([
                "📅 Daha geniş tarih aralığı seçin (en az 5-7 gün)",
                "✅ En az bir gün seçili olduğundan emin olun",
                "📆 Cumartesi/Pazar günlerini de etkinleştirmeyi deneyin"
            ])
        
        # Öğrenci bulunamadı
        elif 'öğrenci' in error_lower and 'bulunamadı' in error_lower:
            suggestions.extend([
                "👥 Seçili derslere öğrenci kaydı yapın",
                "✅ Öğrenci kayıtlarının aktif olduğunu kontrol edin"
            ])
        
        # Genel öneriler ekle
        if not suggestions:
            suggestions.extend([
                "📋 Hata mesajını dikkatlice okuyun",
                "🔍 Belirtilen ders/derslik/tarih bilgilerini kontrol edin",
                "📞 Sorun devam ederse teknik destek ile iletişime geçin"
            ])
        
        return suggestions

    def _analyze_failure_patterns(self, attempts_history: List[Dict]) -> Dict:
        """Analyze patterns when no explicit error messages"""
        
        # Collect common patterns from all failed attempts
        common_issues = []
        unscheduled_courses = set()
        capacity_errors = []
        conflict_errors = []
        day_exhausted_count = 0
        empty_schedule_count = 0
        
        for attempt in attempts_history:
            result = attempt.get('result', {})
            
            # Check if schedule was empty
            schedule = result.get('schedule', [])
            if not schedule or len(schedule) == 0:
                empty_schedule_count += 1
            
            # Check for unscheduled courses
            unscheduled = result.get('unscheduled_courses', [])
            if unscheduled:
                unscheduled_courses.update(unscheduled)
            
            # Check for days exhausted
            message = result.get('message', '')
            if 'yerleştirilemedi' in message.lower() or 'days_exhausted' in str(result):
                day_exhausted_count += 1
            
            # Look for capacity issues in message
            if 'kapasite' in message.lower():
                capacity_errors.append(message)
            
            # Look for conflict issues
            if 'çakış' in message.lower():
                conflict_errors.append(message)
        
        # Build detailed message based on patterns
        message = "❌ Sınav programı oluşturulamadı!"
        details = ""
        suggestions = []
        
        total_attempts = len(attempts_history)
        
        # Pattern 1: All attempts produced empty schedules
        if empty_schedule_count == total_attempts:
            details = (
                f"Tüm {total_attempts} denemede hiçbir sınav yerleştirilemedi.\n\n"
                "🔍 Olası Nedenler:\n"
                "  • Tüm dersler çakışma grafında birbirine bağlı olabilir\n"
                "  • Günlük limitler çok kısıtlayıcı olabilir\n"
                "  • Öğrenci sınavları arası bekleme süresi uygulanamıyor olabilir\n"
                "  • Derslik kapasitesi her slot için yetersiz olabilir"
            )
            suggestions = [
                "📅 Tarih aralığını genişletin (örn: +3-5 gün)",
                "⚙️ Günlük limit (sınıf) ve Günlük limit (öğrenci) değerlerini artırın",
                "⏰ Bekleme süresini azaltın (örn: 15→10 dk)",
                "🏫 Daha fazla derslik ekleyin veya mevcut kapasite artırın",
                "📚 Eğer 'Paralel sınav olmasın' seçiliyse, kaldırın",
                "🔢 Bazı dersleri çıkararak daha küçük bir program deneyin"
            ]
        
        # Pattern 2: Days exhausted frequently
        elif day_exhausted_count > total_attempts * 0.7:
            details = (
                f"{total_attempts} denemeden {day_exhausted_count} tanesinde günler tükendi.\n\n"
                "🔍 Sorun:\n"
                f"  • {len(unscheduled_courses)} ders yerleştirilemedi\n"
                "  • Seçilen tarih aralığı ve günlük sınav sayısı yetersiz\n"
                "  • Öğle arası ve zaman kısıtlamaları çok fazla slot kaybettiriyor"
            )
            suggestions = [
                f"📅 Tarih aralığını EN AZ {len(unscheduled_courses) // 3 + 2} gün daha uzatın",
                "⏰ Günlük ilk sınav saatini erkene alın (örn: 09:00)",
                "⏰ Günlük son sınav saatini ileri alın (örn: 20:00)",
                "🍽️ Öğle arası süresini kısaltın",
                "📚 Uzun süreli sınavları kısaltın veya standart 75 dk yapın",
                "✅ Cumartesi veya Pazar günlerini etkinleştirin"
            ]
        
        # Pattern 3: Capacity issues
        elif capacity_errors:
            details = (
                f"Derslik kapasitesi sorunu tespit edildi.\n\n"
                "🔍 Sorun:\n"
                f"  • {len(capacity_errors)} denemede kapasite hatası\n"
                "  • Bazı dersler için tüm dersliklerin toplam kapasitesi yetersiz\n"
                "  • Sıra yapısı (boşluklu oturma) nedeniyle efektif kapasite düşük"
            )
            # Show first capacity error as example
            if capacity_errors:
                details += f"\n📋 Örnek Hata:\n{capacity_errors[0][:200]}"
            
            suggestions = [
                "🏫 Yeni derslik ekleyin veya mevcut dersliklerin kapasitesini artırın",
                "👥 Sıra yapısını değiştirin (4'lü yerine 2'li veya 3'lü)",
                "📊 Büyük dersleri birden fazla gruba bölün",
                "🔄 Eğer 'Paralel sınav olmasın' kapalıysa, aynı anda birden fazla sınav olabilir",
                "📅 Tarih aralığını artırarak sınavların daha az yoğun günlere dağılmasını sağlayın"
            ]
        
        # Pattern 4: Conflict issues
        elif conflict_errors:
            details = (
                "Öğrenci çakışmaları çözülemedi.\n\n"
                "🔍 Sorun:\n"
                "  • Ortak öğrencisi olan dersler aynı zamana denk geliyor\n"
                "  • Çakışma grafiği çok karmaşık"
            )
            suggestions = [
                "📅 Daha fazla gün ekleyin ki dersler farklı saatlere yerleşsin",
                "⚙️ Günlük limitler zaten çakışmaları azaltıyor, değerleri kontrol edin",
                "👥 Derslerin öğrenci kayıtlarını kontrol edin (fazla ortak öğrenci?)"
            ]
        
        # Pattern 5: Mixed issues
        else:
            unscheduled_count = len(unscheduled_courses)
            details = (
                f"{total_attempts} deneme yapıldı, hiçbiri tüm dersleri yerleştiremedi.\n\n"
                "🔍 Karışık sorunlar:\n"
            )
            if unscheduled_count > 0:
                details += f"  • {unscheduled_count} ders yerleştirilemedi\n"
            details += (
                "  • Günler, kapasite ve kısıtlar birlikte yeterli değil\n"
                "  • Bazı dersler hiçbir slota uymuyor"
            )
            suggestions = [
                "📅 Tarih aralığını genişletin (öncelik: +5 gün)",
                "🏫 Derslik sayısını veya kapasiteyi artırın",
                "⚙️ Günlük limitleri esnetin (sınıf: 3→4, öğrenci: 3→4)",
                "⏰ Bekleme süresini azaltın (15→10 dk)",
                "📚 Sınav sürelerini kısaltın (uzun sınavlar → 75 dk)",
                "🔄 'Paralel sınav olmasın' seçeneğini kapatın"
            ]
        
        return {
            'message': message,
            'details': details,
            'suggestions': suggestions
        }