from flask import request, jsonify, current_app
from models import db, Clinic, User
from services.jwt_service import JWTService
from services.cloudinary_service import CloudinaryService

class ClinicController:
    @staticmethod
    def create_clinic():
        try:
            token = JWTService.extract_token_from_headers(request.headers)
            if not token:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 401
            
            # Ideally check for admin role here
            
            if 'image' not in request.files:
                 return jsonify({'success': False, 'message': 'Image is required'}), 400
                 
            file = request.files['image']
            if file.filename == '':
                return jsonify({'success': False, 'message': 'No selected file'}), 400
            
            name = request.form.get('name')
            address = request.form.get('address')
            phone_number = request.form.get('phone_number')
            
            if not name or not address or not phone_number:
                return jsonify({'success': False, 'message': 'All fields (name, address, phone_number) are required'}), 400
                
            upload_result = CloudinaryService.upload_image(file)
            if not upload_result['success']:
                return jsonify({'success': False, 'message': upload_result['message']}), 500
                
            image_url = upload_result['url']
            
            clinic = Clinic(
                name=name,
                address=address,
                phone_number=phone_number,
                image_url=image_url
            )
            
            db.session.add(clinic)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Clinic created successfully',
                'data': {
                    'id': clinic.id,
                    'name': clinic.name,
                    'image_url': clinic.image_url
                }
            }), 201
            
        except Exception as e:
            current_app.logger.error(f"Create clinic error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_clinics():
        try:
            token = JWTService.extract_token_from_headers(request.headers)
            if not token:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 401
                
            payload = JWTService.verify_token(token)
            if not payload:
                return jsonify({'success': False, 'message': 'Invalid token'}), 401
                
            user_id = payload.get('user_id')
            user = User.query.get(user_id)
            
            clinics = []
            if user and user.address:
                # Rule based: Try to find clinics in the same area (partial match)
                search = f"%{user.address}%"
                clinics = Clinic.query.filter(Clinic.address.ilike(search)).all()
            
            # If no clinics found by address (or no address), return all (or handles empty case)
            if not clinics:
                 clinics = Clinic.query.all()
            
            data = [{
                'id': c.id,
                'name': c.name,
                'address': c.address,
                'phone_number': c.phone_number,
                'image_url': c.image_url,
                'created_at': c.created_at.isoformat()
            } for c in clinics]
            
            return jsonify({
                'success': True,
                'data': data
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Get clinics error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
