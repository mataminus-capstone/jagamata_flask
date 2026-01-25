from flask import Blueprint
from controllers.drowsiness_controller import drowsiness_controller
from services.auth_service import token_required

drowsiness_bp = Blueprint('drowsiness_bp', __name__)

@drowsiness_bp.route('/api/predict-drowsiness', methods=['POST'])
@token_required
def predict(current_user):
    return drowsiness_controller.predict(current_user)

@drowsiness_bp.route('/api/drowsiness-history', methods=['GET'])
@token_required
def get_history(current_user):
    return drowsiness_controller.get_history(current_user)
