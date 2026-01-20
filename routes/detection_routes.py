from flask import Blueprint
from controllers.detection_controller import DetectionController
from services.auth_service import token_required

detection_bp = Blueprint('detection', __name__, url_prefix='/api/detection')

@detection_bp.route('/predict', methods=['POST'])
@token_required
def predict_disease(current_user):
    return DetectionController.detect_disease(current_user)

@detection_bp.route('/history', methods=['GET'])
@token_required
def get_history(current_user):
    return DetectionController.get_history(current_user)
