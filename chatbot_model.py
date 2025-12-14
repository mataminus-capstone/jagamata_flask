import os
import pickle
import numpy as np
import pandas as pd
import re
import google.generativeai as genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import current_app

class ChatbotModel:
    def __init__(self, app=None):
        self.is_loaded = False
        self.dataset_df = None
        self.vectorizer = None
        self.tfidf_matrix = None
        self.gemini_configured = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Load semantic search model from PKL files and configure Gemini"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            models_dir = os.path.join(base_dir, 'models')
            
            app.logger.info("Loading semantic search model...")
            
            # Load dataset.pkl
            dataset_path = os.path.join(models_dir, 'dataset.pkl')
            if not os.path.exists(dataset_path):
                raise FileNotFoundError(f"File tidak ditemukan: {dataset_path}")
            self.dataset_df = pd.read_pickle(dataset_path)
            app.logger.info(f"✓ Dataset: {len(self.dataset_df)} rows")
            
            # Load vectorizer.pkl
            vectorizer_path = os.path.join(models_dir, 'vectorizer.pkl')
            with open(vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            app.logger.info("✓ Vectorizer loaded")
            
            # Load tfidf_matrix.pkl
            tfidf_path = os.path.join(models_dir, 'tfidf_matrix.pkl')
            with open(tfidf_path, 'rb') as f:
                self.tfidf_matrix = pickle.load(f)
            app.logger.info("✓ TF-IDF matrix loaded")
            
            gemini_api_key = os.getenv('GEMINI_API_KEY')
            if gemini_api_key:
                genai.configure(api_key=gemini_api_key)
                self.gemini_configured = True
                app.logger.info("✓ Gemini API configured")
            else:
                app.logger.warning("⚠ Gemini API key tidak ditemukan, generate response akan dilewati")
            
            self.is_loaded = True
            app.logger.info("✅ Semantic search ready!")
            
        except Exception as e:
            app.logger.error(f"✗ Error: {str(e)}")
            import traceback
            app.logger.error(traceback.format_exc())
            self.is_loaded = False
    
    def clean_text(self, text):
        if pd.isna(text):
            return ""
        text = str(text).lower()
        text = re.sub(r'http\S+|www\S+', '', text)
        text = re.sub(r'[^a-z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def generate_with_gemini(self, user_message, semantic_response, doctor_name):
        try:
            if not self.gemini_configured:
                current_app.logger.warning("Gemini not configured, returning semantic response")
                return semantic_response
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""Anda adalah chatbot medis mata yang membantu user. 

anda adalah chatbot untuk aplikasi konsultasi kesehatan mata bernama JagaMata.  
            
User bertanya: "{user_message}"

Berikut adalah jawaban dari {doctor_name}:
"{semantic_response}"

Jika user hanya mengirim sapaan atau pertanyaan umum, balas dengan sopan dan ramah tanpa konteks medis.
Atau jika sudah keluar dari konteks medis mata, katakan "Maaf, saya hanya bisa membantu masalah terkait kesehatan mata."

dan tidak usah tulis nama dokter lagi.
hapus isi jawaban semacam "**Jawaban dari dr.....:** ", dan langsung berikan jawaban yang jelas dan informatif.

Tolong enhance/improve jawaban tersebut dengan:
1. Jelas dan mudah dipahami
2. Tambahkan konteks medis jika diperlukan
3. Berikan saran praktis
4. Gunakan bahasa Indonesia yang baik
5. Jangan terlalu panjang (maksimal 3-4 paragraf)

Generated Response:"""
            
            response = model.generate_content(prompt)
            generated_text = response.text if response.text else semantic_response
            
            current_app.logger.info("✓ Gemini response generated successfully")
            return generated_text
            
        except Exception as e:
            current_app.logger.error(f"Gemini generation error: {str(e)}")
            return semantic_response
    
    def predict(self, text, max_length=128):
        if not self.is_loaded:
            return {
                'error': 'Model not loaded',
                'response': 'Maaf, chatbot belum siap. Silakan coba lagi nanti.'
            }
        
        try:
            # Log input
            current_app.logger.info(f"User: '{text}'")
            
            # Clean input
            cleaned_text = self.clean_text(text)
            
            # Create TF-IDF vector
            input_vector = self.vectorizer.transform([cleaned_text])
            
            # Find most similar question
            similarities = cosine_similarity(input_vector, self.tfidf_matrix)
            best_idx = np.argmax(similarities[0])
            best_score = similarities[0][best_idx]
            
            # Get doctor answer
            doctor_answer = self.dataset_df.iloc[best_idx]['answer_content']
            doctor_name = self.dataset_df.iloc[best_idx]['doctor_name']
            
            current_app.logger.info(f"Semantic match dengan confidence: {best_score:.2f}")
            
            enhanced_response = self.generate_with_gemini(text, doctor_answer, doctor_name)
            
            # Format response
            response = enhanced_response
            
            return {
                'response': response,
                'doctor': doctor_name,
                'confidence': float(best_score),
                'status': 'success'
            }
            
        except Exception as e:
            current_app.logger.error(f"✗ Error: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return {
                'error': str(e),
                'response': 'Maaf, terjadi kesalahan saat memproses pertanyaan Anda.'
            }

# Global instance
chatbot = ChatbotModel()

# Test
if __name__ == "__main__":
    import logging
    from flask import Flask
    
    app = Flask(__name__)
    app.logger.setLevel(logging.INFO)
    
    chatbot.init_app(app)
    
    if chatbot.is_loaded:
        print("✅ TEST BERHASIL: Model siap digunakan")
        print("\nContoh pertanyaan:")
        print("1. mata saya sakit")
        print("2. mata merah bengkak")
        print("3. penglihatan kabur")
        
        # Test
        result = chatbot.predict("mata saya sakit")
        print(f"\n{'='*60}")
        print(f"JAWABAN:\n{result['response']}")
        print(f"{'='*60}")
    else:
        print("❌ TEST GAGAL: Model tidak bisa diload")