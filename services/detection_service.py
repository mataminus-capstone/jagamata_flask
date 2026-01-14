from gradio_client import Client, handle_file
from flask import current_app
import os

class DetectionService:
    _client = None
    
    DISEASE_INFO = {
        "Uveitis": {
            "handling": "Kondisi Serius: Segera temui dokter mata. Penundaan bisa berisiko pada penglihatan.\n\nObat Umum (Hanya dengan Resep Dokter):\n- Tetes Mata Steroid: Prednisolone acetate, Dexamethasone (untuk meredakan radang).\n- Tetes Pelebar Pupil: Atropine, Cyclopentolate (untuk mengurangi nyeri dan mencegah komplikasi).\n- Obat Oral: Steroid atau antibiotik/antivirus jika ada infeksi penyerta.",
            "solution": "Langkah yang Harus Dilakukan:\n1. Jangan membeli obat tetes mata sembarangan tanpa rekomendasi dokter.\n2. Gunakan kacamata hitam jika mata sensitif terhadap cahaya.\n3. Istirahatkan mata dan hindari aktivitas berat selama masa pemulihan.\n4. Lakukan kontrol rutin sesuai jadwal dokter."
        },
        "Konjungtivitis": {
            "handling": "Penyebab bisa karena virus, bakteri, atau alergi. Penanganan berbeda untuk setiap jenisnya.\n\nObat Berdasarkan Jenis:\n- Virus: Biasanya sembuh sendiri. Gunakan tetes mata lubrikan atau air mata buatan dan kompres dingin.\n- Bakteri: Memerlukan tetes mata antibiotik (Contoh: Chloramphenicol, Tobramycin).\n- Alergi: Tetes mata antihistamin (Contoh: Olopatadine, Ketotifen).",
            "solution": "Pencegahan dan Perawatan Rumah:\n1. Jangan mengucek mata karena bisa memperparah iritasi.\n2. Sering cuci tangan dengan sabun.\n3. Gunakan kompres dingin untuk meredakan bengkak dan gatal.\n4. Ganti sarung bantal dan handuk setiap hari untuk mencegah penularan."
        },
        "Eyelid disease": {
            "handling": "Gangguan kelopak mata seperti bintitan (Hordeolum), kalazion, atau radang tepi kelopak (Blefaritis).\n\nPenanganan Awal:\n- Kompres Hangat: Tempelkan kain hangat pada kelopak mata selama 10-15 menit, 3-4 kali sehari.\n- Kebersihan: Bersihkan tepi kelopak mata dengan sampo bayi yang diencerkan.\n- Salep Antibiotik: Seperti Erythromycin atau Chloramphenicol, mungkin diperlukan jika ada infeksi bakteri.",
            "solution": "Segera ke Dokter Jika:\n- Benjolan tidak mengecil dalam 2 minggu.\n- Nyeri sangat hebat atau kelopak mata bengkak parah hingga mata sulit dibuka.\n- Gangguan penglihatan terjadi.\n- Benjolan berdarah atau bernanah terus menerus."
        },
        "Katarak": {
            "handling": "Lensa mata keruh yang mengganggu penglihatan. Tidak ada obat tetes yang bisa menghilangkan katarak sepenuhnya.\n\nTindakan Medis:\n- Operasi Katarak adalah satu-satunya cara efektif untuk mengembalikan penglihatan jernih. Prosedur ini cepat dan memiliki tingkat keberhasilan tinggi.\n- Obat Pasca Operasi: Dokter akan meresepkan tetes antibiotik dan anti-radang untuk pemulihan.",
            "solution": "Saran dan Gaya Hidup:\n1. Jika katarak masih tipis dan belum mengganggu, kacamata baru mungkin membantu sementara.\n2. Gunakan kacamata hitam dengan perlindungan UV saat di luar ruangan untuk memperlambat progresivitas.\n3. Perbanyak konsumsi makanan kaya antioksidan (buah dan sayur).\n4. Kontrol rutin untuk memantau ketebalan katarak."
        },
        "Mata Normal": {
            "handling": "Kabar Baik. Mata Anda terdeteksi dalam kondisi sehat dan tidak menunjukkan gejala penyakit mata yang signifikan.",
            "solution": "Tips Menjaga Kesehatan Mata:\n1. Aturan 20-20-20: Setiap 20 menit menatap layar, istirahatkan mata selama 20 detik dengan melihat objek sejauh 20 kaki (6 meter).\n2. Gunakan pencahayaan yang cukup saat membaca atau bekerja.\n3. Makan makanan bervitamin A (wortel, bayam, telur).\n4. Lakukan pemeriksaan mata rutin minimal 1-2 tahun sekali."
        }
    }


    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = Client("iqbaals/jagamata_api")
        return cls._client

    @classmethod
    def predict(cls, image_url):
        try:
            client = cls.get_client()
            # The API accepts url or path. Since we have image_url from Cloudinary, we can pass it.
            # Usually handle_file can take a URL.
            result = client.predict(
                img=handle_file(image_url),
                api_name="/predict_image"
            )
            
            # Result format from user: dict(label: str, confidences: list)
            # Example result print might be needed to debug, but let's assume standard Gradio Label output.
            # If standard Gradio Label output, it might directly return the label string or a dict.
            # The user description says "Returns 1 element dict(label: ..., confidences: ...)"
            
            label = result.get('label')
            confidences = result.get('confidences', [])
            
            # Find the confidence for the predicted label
            confidence = 0.0
            for conf in confidences:
                if conf.get('label') == label:
                    confidence = conf.get('confidence')
                    break
            
            # Normalize label (Capitalize etc)
            normalized_label = label
            # Map common variations if needed, e.g. "katarak" -> "Katarak"
            if normalized_label.lower() == "katarak":
                normalized_label = "Katarak"
            elif normalized_label.lower() == "normal":
                normalized_label = "Mata Normal"
                
            info = cls.DISEASE_INFO.get(normalized_label, {
                "handling": "Konsultasikan dengan dokter untuk diagnosis lebih lanjut.",
                "solution": "Segera periksa ke dokter mata terdekat."
            })
            
            return {
                "success": True,
                "label": normalized_label,
                "confidence": confidence,
                "handling": info["handling"],
                "solution": info["solution"]
            }
            
        except Exception as e:
            current_app.logger.error(f"Prediction error: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }

detection_service = DetectionService()
