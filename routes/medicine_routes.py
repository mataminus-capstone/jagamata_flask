from flask import Blueprint, request, jsonify
from services.auth_service import token_required
from models import Medicine, Category

medicine_bp = Blueprint('medicine', __name__, url_prefix='/api/medicines')

@medicine_bp.route('', methods=['GET'])
@token_required
def get_medicines(current_user):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category_name = request.args.get('category')
        
        query = Medicine.query
        
        if category_name:
            category = Category.query.filter_by(name=category_name).first()
            if category:
                query = query.filter_by(category_id=category.id)
            else:
                return jsonify({
                    'success': True,
                    'data': [],
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total_pages': 0,
                        'total_items': 0
                    }
                })
        
        paginated_medicines = query.order_by(Medicine.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        medicines_list = []
        for medicine in paginated_medicines.items:
            medicines_list.append({
                'id': medicine.id,
                'name': medicine.name,
                'description': medicine.description,
                'price': medicine.price,
                'image_url': medicine.image_url,
                'category': medicine.category.name if medicine.category else None,
                'created_at': medicine.created_at.isoformat()
            })
            
        return jsonify({
            'success': True,
            'data': medicines_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginated_medicines.pages,
                'total_items': paginated_medicines.total
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': str(e)
        }), 500

@medicine_bp.route('/<int:id>', methods=['GET'])
@token_required
def get_medicine_detail(current_user, id):
    try:
        medicine = Medicine.query.get_or_404(id)
        
        return jsonify({
            'success': True,
            'data': {
                'id': medicine.id,
                'name': medicine.name,
                'description': medicine.description,
                'price': medicine.price,
                'image_url': medicine.image_url,
                'category': medicine.category.name if medicine.category else None,
                'created_at': medicine.created_at.isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': str(e)
        }), 500
