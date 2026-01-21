from flask import request, jsonify, current_app
from models import db, Feedback, User
from services.sentiment_service import SentimentService
from services.jwt_service import JWTService

class FeedbackController:
    
    @staticmethod
    def _get_current_user_id():
        """Helper: Extract user_id from JWT token or Flask-Login session"""
        # 1. Try JWT from Headers
        token = JWTService.extract_token_from_headers(request.headers)
        if token:
            payload = JWTService.verify_token(token)
            if payload:
                return payload.get('user_id')
        
        # 2. Try Flask-Login Session
        from flask_login import current_user
        if current_user.is_authenticated:
            return current_user.id
            
        return None

    @staticmethod
    def create_feedback():
        """Create new feedback and analyze sentiment"""
        current_user_id = FeedbackController._get_current_user_id()
        if not current_user_id:
             return jsonify({
                'success': False,
                'message': 'Unauthorized: You must be logged in to submit feedback.'
            }), 401
            
        try:
            # Get content from JSON or Form
            content = None
            if request.is_json:
                data = request.get_json()
                content = data.get('content')
            else:
                content = request.form.get('content')

            if not content:
                return jsonify({
                    'success': False,
                    'message': 'Content (feedback) is required!'
                }), 400

            # Analyze sentiment
            label, score = SentimentService.analyze(content)

            # Save to DB
            feedback = Feedback(
                user_id=current_user_id,
                content=content,
                sentiment_label=label,
                sentiment_score=score
            )
            
            db.session.add(feedback)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Feedback berhasil dikirim! Terima kasih.',
                'data': {
                    'id': feedback.id,
                    'content': feedback.content,
                    'created_at': feedback.created_at.isoformat()
                }
            }), 201

        except Exception as e:
            current_app.logger.error(f"Create feedback error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An error occurred while processing feedback.'
            }), 500

    @staticmethod
    def get_feedbacks():
        """Get all feedbacks (could be admin only, but public for now for testing)"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            feedbacks_paginated = Feedback.query.order_by(Feedback.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            feedbacks_data = [{
                'id': f.id,
                'user_id': f.user_id,
                'user_name': f.user.username if f.user else 'Unknown', 
                'content': f.content,
                'sentiment_label': f.sentiment_label,
                'sentiment_score': f.sentiment_score,
                'created_at': f.created_at.isoformat()
            } for f in feedbacks_paginated.items]
            
            return jsonify({
                'success': True,
                'data': {
                    'feedbacks': feedbacks_data,
                    'pagination': {
                        'page': feedbacks_paginated.page,
                        'per_page': feedbacks_paginated.per_page,
                        'total': feedbacks_paginated.total,
                        'pages': feedbacks_paginated.pages
                    }
                }
            }), 200
        except Exception as e:
             current_app.logger.error(f"Get feedbacks error: {str(e)}")
             return jsonify({
                'success': False,
                'message': 'Error retrieving feedbacks'
            }), 500

    @staticmethod
    def get_sentiment_stats():
        """Get statistics for sentiment analysis"""
        try:
            total = Feedback.query.count()
            positive = Feedback.query.filter_by(sentiment_label='POSITIVE').count()
            negative = Feedback.query.filter_by(sentiment_label='NEGATIVE').count()
            
            return {
                'total': total,
                'positive': positive,
                'negative': negative
            }
        except Exception as e:
            current_app.logger.error(f"Get sentiment stats error: {str(e)}")
            return {'total': 0, 'positive': 0, 'negative': 0}

