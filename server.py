from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sqlite3
import datetime
import os
import json
import hashlib
import numpy as np
import tensorflow as tf
from PIL import Image
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "plantmd_secret_key_premium"
# app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure upload directory exists
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_FILE = "users.sqlite"
MODEL_PATH = "plant_disease_best.h5"
REMEDIES_FILE = "remedies.json"

class_names = [
    'Cassava__bacterial_blight', 'Cassava__brown_streak_disease', 'Cassava__green_mottle', 
    'Cassava__healthy', 'Cassava__mosaic_disease', 'Corn__common_rust', 'Corn__gray_leaf_spot', 
    'Corn__healthy', 'Corn__northern_leaf_blight', 'Potato__early_blight', 'Potato__healthy', 
    'Potato__late_blight', 'Rice__brown_spot', 'Rice__healthy', 'Rice__hispa', 'Rice__leaf_blast', 
    'Rice__neck_blast', 'Sugarcane__bacterial_blight', 'Sugarcane__healthy', 'Sugarcane__red_rot', 
    'Sugarcane__red_stripe', 'Sugarcane__rust', 'Tomato__bacterial_spot', 'Tomato__early_blight', 
    'Tomato__healthy', 'Tomato__late_blight', 'Tomato__leaf_mold', 'Tomato__mosaic_virus', 
    'Tomato__septoria_leaf_spot', 'Tomato__spider_mites_(two_spotted_spider_mite)', 
    'Tomato__target_spot', 'Tomato__yellow_leaf_curl_virus', 'Wheat__brown_rust', 
    'Wheat__healthy', 'Wheat__septoria', 'Wheat__yellow_rust'
]

print("Loading Model...")
model = tf.keras.models.load_model(MODEL_PATH)
print("Model Loaded.")

with open(REMEDIES_FILE, "r") as f:
    remedies_data = json.load(f)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        date_of_register TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route("/")
def index():
    if "user_name" in session:
        return redirect(url_for('dashboard'))
    return render_template("auth.html")

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"success": False, "message": "Missing fields"}), 400

    hashed_pw = hash_password(password)
    registration_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO users (user_name, password, date_of_register) VALUES (?, ?, ?)", 
                  (username, hashed_pw, registration_date))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Account created successfully! Please login."})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username already exists."}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/signin", methods=["POST"])
def signin():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    hashed_pw = hash_password(password)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_name=? AND password=?", (username, hashed_pw))
    user = c.fetchone()
    conn.close()

    if user:
        session["user_name"] = username
        return jsonify({"success": True, "message": "Logged in successfully!"})
    else:
        return jsonify({"success": False, "message": "Invalid credentials!"}), 401

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_name", None)
    return jsonify({"success": True})

@app.route("/dashboard")
def dashboard():
    if "user_name" not in session:
        return redirect(url_for('index'))
    return render_template("dashboard.html", username=session["user_name"])

@app.route("/remedies")
def remedies():
    if "user_name" not in session:
        return redirect(url_for('index'))
    return render_template("remedies.html", username=session["user_name"])

@app.route("/api/predict", methods=["POST"])
def predict():
    if "user_name" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(filepath)

    try:
        img = Image.open(filepath).convert("RGB")
        img = img.resize((224, 224))
        img_array = np.array(img, dtype=np.float32)
        img_array = np.expand_dims(img_array, axis=0)

        probs = model.predict(img_array, verbose=0)[0]
        top_idx = int(np.argmax(probs))
        confidence = float(np.max(probs))

        disease_class = class_names[top_idx]
        
        remedy_info = next((item for item in remedies_data if item["disease"] == disease_class), None)

        # file_url = url_for('static', filename='uploads/' + secure_filename(file.filename))

        return jsonify({
            "success": True,
            "disease_class": disease_class,
            "confidence": round(confidence * 100, 2),
            "remedy": remedy_info
            # "image_url": file_url
        })
    except Exception as e:
        return jsonify({"error": "Prediction failed", "details": str(e)}), 500

@app.route("/api/remedies_data", methods=["GET"])
def get_remedies_data():
    if "user_name" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(remedies_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
