from flask import Blueprint, request, jsonify
from controllers.chatbot_controller import ChatbotController

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')


@chatbot_bp.route('/', methods=['POST'])
def chat():
    """Send message to chatbot"""
    return ChatbotController.chat()

@chatbot_bp.route('/status', methods=['GET'])
def status():
    """Get chatbot status"""
    return ChatbotController.status()

@chatbot_bp.route('/history', methods=['GET'])
def history():
    """Get chat history (requires auth)"""
    return ChatbotController.get_history()
