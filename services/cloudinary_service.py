import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app
import os

class CloudinaryService:
    @staticmethod
    def configure():
        if not cloudinary.config().cloud_name:
            cloudinary.config(
                cloud_name = current_app.config.get('CLOUDINARY_CLOUD_NAME'),
                api_key = current_app.config.get('CLOUDINARY_API_KEY'),
                api_secret = current_app.config.get('CLOUDINARY_API_SECRET')
            )
        
    @staticmethod
    def upload_image(file_or_path):
        """
        Upload image to Cloudinary
        Args:
            file_or_path: File object or path to file
        Returns:
            dict: {success, url, public_id, message}
        """
        try:
            CloudinaryService.configure()
            upload_result = cloudinary.uploader.upload(file_or_path)
            return {
                'success': True,
                'url': upload_result.get('secure_url'),
                'public_id': upload_result.get('public_id')
            }
        except Exception as e:
            current_app.logger.error(f"Cloudinary upload error: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
