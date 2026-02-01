from flask import Flask
from flask_cors import CORS
from auth import auth_bp
from jobs import jobs_bp
from profile import profile_bp

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(jobs_bp)
app.register_blueprint(profile_bp)


@app.route("/")
def home():
    return "Backend is running 🚀"


# IMPORTANT for deployment
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)