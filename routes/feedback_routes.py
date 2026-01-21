from flask import Blueprint, request
from controllers.feedback_controller import FeedbackController

feedback_bp = Blueprint('feedback', __name__, url_prefix='/api/feedback')

@feedback_bp.route('/', methods=['GET', 'POST'])
def handle_feedback():
    """Get feedbacks (GET) or create feedback (POST)"""
    if request.method == 'GET':
        return FeedbackController.get_feedbacks()
    else:
        return FeedbackController.create_feedback()
