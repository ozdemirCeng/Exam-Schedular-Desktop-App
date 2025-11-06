"""
Oturma Planı Algoritması
Intelligent seating plan generation with spacing optimization
"""

import logging
import random
from typing import Dict, List, Callable, Optional
from models.database import db
from models.ogrenci_model import OgrenciModel
from models.derslik_model import DerslikModel
from models.sinav_model import SinavModel

logger = logging.getLogger(__name__)


class OturmaPlanlama:
    """Seating plan generation algorithm"""
    
    def __init__(self):
        self.ogrenci_model = OgrenciModel(db)
        self.derslik_model = DerslikModel(db)
        self.sinav_model = SinavModel(db)
    
    def generate_seating_plan(
        self,
        sinav_id: int,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict:
        """
        Generate seating plan for an exam across multiple classrooms
        
        Args:
            sinav_id: Exam ID
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with success status and seating plan
        """
        try:
            if progress_callback:
                progress_callback(10, "Sınav bilgileri yükleniyor...")
            
            # Get exam details
            sinav = self.sinav_model.get_sinav_by_id(sinav_id)
            if not sinav:
                raise Exception(f"Sınav bulunamadı: {sinav_id}")
            
            if progress_callback:
                progress_callback(20, "Öğrenciler yükleniyor...")
            
            # Get students enrolled in this course
            ogrenciler = self.ogrenci_model.get_ogrenciler_by_ders(sinav['ders_id'])
            if not ogrenciler:
                raise Exception(f"Bu derse kayıtlı öğrenci bulunamadı: {sinav['ders_kodu']}")
            
            # Shuffle students for randomized seating
            random.shuffle(ogrenciler)
            
            if progress_callback:
                progress_callback(30, "Derslik bilgileri yükleniyor...")
            
            # Get classroom assignments for this exam
            derslikler = self.sinav_model.get_sinav_derslikleri(sinav_id)
            if not derslikler:
                raise Exception(f"Bu sınav için derslik ataması bulunamadı!")
            
            logger.info(f"📊 Sınav: {sinav['ders_kodu']}, {len(ogrenciler)} öğrenci, {len(derslikler)} derslik")
            
            if progress_callback:
                progress_callback(50, "Oturma planı oluşturuluyor...")
            
            # Generate seating plan across all classrooms
            seating_plan = self._generate_multi_classroom_plan(
                ogrenciler, 
                derslikler,
                progress_callback
            )
            
            if progress_callback:
                progress_callback(100, "Tamamlandı!")
            
            logger.info(f"✅ Seating plan generated: {len(seating_plan)} öğrenci yerleştirildi")
            
            # Calculate statistics
            placed_count = len(seating_plan)
            unplaced_count = len(ogrenciler) - placed_count
            
            message = f"✅ {placed_count} öğrenci yerleştirildi"
            if unplaced_count > 0:
                message += f" (⚠️ {unplaced_count} öğrenci yerleştirilemedi - kapasite yetersiz)"
            
            return {
                'success': True,
                'message': message,
                'plan': seating_plan,
                'sinav': sinav,
                'derslikler': derslikler,
                'placed_count': placed_count,
                'unplaced_count': unplaced_count
            }
            
        except Exception as e:
            logger.error(f"Error generating seating plan: {e}", exc_info=True)
            return {
                'success': False,
                'message': f"Hata: {str(e)}",
                'plan': []
            }
    
    def _generate_multi_classroom_plan(
        self,
        students: List[Dict],
        derslikler: List[Dict],
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> List[Dict]:
        """
        Generate seating plan across multiple classrooms with spacing and balanced distribution
        
        Args:
            students: List of students to seat
            derslikler: List of classrooms
            progress_callback: Progress callback
            
        Returns:
            Complete seating plan
        """
        complete_plan = []
        total_students = len(students)
        
        # Sort classrooms by capacity (use largest first for initial sorting)
        sorted_derslikler = sorted(derslikler, key=lambda x: x['kapasite'], reverse=True)
        
        # Calculate available seats for each classroom
        classroom_info = []
        for derslik in sorted_derslikler:
            satir_sayisi = derslik['satir_sayisi']
            sutun_sayisi = derslik['sutun_sayisi']
            sira_yapisi = derslik.get('sira_yapisi', 3)  # 2'li, 3'lü veya 4'lü gruplar
            
            # Sıra yapısına göre oturma düzeni
            available_seats = []
            
            for satir in range(1, satir_sayisi + 1):
                # Her grup için pattern uygula
                for grup_baslangic in range(1, sutun_sayisi + 1, sira_yapisi):
                    # Grup içinde hangi sütunlara oturulacak?
                    if sira_yapisi == 4:
                        # 4'lü grup: dolu-boş-boş-dolu (1. ve 4. sütun)
                        offset_sutunlar = [0, 3]
                    elif sira_yapisi == 3:
                        # 3'lü grup: dolu-boş-dolu (1. ve 3. sütun)
                        offset_sutunlar = [0, 2]
                    elif sira_yapisi == 2:
                        # 2'li grup: boş-dolu (2. sütun, kapı tarafı/sağdan)
                        offset_sutunlar = [1]
                    else:
                        # Genel durum: ilk sütun
                        offset_sutunlar = [0]
                    
                    # Offsetleri uygula
                    for offset in offset_sutunlar:
                        sutun = grup_baslangic + offset
                        if sutun <= sutun_sayisi:  # Sütun sınırını aşma
                            available_seats.append((satir, sutun))
            
            classroom_info.append({
                'derslik': derslik,
                'available_seats': available_seats,
                'capacity': len(available_seats),
                'placed_count': 0,
                'current_seat_index': 0
            })
            
            logger.info(f"  📍 {derslik['derslik_adi']}: {len(available_seats)} koltuk (kapasite: {derslik['kapasite']})")
        
        # DENGELI DAĞILIM: Round-robin yerleştirme
        # Her sınıfa sırayla birer öğrenci yerleştir
        student_index = 0
        classroom_index = 0
        
        while student_index < total_students:
            # Mevcut sınıf bilgisini al
            current_classroom = classroom_info[classroom_index]
            
            # Bu sınıfta boş koltuk var mı kontrol et
            if current_classroom['current_seat_index'] < current_classroom['capacity']:
                student = students[student_index]
                derslik = current_classroom['derslik']
                seat = current_classroom['available_seats'][current_classroom['current_seat_index']]
                satir, sutun = seat
                
                complete_plan.append({
                    'ogrenci_no': student['ogrenci_no'],
                    'ad_soyad': student['ad_soyad'],
                    'derslik_id': derslik['derslik_id'],
                    'derslik_kodu': derslik['derslik_kodu'],
                    'derslik_adi': derslik['derslik_adi'],
                    'satir': satir,
                    'sutun': sutun
                })
                
                current_classroom['placed_count'] += 1
                current_classroom['current_seat_index'] += 1
                student_index += 1
                
                # Progress callback
                if progress_callback and student_index % 10 == 0:
                    percent = 50 + int((student_index / total_students) * 40)
                    progress_callback(percent, f"Yerleştiriliyor: {student_index}/{total_students}")
            
            # Bir sonraki sınıfa geç (round-robin)
            classroom_index = (classroom_index + 1) % len(classroom_info)
            
            # Eğer tüm sınıflar doluysa döngüyü kır
            all_full = all(c['current_seat_index'] >= c['capacity'] for c in classroom_info)
            if all_full and student_index < total_students:
                logger.warning(f"⚠️ Kapasite yetersiz: {total_students - student_index} öğrenci yerleştirilemedi")
                break
        
        # Log final distribution
        for info in classroom_info:
            logger.info(f"  ✅ {info['derslik']['derslik_adi']}: {info['placed_count']}/{info['capacity']} koltuk dolu")
        
        return complete_plan
    
    def validate_seating_plan(self, plan: List[Dict]) -> Dict:
        """Validate seating plan for conflicts"""
        conflicts = []
        
        # Check for duplicate seat assignments
        seat_map = {}
        for assignment in plan:
            key = f"{assignment['derslik_id']}_{assignment['satir']}_{assignment['sutun']}"
            
            if key in seat_map:
                conflicts.append({
                    'type': 'duplicate_seat',
                    'student1': seat_map[key],
                    'student2': assignment['ogrenci_no'],
                    'message': f"Aynı koltuk ({assignment['derslik_adi']} - Sıra:{assignment['satir']}, Sütun:{assignment['sutun']}) iki öğrenciye atanmış"
                })
            else:
                seat_map[key] = assignment['ogrenci_no']
        
        if conflicts:
            return {
                'success': False,
                'conflicts': conflicts,
                'message': f"{len(conflicts)} çakışma bulundu"
            }
        
        return {
            'success': True,
            'message': "Plan geçerli"
        }
