# import pickle
# import numpy as np
# from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
# import tensorflow as tf
# import os

# class ChatbotService:
#     def __init__(self):
#         """Load semua model saat inisialisasi"""
#         self.model = None
#         self.tokenizer = None
#         self.label_encoder = None
#         self.config = None
#         self.load_models()
    
#     def load_models(self):
#         """Load model dari folder models/"""
#         try:
#             print("Loading chatbot models...")
            
#             # Load label encoder
#             with open('models/label_encoder.pkl', 'rb') as f:
#                 self.label_encoder = pickle.load(f)
            
#             # Load config
#             with open('models/config.pkl', 'rb') as f:
#                 self.config = pickle.load(f)
            
#             # Load tokenizer dan model IndoBERT
#             model_path = 'models/transformer_model'
#             self.tokenizer = AutoTokenizer.from_pretrained(model_path)
#             self.model = TFAutoModelForSequenceClassification.from_pretrained(model_path)
            
#             print("✅ Chatbot models loaded successfully!")
            
#         except Exception as e:
#             print(f"❌ Error loading models: {str(e)}")
#             print("Pastikan folder 'models/' ada di root proyek")
    
#     def predict_intent(self, message):
#         """Prediksi intent dari pesan user"""
#         if not self.model or not self.tokenizer:
#             return "default", "Maaf, chatbot belum siap. Silakan coba lagi nanti."
        
#         try:
#             # Tokenize input
#             inputs = self.tokenizer(
#                 message,
#                 padding=True,
#                 truncation=True,
#                 max_length=128,
#                 return_tensors="tf"
#             )
            
#             # Predict
#             predictions = self.model.predict(inputs['input_ids'], verbose=0)
#             predicted_class = np.argmax(predictions.logits, axis=1)[0]
            
#             # Decode label
#             intent = self.label_encoder.inverse_transform([predicted_class])[0]
            
#             # Get confidence score
#             confidence = tf.nn.softmax(predictions.logits[0])[predicted_class].numpy()
            
#             return intent, confidence
            
#         except Exception as e:
#             print(f"Prediction error: {str(e)}")
#             return "default", 0.0
    
#     def get_response(self, intent, confidence=0.5):
#         """Generate response berdasarkan intent dan confidence"""
#         # Response mapping (sesuaikan dengan intent Anda)
#         responses = {
#             'short': "Terima kasih atas pertanyaan Anda. Untuk jawaban lebih detail, bisa jelaskan gejalanya lebih lengkap?",
#             'medium': "Pertanyaan Anda sudah cukup jelas. Tim medis kami akan merespons segera.",
#             'long': "Terima kasih atas detail pertanyaannya. Sistem kami sudah mencatat dan dokter akan segera membantu.",
#             'penyakit_mata': "Untuk penyakit mata, segera konsultasikan dengan dokter spesialis mata kami.",
#             'gejala': "Gejala yang Anda sebutkan perlu penanganan profesional. Segera lakukan check-up.",
#             'pengobatan': "Informasi pengobatan sudah kami catat. Dokter akan memberikan rekomendasi terbaik.",
#             'default': "Maaf, saya belum mengerti pertanyaan Anda. Tim kami akan segera merespons."
#         }
        
#         # Jika confidence rendah, gunakan default response
#         if confidence < 0.6:
#             return responses['default']
        
#         return responses.get(intent, responses['default'])

# # Buat global instance
# chatbot_service = ChatbotService()