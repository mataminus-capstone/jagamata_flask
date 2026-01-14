from flask import request, jsonify, current_app
from services.chatbot_service import chatbot

class ChatbotController:
    
    @staticmethod
    def chat():
        """Send message to chatbot"""
        try:
            data = request.get_json(force=True, silent=True)
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON format'
                }), 400
            
            message = data.get('message', '').strip()
            
            if not message:
                return jsonify({
                    'success': False,
                    'message': 'Pesan tidak boleh kosong.',
                    'data': {
                        'response': 'Pesan tidak boleh kosong.',
                        'doctor': 'System',
                        'confidence': 0
                    }
                }), 400
            
            # Get chatbot response
            result = chatbot.predict(message)
            
            if 'error' in result:
                return jsonify({
                    'success': False,
                    'message': 'Gagal memproses pesan.',
                    'data': {
                        'response': result.get('response', 'Terjadi kesalahan saat memproses pesan.'),
                        'doctor': 'System',
                        'confidence': 0
                    }
                }), 500
            
            return jsonify({
                'success': True,
                'message': 'Berhasil mendapatkan respons.',
                'data': {
                    'response': result.get('response', ''),
                    'doctor': result.get('doctor', 'ChatBot AI'),
                    'confidence': result.get('confidence', 0)
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Chatbot error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat memproses pesan.',
                'data': {
                    'response': 'Terjadi kesalahan saat memproses pesan.',
                    'doctor': 'System',
                    'confidence': 0
                }
            }), 500
    
    @staticmethod
    def status():
        """Get chatbot status"""
        try:
            return jsonify({
                'success': True,
                'data': {
                    'status': 'ready' if chatbot.is_loaded else 'not_loaded',
                    'message': 'Chatbot siap digunakan' if chatbot.is_loaded else 'Model belum dimuat',
                    'model_loaded': chatbot.is_loaded,
                    'gemini_configured': chatbot.gemini_configured
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Chatbot status error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Gagal mendapatkan status chatbot.'
            }), 500
    
    @staticmethod
    def get_history():
        """Get chat history (requires auth)"""
        return jsonify({
            'success': False,
            'message': 'Not implemented yet. Requires authentication.'
        }), 501
