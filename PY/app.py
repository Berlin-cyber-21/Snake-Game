from flask import Flask, render_template, request, redirect, url_for, flash
import random
import os
from dotenv import load_dotenv
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import redis

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

# Initialize Flask-Talisman for security headers and HTTPS
csp = {
    'default-src': ['\'self\''],
    'script-src': ['\'self\'', 'https://trustedscripts.example.com'],
    'style-src': ['\'self\'', 'https://trustedstyles.example.com'],
}
talisman = Talisman(app, content_security_policy=csp)

# Configure Redis for rate limiting storage
redis_client = redis.StrictRedis(
    host='localhost',
    port=6379,
    db=0,
    password=None,
    decode_responses=True
)

# Initialize Flask-Limiter for rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri='redis://localhost:6379',
    default_limits=["200 per day", "50 per hour"]
)

# Configure secure session management
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store the target number
target_number = random.randint(1, 100)

@app.route('/', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def index():
    global target_number
    if request.method == 'POST':
        try:
            guess = int(request.form['guess'])
            if not 1 <= guess <= 100:
                raise ValueError("Number out of range")
        except ValueError:
            logger.warning('Invalid input detected.')
            flash('Please enter a valid number between 1 and 100.')
            return redirect(url_for('index'))

        if guess < target_number:
            flash('Too low!')
        elif guess > target_number:
            flash('Too high!')
        else:
            flash('Congratulations! You guessed the number!')
            target_number = random.randint(1, 100)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
