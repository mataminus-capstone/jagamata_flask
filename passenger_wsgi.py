import os
import sys

# Add the project directory to sys.path so that modules can be imported
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

# Create the application instance
# You can change 'production' to 'development' if you need debug mode,
# but 'production' is recommended for deployment.
application = create_app('production')
