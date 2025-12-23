from flask import request, jsonify, current_app
from models import db, User
from datetime import datetime

class UserController:
    
    @staticmethod
    def get_all_users():
        """Get all users with pagination"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            users_pagination = User.query.paginate(page=page, per_page=per_page)
            
            users = [{
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'email_verified': user.email_verified,
                'oauth_provider': user.oauth_provider,
                'created_at': user.created_at.isoformat()
            } for user in users_pagination.items]
            
            return jsonify({
                'success': True,
                'data': {
                    'users': users,
                    'total': users_pagination.total,
                    'pages': users_pagination.pages,
                    'current_page': page
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Get users error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat mengambil data pengguna.'
            }), 500
    
    @staticmethod
    def get_user(user_id):
        """Get single user by ID"""
        try:
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'Pengguna tidak ditemukan.'
                }), 404
            
            return jsonify({
                'success': True,
                'data': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'email_verified': user.email_verified,
                    'oauth_provider': user.oauth_provider,
                    'created_at': user.created_at.isoformat()
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Get user error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat mengambil data pengguna.'
            }), 500
    
    @staticmethod
    def update_user_role(user_id):
        """Update user role"""
        try:
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'Pengguna tidak ditemukan.'
                }), 404
            
            data = request.get_json(force=True, silent=True)
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON format'
                }), 400
            
            role = data.get('role', '').strip()
            
            if role not in ['user', 'moderator', 'admin']:
                return jsonify({
                    'success': False,
                    'message': 'Role tidak valid. Gunakan: user, moderator, atau admin'
                }), 400
            
            old_role = user.role
            user.role = role
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Role berhasil diubah dari {old_role} menjadi {role}',
                'data': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Update user role error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat mengubah role.'
            }), 500
    
    @staticmethod
    def delete_user(user_id):
        """Delete user"""
        try:
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'Pengguna tidak ditemukan.'
                }), 404
            
            username = user.username
            db.session.delete(user)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Pengguna {username} berhasil dihapus.'
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Delete user error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat menghapus pengguna.'
            }), 500
    
    @staticmethod
    def get_user_stats():
        """Get user statistics"""
        try:
            total_users = User.query.count()
            admin_count = User.query.filter_by(role='admin').count()
            moderator_count = User.query.filter_by(role='moderator').count()
            user_count = User.query.filter_by(role='user').count()
            verified_count = User.query.filter_by(email_verified=True).count()
            
            return jsonify({
                'success': True,
                'data': {
                    'total_users': total_users,
                    'admin_count': admin_count,
                    'moderator_count': moderator_count,
                    'user_count': user_count,
                    'verified_count': verified_count,
                    'unverified_count': total_users - verified_count
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Get user stats error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat mengambil statistik.'
            }), 500
