from gradio_client import Client
import logging
import os

class SentimentService:
    _client = None
    # URL Space Anda yang sudah berjalan
    _space_url = "ahmatfauzy/sentiment-analysis"

    @classmethod
    def get_client(cls):
        if cls._client is None:
            try:
                # Initialize client connected to the HF Space
                print(f"Connecting to Sentiment Analysis API at {cls._space_url}...")
                cls._client = Client(cls._space_url)
                print("Connected to Sentiment Analysis API successfully.")
            except Exception as e:
                logging.error(f"Error connecting to sentiment API: {e}")
                return None
        return cls._client

    @staticmethod
    def analyze(text):
        client = SentimentService.get_client()
        if not client:
            logging.warning("Sentiment API client not available. Skipping analysis.")
            return None, 0.0
            
        try:
            # Predict using the API
            result = client.predict(
                text=text,
                api_name="/analyze_sentiment"
            )
            
            # Result dari Gradio JSON output biasanya langsung berupa dict
            if result:
                # Jika result berupa path/file (kadang terjadi), perlu dibaca, tapi karena output JSON component
                # gradion_client biasanya me-return native python dict/list.
                if isinstance(result, dict):
                    label = result.get('label')
                    
                    # Map labels
                    if label == 'LABEL_1':
                        label = 'POSITIVE'
                    elif label == 'LABEL_0':
                        label = 'NEGATIVE'
                        
                    score = result.get('score')
                    return label, float(score) if score else 0.0
                else:
                    logging.warning(f"Unexpected result format: {result}")
                    return None, 0.0
                
        except Exception as e:
            logging.error(f"Error during sentiment API call: {e}")
        
        return None, 0.0
