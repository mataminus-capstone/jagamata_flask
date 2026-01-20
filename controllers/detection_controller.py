from flask import request, jsonify
from models import db, DetectionHistory
from services.detection_service import detection_service
from services.cloudinary_service import CloudinaryService

class DetectionController:
    @staticmethod
    def detect_disease(current_user):
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No image provided'}), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'}), 400
            
        try:
            # 1. Upload to Cloudinary
            upload_result = CloudinaryService.upload_image(file)
            if not upload_result['success']:
                return jsonify({'success': False, 'message': upload_result.get('message', 'Upload failed')}), 500
                
            image_url = upload_result['url']
            
            # 2. Predict
            prediction = detection_service.predict(image_url)
            
            if not prediction['success']:
                return jsonify({'success': False, 'message': prediction.get('message', 'Prediction failed')}), 500
                
            # 3. Save to History
            history = DetectionHistory(
                user_id=current_user.id,
                image_url=image_url,
                diagnosis=prediction['label'],
                confidence=float(prediction.get('confidence', 0.0))
            )
            db.session.add(history)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'data': {
                    'id': history.id,
                    'image_url': image_url,
                    'diagnosis': prediction['label'],
                    'confidence': prediction['confidence'],
                    'handling': prediction['handling'],
                    'solution': prediction['solution'],
                    'created_at': history.created_at.isoformat()
                }
            }), 200
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_history(current_user):
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            history_query = DetectionHistory.query.filter_by(user_id=current_user.id).order_by(DetectionHistory.created_at.desc())
            
            pagination = history_query.paginate(page=page, per_page=per_page, error_out=False)
            
            history_items = []
            for item in pagination.items:
                # Re-fetch info to ensure we send the text even if we didn't store it
                # (Or we could store it to be safe, but for now we map dynamically)
                info = detection_service.DISEASE_INFO.get(item.diagnosis, {
                    "handling": "Konsultasikan dengan dokter.",
                    "solution": ""
                })
                
                history_items.append({
                    'id': item.id,
                    'image_url': item.image_url,
                    'diagnosis': item.diagnosis,
                    'confidence': item.confidence,
                    'created_at': item.created_at.isoformat(),
                    'handling': info['handling'],
                    'solution': info['solution']
                })
                
            return jsonify({
                'success': True,
                'data': history_items,
                'pagination': {
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'current_page': pagination.page,
                    'per_page': pagination.per_page
                }
            }), 200
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
