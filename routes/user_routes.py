from flask import Blueprint
from controllers.user_controller import UserController

user_bp = Blueprint('api_users', __name__, url_prefix='/api/users')

# API Routes
user_bp.route('', methods=['GET'])(UserController.get_all_users)
user_bp.route('/<int:user_id>', methods=['GET'])(UserController.get_user)
user_bp.route('/<int:user_id>/role', methods=['PUT'])(UserController.update_user_role)
user_bp.route('/<int:user_id>', methods=['DELETE'])(UserController.delete_user)
user_bp.route('/stats', methods=['GET'])(UserController.get_user_stats)
