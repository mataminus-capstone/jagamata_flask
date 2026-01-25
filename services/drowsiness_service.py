import os
from gradio_client import Client, handle_file
from flask import current_app

class DrowsinessService:
    def __init__(self):
        # Initialize client lazily or here if appropriate
        self.client = None

    def _get_client(self):
        if not self.client:
            self.client = Client("iqbaals/drowiness_model")
        return self.client

    def predict(self, image_url):
        try:
            client = self._get_client()
            result = client.predict(
                image=handle_file(image_url),
                api_name="/predict_drowsiness"
            )
            # Result is a tuple: 
            # [0] dict(label: str, confidences: list)
            # [1] float (confidence of prediction)
            
            return {
                'success': True,
                'data': {
                    'label': result[0]['label'],
                    'confidence': result[1], # Main confidence
                    'details': result[0] 
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

drowsiness_service = DrowsinessService()
