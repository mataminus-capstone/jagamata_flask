import os
import joblib
import numpy as np
import pandas as pd
import re
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity
from flask import current_app

class ChatbotModel:
    def __init__(self, app=None):
        self.is_loaded = False
        self.answers = None
        self.vectorizer = None
        self.tfidf_matrix = None
        self.gemini_configured = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Load semantic search model from PKL files and configure Gemini"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to reach models folder
            models_dir = os.path.join(os.path.dirname(base_dir), 'models', 'alodokter_chatbot')
            
            app.logger.info("Loading semantic search model from alodokter_chatbot...")
            
            # Load answers.pkl
            answers_path = os.path.join(models_dir, 'answers.pkl')
            if not os.path.exists(answers_path):
                raise FileNotFoundError(f"File tidak ditemukan: {answers_path}")
            
            with open(answers_path, 'rb') as f:
                self.answers = joblib.load(f)
            app.logger.info(f"✓ Answers loaded: {len(self.answers)} items")
            
            # Load vectorizer.pkl
            vectorizer_path = os.path.join(models_dir, 'vectorizer.pkl')
            with open(vectorizer_path, 'rb') as f:
                self.vectorizer = joblib.load(f)
            app.logger.info("✓ Vectorizer loaded")
            
            # Load X_matrix.pkl (tfidf_matrix)
            tfidf_path = os.path.join(models_dir, 'X_matrix.pkl')
            with open(tfidf_path, 'rb') as f:
                self.tfidf_matrix = joblib.load(f)
            app.logger.info("✓ TF-IDF matrix loaded")
            
            gemini_api_key = os.getenv('GEMINI_API_KEY')
            if gemini_api_key:
                genai.configure(api_key=gemini_api_key)
                self.gemini_configured = True
                app.logger.info("✓ Gemini API configured")
            else:
                app.logger.warning("⚠ Gemini API key tidak ditemukan, generate response akan dilewati")
            
            self.is_loaded = True
            app.logger.info("✓ Semantic search ready!")
            
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
    
    def generate_with_gemini(self, user_message, semantic_response):
        try:
            if not self.gemini_configured:
                current_app.logger.warning("Gemini not configured, returning semantic response")
                return semantic_response
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""Anda adalah chatbot medis mata yang membantu user. 
            
User bertanya: "{user_message}"

Berikut adalah referensi jawaban medis:
"{semantic_response}"

Instruksi:
1. Gunakan referensi jawaban di atas sebagai dasar, namun sampaikan ulang dengan bahasa yang lebih personal dan ramah.
2. Jika referensi jawaban berisi sapaan formal atau nama dokter, HILANGKAN itu. Langsung ke inti jawaban.
3. Pastikan jawaban mudah dipahami oleh orang awam.
4. Jika pertanyaan user hanya sapaan (halo, hai, selamat pagi), jawab dengan ramah tanpa konteks medis berlebihan.
5. Jika pertanyaan di luar konteks kesehatan (khususnya mata), sampaikan permohonan maaf bahwa Anda hanya fokus pada kesehatan mata.

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
            
            # Get answer
            semantic_answer = self.answers[best_idx]
            
            current_app.logger.info(f"Semantic match dengan confidence: {best_score:.2f}")
            
            enhanced_response = self.generate_with_gemini(text, semantic_answer)
            
            # Format response
            response = enhanced_response
            
            return {
                'response': response,
                'doctor': 'JagaMata AI', # Generic name since specific doctor info is removed
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
