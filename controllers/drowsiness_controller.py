from flask import Blueprint, request, jsonify
from models import db, FatigueHistory
from services.drowsiness_service import drowsiness_service
import cloudinary.uploader

class DrowsinessController:
    def predict(self, current_user):
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No image provided'
            }), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No selected file'
            }), 400

        try:
            # 1. Upload to Cloudinary to get a URL (Gradio client needs URL or path)
            # We use Cloudinary as we are likely doing for other images
            upload_result = cloudinary.uploader.upload(file)
            image_url = upload_result['secure_url']

            # 2. Call Gradio Service
            prediction = drowsiness_service.predict(image_url)

            if not prediction['success']:
                return jsonify({
                    'success': False,
                    'message': prediction['error']
                }), 500

            result_data = prediction['data']
            
            # 3. Save to History (if user is authenticated)
            # With token_required, current_user is passed and is guaranteed to be a user object (or the decorator handles error)
            
            if current_user:
                history = FatigueHistory(
                    user_id=current_user.id,
                    image_url=image_url,
                    label=str(result_data['label']),
                    confidence=float(result_data['confidence'])
                )
                db.session.add(history)
                db.session.commit()

            return jsonify({
                'success': True,
                'data': {
                    'image_url': image_url,
                    'label': result_data['label'],
                    'confidence': result_data['confidence'],
                    'details': result_data['details']
                }
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    def get_history(self, current_user):
        # user is guaranteed to be present by token_required
            
        history = FatigueHistory.query.filter_by(user_id=current_user.id).order_by(FatigueHistory.created_at.desc()).all()
        
        history_list = []
        for h in history:
            history_list.append({
                'id': h.id,
                'image_url': h.image_url,
                'label': h.label,
                'confidence': h.confidence,
                'created_at': h.created_at.isoformat()
            })
            
        return jsonify({
            'success': True,
            'data': history_list
        })

drowsiness_controller = DrowsinessController()
