
# Set up flask configuration, store global variables

# Import packages

from flask import Flask
app = Flask(__name__)

# specify upload folder here
app.config['UPLOAD_FOLDER'] = './corpus'

import src.views