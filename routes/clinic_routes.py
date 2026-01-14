from flask import Blueprint
from controllers.clinic_controller import ClinicController

clinic_bp = Blueprint('clinic_bp', __name__)

clinic_bp.route('/', methods=['GET'])(ClinicController.get_clinics)
clinic_bp.route('/', methods=['POST'])(ClinicController.create_clinic)
