from flask import Blueprint, jsonify
from services.auth_service import token_required
from models import Category

category_bp = Blueprint('category', __name__, url_prefix='/api/categories')

@category_bp.route('', methods=['GET'])
@token_required
def get_categories(current_user):
    try:
        categories = Category.query.order_by(Category.name.asc()).all()
        
        categories_list = []
        for category in categories:
            categories_list.append({
                'id': category.id,
                'name': category.name,
                'created_at': category.created_at.isoformat()
            })
            
        return jsonify({
            'success': True,
            'data': categories_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': str(e)
        }), 500
