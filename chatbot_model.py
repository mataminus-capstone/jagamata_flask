import os
import pickle
import numpy as np
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import current_app

class ChatbotModel:
    def __init__(self, app=None):
        self.is_loaded = False
        self.dataset_df = None
        self.vectorizer = None
        self.tfidf_matrix = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Load semantic search model from PKL files"""
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
            
            self.is_loaded = True
            app.logger.info("✅ Semantic search ready!")
            
        except Exception as e:
            app.logger.error(f"✗ Error: {str(e)}")
            import traceback
            app.logger.error(traceback.format_exc())
            self.is_loaded = False
    
    def clean_text(self, text):
        """Clean text for matching"""
        if pd.isna(text):
            return ""
        text = str(text).lower()
        text = re.sub(r'http\S+|www\S+', '', text)
        text = re.sub(r'[^a-z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def predict(self, text, max_length=128):
        """Find most similar question and return doctor's answer"""
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
            
            # Format response
            response = f"**Jawaban dari {doctor_name}:**\n\n{doctor_answer}"
            
            current_app.logger.info(f"Match dengan confidence: {best_score:.2f}")
            
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