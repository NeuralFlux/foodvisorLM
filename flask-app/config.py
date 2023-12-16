import os

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = False

# Secret key for session management. You can generate random strings here:
# https://randomkeygen.com/
SECRET_KEY = 'Jr?(8an21{_-_.I_=]]]B{=kh-H,ZhJ&Op">N~&ta{qrPt*n1*>(v8r*xe;{zAX'

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
