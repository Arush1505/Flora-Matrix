# from flask import Flask, request, jsonify, render_template, redirect, url_for, session
# import pymysql
# import pymysql.cursors
# import datetime
# import os
# import json
# import hashlib
# import numpy as np
# import tensorflow as tf
# from PIL import Image
# from werkzeug.utils import secure_filename
# import boto3
# from botocore.exceptions import NoCredentialsError
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# import random
# from functools import wraps
# import dotenv
# dotenv.load_dotenv()
# app = Flask(__name__)
# app.secret_key = "plantmd_secret_key_premium"
# app.config['UPLOAD_FOLDER'] = 'static/uploads'

# # Ensure upload directory exists
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# # RDS Database Configuration
# RDS_HOST = os.getenv("RDS_HOST")
# RDS_USER = os.getenv("RDS_USER")
# RDS_PW = os.getenv("RDS_PW")
# RDS_PORT = int(os.getenv("RDS_PORT", 3306))
# RDS_DB = os.getenv("RDS_DB")
# MODEL_PATH = "plant_disease_best.h5"
# REMEDIES_FILE = "remedies.json"

# # Amazon S3 Configuration
# S3_BUCKET = os.getenv("S3_BUCKET")
# S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
# S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
# S3_REGION = os.getenv("S3_REGION")

# # Admin Email Configuration
# ADMIN_GMAIL = os.getenv("ADMIN_GMAIL")
# GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


# s3_client = boto3.client(
#     's3',
#     aws_access_key_id=S3_ACCESS_KEY,
#     aws_secret_access_key=S3_SECRET_KEY,
#     region_name=S3_REGION
# )

# cloudwatch_client = boto3.client(
#     'cloudwatch',
#     aws_access_key_id=S3_ACCESS_KEY,
#     aws_secret_access_key=S3_SECRET_KEY,
#     region_name=S3_REGION
# )

# def get_db_connection():
#     return pymysql.connect(
#         host=RDS_HOST,
#         user=RDS_USER,
#         password=RDS_PW,
#         database=RDS_DB,
#         port=RDS_PORT,
#         cursorclass=pymysql.cursors.DictCursor
#     )

# class_names = [
#     'Cassava__bacterial_blight', 'Cassava__brown_streak_disease', 'Cassava__green_mottle', 
#     'Cassava__healthy', 'Cassava__mosaic_disease', 'Corn__common_rust', 'Corn__gray_leaf_spot', 
#     'Corn__healthy', 'Corn__northern_leaf_blight', 'Potato__early_blight', 'Potato__healthy', 
#     'Potato__late_blight', 'Rice__brown_spot', 'Rice__healthy', 'Rice__hispa', 'Rice__leaf_blast', 
#     'Rice__neck_blast', 'Sugarcane__bacterial_blight', 'Sugarcane__healthy', 'Sugarcane__red_rot', 
#     'Sugarcane__red_stripe', 'Sugarcane__rust', 'Tomato__bacterial_spot', 'Tomato__early_blight', 
#     'Tomato__healthy', 'Tomato__late_blight', 'Tomato__leaf_mold', 'Tomato__mosaic_virus', 
#     'Tomato__septoria_leaf_spot', 'Tomato__spider_mites_(two_spotted_spider_mite)', 
#     'Tomato__target_spot', 'Tomato__yellow_leaf_curl_virus', 'Wheat__brown_rust', 
#     'Wheat__healthy', 'Wheat__septoria', 'Wheat__yellow_rust'
# ]

# print("Loading Model...")
# model = tf.keras.models.load_model(MODEL_PATH)
# print("Model Loaded.")

# with open(REMEDIES_FILE, "r") as f:
#     remedies_data = json.load(f)

# def init_db():
#     conn = get_db_connection()
#     with conn.cursor() as c:
#         c.execute('''CREATE TABLE IF NOT EXISTS users (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             user_name VARCHAR(255) UNIQUE NOT NULL,
#             password TEXT NOT NULL,
#             date_of_register DATETIME NOT NULL,
#             is_admin INT NOT NULL DEFAULT 0
#         )''')
        
#         try:
#             c.execute("ALTER TABLE users ADD COLUMN is_admin INT NOT NULL DEFAULT 0")
#         except pymysql.err.OperationalError as e:
#             if e.args[0] != 1060: # 1060 is Duplicate column name
#                 print(f"Schema update note: {e}")
                
#         c.execute('''CREATE TABLE IF NOT EXISTS images (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             user_id INT NOT NULL,
#             Image_url TEXT,
#             upload_date DATETIME NOT NULL,
#             size_of_image INT NOT NULL,
#             status INT NOT NULL DEFAULT 0
#         )''')
#     conn.commit()
#     conn.close()

# init_db()

# def admin_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if "user_name" not in session:
#             return redirect(url_for('index'))
        
#         conn = get_db_connection()
#         try:
#             with conn.cursor() as c:
#                 c.execute("SELECT is_admin FROM users WHERE user_name=%s", (session["user_name"],))
#                 user = c.fetchone()
#         finally:
#             conn.close()
            
#         if not user or not user.get('is_admin'):
#             return render_template("auth.html", error="Admin privileges required.")
            
#         return f(*args, **kwargs)
#     return decorated_function

# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# @app.route("/")
# def index():
#     if "user_name" in session:
#         return redirect(url_for('dashboard'))
#     return render_template("auth.html")

# @app.route("/signup", methods=["POST"])
# def signup():
#     data = request.json
#     username = data.get("username")
#     password = data.get("password")
    
#     if not username or not password:
#         return jsonify({"success": False, "message": "Missing fields"}), 400

#     hashed_pw = hash_password(password)
#     registration_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#     try:
#         conn = get_db_connection()
#         with conn.cursor() as c:
#             c.execute("INSERT INTO users (user_name, password, date_of_register) VALUES (%s, %s, %s)", 
#                       (username, hashed_pw, registration_date))
#         conn.commit()
#         conn.close()
#         return jsonify({"success": True, "message": "Account created successfully! Please login."})
#     except pymysql.err.IntegrityError:
#         return jsonify({"success": False, "message": "Username already exists."}), 400
#     except Exception as e:
#         return jsonify({"success": False, "message": str(e)}), 500

# @app.route("/signin", methods=["POST"])
# def signin():
#     data = request.json
#     username = data.get("username")
#     password = data.get("password")
#     is_admin_login = data.get("is_admin", False)

#     hashed_pw = hash_password(password)

#     conn = get_db_connection()
#     with conn.cursor() as c:
#         c.execute("SELECT * FROM users WHERE user_name=%s AND password=%s", (username, hashed_pw))
#         user = c.fetchone()
#     conn.close()

#     if user:
#         if is_admin_login:
#             if not user.get('is_admin'):
#                 return jsonify({"success": False, "message": "Not authorized as Admin."}), 403
#             session["user_name"] = username
#             return jsonify({"success": True, "message": "Admin logged in successfully!", "redirect": "/admin/dashboard"})
#         else:
#             session["user_name"] = username
#             return jsonify({"success": True, "message": "Logged in successfully!", "redirect": "/dashboard"})
#     else:
#         return jsonify({"success": False, "message": "Invalid credentials!"}), 401

# @app.route("/logout", methods=["POST"])
# def logout():
#     session.pop("user_name", None)
#     return jsonify({"success": True})

# @app.route("/dashboard")
# def dashboard():
#     if "user_name" not in session:
#         return redirect(url_for('index'))
#     return render_template("dashboard.html", username=session["user_name"])

# @app.route("/remedies")
# def remedies():
#     if "user_name" not in session:
#         return redirect(url_for('index'))
#     return render_template("remedies.html", username=session["user_name"])

# @app.route("/api/predict", methods=["POST"])
# def predict():
#     if "user_name" not in session:
#         return jsonify({"error": "Unauthorized"}), 401

#     if "file" not in request.files:
#         return jsonify({"error": "No file uploaded"}), 400

#     file = request.files["file"]
#     if file.filename == "":
#         return jsonify({"error": "No file selected"}), 400

#     filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
#     file.save(filepath)

#     try:
#         img = Image.open(filepath).convert("RGB")
#         # Get image size in bytes
#         image_size = os.path.getsize(filepath)
        
#         img = img.resize((224, 224))
#         img_array = np.array(img, dtype=np.float32)
#         img_array = np.expand_dims(img_array, axis=0)

#         probs = model.predict(img_array, verbose=0)[0]
#         top_idx = int(np.argmax(probs))
#         confidence = float(np.max(probs))

#         disease_class = class_names[top_idx]
#         remedy_info = next((item for item in remedies_data if item["disease"] == disease_class), None)

#         # 1. Get user_id from RDS
#         conn = get_db_connection()
#         with conn.cursor() as c:
#             c.execute("SELECT id FROM users WHERE user_name=%s", (session["user_name"],))
#             user_data = c.fetchone()
        
#         user_id = user_data['id'] if user_data else 0
#         upload_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         s3_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{secure_filename(file.filename)}"
#         upload_status = 0

#         # 2. Upload to S3 if prediction is successful
#         try:
#             s3_client.upload_file(filepath, S3_BUCKET, secure_filename(file.filename))
#             upload_status = 1
#         except Exception as upload_err:
#             print(f"S3 Upload Error: {upload_err}")
#             upload_status = 0

#         # 3. Save to RDS
#         with conn.cursor() as c_img:
#             c_img.execute("""
#                 INSERT INTO images (user_id, Image_url, upload_date, size_of_image, status)
#                 VALUES (%s, %s, %s, %s, %s)
#             """, (user_id, s3_url, upload_date, image_size, upload_status))
#         conn.commit()
#         conn.close()

#         return jsonify({
#             "success": True,
#             "disease_class": disease_class,
#             "confidence": round(confidence * 100, 2),
#             "remedy": remedy_info,
#             "image_url": s3_url if upload_status == 1 else None
#         })
#     except Exception as e:
#         return jsonify({"error": "Prediction failed", "details": str(e)}), 500

# @app.route("/api/remedies_data", methods=["GET"])
# def get_remedies_data():
#     if "user_name" not in session:
#         return jsonify({"error": "Unauthorized"}), 401
#     return jsonify(remedies_data)

# @app.route("/admin/signup", methods=["GET", "POST"])
# def admin_signup():
#     if request.method == "GET":
#         return render_template("admin_signup.html")
        
#     data = request.json
#     username = data.get("username")
#     password = data.get("password")
#     email = data.get("email")
    
#     if not username or not password or not email:
#         return jsonify({"success": False, "message": "Missing fields"}), 400

#     conn = get_db_connection()
#     try:
#         with conn.cursor() as c:
#             c.execute("SELECT id FROM users WHERE user_name=%s", (username,))
#             if c.fetchone():
#                 return jsonify({"success": False, "message": "Username already exists."}), 400
#     finally:
#         conn.close()

#     verification_code = str(random.randint(1000, 9999))
#     session["pending_admin"] = {
#         "username": username,
#         "password": hash_password(password),
#         "code": verification_code
#     }

#     if not ADMIN_GMAIL or not GMAIL_APP_PASSWORD:
#         print("ERROR: ADMIN_GMAIL or GMAIL_APP_PASSWORD is missing in .env")
#         return jsonify({"success": False, "message": "Email not configured on server. Please add ADMIN_GMAIL and GMAIL_APP_PASSWORD to .env file."}), 500

#     try:
#         msg = MIMEMultipart()
#         msg['From'] = ADMIN_GMAIL
#         msg['To'] = ADMIN_GMAIL
#         msg['Subject'] = "Admin Signup Request - Flora Matrix"
        
#         body = f"A new user has requested Admin access.\nUsername: {username}\nEmail: {email}\n\nVerification Code: {verification_code}"
#         msg.attach(MIMEText(body, 'plain'))
        
#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
#         server.login(ADMIN_GMAIL, GMAIL_APP_PASSWORD)
#         text = msg.as_string()
#         server.sendmail(ADMIN_GMAIL, ADMIN_GMAIL, text)
#         server.quit()
        
#         return jsonify({"success": True, "message": "Verification code sent to Admin."})
#     except Exception as e:
#         print(f"Email error: {e}")
#         return jsonify({"success": False, "message": "Failed to send verification email."}), 500

# @app.route("/admin/verify", methods=["GET", "POST"])
# def admin_verify():
#     if request.method == "GET":
#         if "pending_admin" not in session:
#             return redirect(url_for("admin_signup"))
#         return render_template("admin_verify.html")
        
#     data = request.json
#     code = data.get("code")
    
#     if "pending_admin" not in session:
#         return jsonify({"success": False, "message": "Session expired. Please signup again."}), 400
        
#     pending = session["pending_admin"]
#     if str(code) != pending["code"]:
#         return jsonify({"success": False, "message": "Invalid verification code."}), 400
        
#     registration_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     conn = get_db_connection()
#     try:
#         with conn.cursor() as c:
#             c.execute("INSERT INTO users (user_name, password, date_of_register, is_admin) VALUES (%s, %s, %s, 1)", 
#                       (pending["username"], pending["password"], registration_date))
#         conn.commit()
#     except pymysql.err.IntegrityError:
#         return jsonify({"success": False, "message": "Username already exists."}), 400
#     except Exception as e:
#         return jsonify({"success": False, "message": str(e)}), 500
#     finally:
#         conn.close()
        
#     session.pop("pending_admin", None)
#     return jsonify({"success": True, "message": "Admin account verified and created!"})

# @app.route("/admin/dashboard")
# @admin_required
# def admin_dashboard():
#     conn = get_db_connection()
#     metrics = {}
#     users_list = []
#     images_list = []
    
#     try:
#         with conn.cursor() as c:
#             c.execute("SELECT COUNT(*) as total FROM users")
#             metrics['total_users'] = c.fetchone()['total']
            
#             c.execute("SELECT SUM(size_of_image) as total_size FROM images")
#             res = c.fetchone()
#             metrics['total_size_bytes'] = res['total_size'] if res['total_size'] else 0
#             metrics['total_size_mb'] = round(metrics['total_size_bytes'] / (1024 * 1024), 2)
            
#             c.execute("SELECT status, COUNT(*) as count FROM images GROUP BY status")
#             status_counts = c.fetchall()
#             metrics['success_count'] = next((item['count'] for item in status_counts if item['status'] == 1), 0)
#             metrics['fail_count'] = next((item['count'] for item in status_counts if item['status'] == 0), 0)
            
#             c.execute("SELECT id, user_name, date_of_register, is_admin FROM users ORDER BY id DESC LIMIT 10")
#             users_list = c.fetchall()
            
#             c.execute("SELECT id, user_id, upload_date, size_of_image, status FROM images ORDER BY id DESC LIMIT 10")
#             images_list = c.fetchall()
#     except Exception as e:
#         print(f"DB Analytics Error: {e}")
#     finally:
#         conn.close()
        
#     aws_metrics = {'cpu': 'N/A', 's3_objects': 'N/A'}
#     try:
#         cpu_response = cloudwatch_client.get_metric_statistics(
#             Namespace='AWS/RDS',
#             MetricName='CPUUtilization',
#             Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': 'flora-db'}],
#             StartTime=datetime.datetime.utcnow() - datetime.timedelta(hours=1),
#             EndTime=datetime.datetime.utcnow(),
#             Period=3600,
#             Statistics=['Average']
#         )
#         if cpu_response['Datapoints']:
#             aws_metrics['cpu'] = f"{round(cpu_response['Datapoints'][0]['Average'], 2)}%"
            
#         s3_response = cloudwatch_client.get_metric_statistics(
#             Namespace='AWS/S3',
#             MetricName='NumberOfObjects',
#             Dimensions=[{'Name': 'BucketName', 'Value': S3_BUCKET}, {'Name': 'StorageType', 'Value': 'AllStorageTypes'}],
#             StartTime=datetime.datetime.utcnow() - datetime.timedelta(days=2),
#             EndTime=datetime.datetime.utcnow(),
#             Period=86400,
#             Statistics=['Average']
#         )
#         if s3_response['Datapoints']:
#             aws_metrics['s3_objects'] = int(s3_response['Datapoints'][0]['Average'])
            
#     except Exception as e:
#         print(f"AWS Metrics Error: {e}")

#     return render_template("admin_dashboard.html", username=session["user_name"], metrics=metrics, aws_metrics=aws_metrics, users=users_list, images=images_list)

# if __name__ == "__main__":
#     app.run(debug=True, port=8000)

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import pymysql
import pymysql.cursors
import datetime
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logging
import json
import hashlib
import numpy as np
import tensorflow as tf
from PIL import Image
from werkzeug.utils import secure_filename
import boto3
from botocore.exceptions import NoCredentialsError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import io
from functools import wraps
import dotenv

dotenv.load_dotenv()
app = Flask(__name__)
app.secret_key = "plantmd_secret_key_premium"
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# RDS Database Configuration
RDS_HOST = os.getenv("RDS_HOST")
RDS_USER = os.getenv("RDS_USER")
RDS_PW = os.getenv("RDS_PW")
RDS_PORT = int(os.getenv("RDS_PORT", 3306))
RDS_DB = os.getenv("RDS_DB")
MODEL_PATH = "plant_disease_best.h5"
REMEDIES_FILE = "remedies.json"

# Amazon S3 Configuration
S3_BUCKET = os.getenv("S3_BUCKET")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_REGION = os.getenv("S3_REGION")

# Admin Email Configuration
ADMIN_GMAIL = os.getenv("ADMIN_GMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

s3_client = boto3.client(
    's3',
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION
)

cloudwatch_client = boto3.client(
    'cloudwatch',
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION
)

def get_db_connection():
    return pymysql.connect(
        host=RDS_HOST,
        user=RDS_USER,
        password=RDS_PW,
        database=RDS_DB,
        port=RDS_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

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

# --- LOAD MODEL AT STARTUP ---
# This executes once when the app starts
print("--- Loading Plant Disease Model (this may take a few seconds)... ---")
model = tf.keras.models.load_model(MODEL_PATH)
print("--- Model Loaded Successfully. ---")

with open(REMEDIES_FILE, "r") as f:
    remedies_data = json.load(f)

def init_db():
    conn = get_db_connection()
    with conn.cursor() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_name VARCHAR(255) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            date_of_register DATETIME NOT NULL,
            is_admin INT NOT NULL DEFAULT 0
        )''')
        
        try:
            c.execute("ALTER TABLE users ADD COLUMN is_admin INT NOT NULL DEFAULT 0")
        except pymysql.err.OperationalError as e:
            if e.args[0] != 1060: # 1060 is Duplicate column name
                print(f"Schema update note: {e}")
                
        c.execute('''CREATE TABLE IF NOT EXISTS images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            Image_url TEXT,
            upload_date DATETIME NOT NULL,
            size_of_image INT NOT NULL,
            status INT NOT NULL DEFAULT 0
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS user_feedback (
            feedback_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            feedback TEXT NOT NULL,
            date_of_feedback DATETIME NOT NULL,
            feedback_status INT NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')
    conn.commit()
    conn.close()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_name" not in session:
            return redirect(url_for('index'))
        
        conn = get_db_connection()
        try:
            with conn.cursor() as c:
                c.execute("SELECT is_admin FROM users WHERE user_name=%s", (session["user_name"],))
                user = c.fetchone()
        finally:
            conn.close()
            
        if not user or not user.get('is_admin'):
            return render_template("auth.html", error="Admin privileges required.")
            
        return f(*args, **kwargs)
    return decorated_function

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
        conn = get_db_connection()
        with conn.cursor() as c:
            c.execute("INSERT INTO users (user_name, password, date_of_register) VALUES (%s, %s, %s)", 
                      (username, hashed_pw, registration_date))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Account created successfully! Please login."})
    except pymysql.err.IntegrityError:
        return jsonify({"success": False, "message": "Username already exists."}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/signin", methods=["POST"])
def signin():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    is_admin_login = data.get("is_admin", False)

    hashed_pw = hash_password(password)

    conn = get_db_connection()
    with conn.cursor() as c:
        c.execute("SELECT * FROM users WHERE user_name=%s AND password=%s", (username, hashed_pw))
        user = c.fetchone()
    conn.close()

    if user:
        if is_admin_login:
            if not user.get('is_admin'):
                return jsonify({"success": False, "message": "Not authorized as Admin."}), 403
            session["user_name"] = username
            return jsonify({"success": True, "message": "Admin logged in successfully!", "redirect": "/admin/dashboard"})
        else:
            session["user_name"] = username
            return jsonify({"success": True, "message": "Logged in successfully!", "redirect": "/dashboard"})
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

    filename = secure_filename(file.filename)
    file_content = file.read()
    image_size = len(file_content)

    try:
        img = Image.open(io.BytesIO(file_content)).convert("RGB")
        img = img.resize((224, 224))
        img_array = np.array(img, dtype=np.float32)
        img_array = np.expand_dims(img_array, axis=0)

        # Use the global model directly
        probs = model.predict(img_array, verbose=0)[0]
        top_idx = int(np.argmax(probs))
        confidence = float(np.max(probs))

        disease_class = class_names[top_idx]
        remedy_info = next((item for item in remedies_data if item["disease"] == disease_class), None)

        conn = get_db_connection()
        with conn.cursor() as c:
            c.execute("SELECT id FROM users WHERE user_name=%s", (session["user_name"],))
            user_data = c.fetchone()
        
        user_id = user_data['id'] if user_data else 0
        upload_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        s3_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}"
        upload_status = 0

        try:
            s3_client.upload_fileobj(io.BytesIO(file_content), S3_BUCKET, filename)
            upload_status = 1
        except Exception as upload_err:
            print(f"S3 Upload Error: {upload_err}")
            upload_status = 0

        with conn.cursor() as c_img:
            c_img.execute("""
                INSERT INTO images (user_id, Image_url, upload_date, size_of_image, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, s3_url, upload_date, image_size, upload_status))
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "disease_class": disease_class,
            "confidence": round(confidence * 100, 2),
            "remedy": remedy_info,
            "image_url": s3_url if upload_status == 1 else None
        })
    except Exception as e:
        return jsonify({"error": "Prediction failed", "details": str(e)}), 500

@app.route("/api/remedies_data", methods=["GET"])
def get_remedies_data():
    if "user_name" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(remedies_data)

@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    if "user_name" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.json
    feedback_text = data.get("feedback")
    
    if not feedback_text or not feedback_text.strip():
        return jsonify({"success": False, "message": "Feedback cannot be empty."}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id FROM users WHERE user_name=%s", (session["user_name"],))
            user_data = c.fetchone()
            if not user_data:
                return jsonify({"success": False, "message": "User not found."}), 404
            
            user_id = user_data['id']
            date_of_feedback = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            c.execute("""
                INSERT INTO user_feedback (user_id, feedback, date_of_feedback, feedback_status)
                VALUES (%s, %s, %s, 0)
            """, (user_id, feedback_text, date_of_feedback))
        conn.commit()
        return jsonify({"success": True, "message": "Feedback submitted successfully!"})
    except Exception as e:
        print(f"Feedback Error: {e}")
        return jsonify({"success": False, "message": "Failed to submit feedback."}), 500
    finally:
        conn.close()

@app.route("/admin/feedback/read", methods=["POST"])
@admin_required
def mark_feedback_read():
    data = request.json
    feedback_id = data.get("feedback_id")
    
    if not feedback_id:
        return jsonify({"success": False, "message": "Missing feedback ID."}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as c:
            c.execute("UPDATE user_feedback SET feedback_status = 1 WHERE feedback_id = %s", (feedback_id,))
        conn.commit()
        return jsonify({"success": True, "message": "Feedback marked as read."})
    except Exception as e:
        print(f"Feedback Read Error: {e}")
        return jsonify({"success": False, "message": "Failed to mark feedback as read."}), 500
    finally:
        conn.close()

@app.route("/admin/signup", methods=["GET", "POST"])
def admin_signup():
    if request.method == "GET":
        return render_template("admin_signup.html")
        
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    
    if not username or not password or not email:
        return jsonify({"success": False, "message": "Missing fields"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT id FROM users WHERE user_name=%s", (username,))
            if c.fetchone():
                return jsonify({"success": False, "message": "Username already exists."}), 400
    finally:
        conn.close()

    verification_code = str(random.randint(1000, 9999))
    session["pending_admin"] = {
        "username": username,
        "password": hash_password(password),
        "code": verification_code
    }

    if not ADMIN_GMAIL or not GMAIL_APP_PASSWORD:
        return jsonify({"success": False, "message": "Email not configured on server."}), 500

    try:
        msg = MIMEMultipart()
        msg['From'] = ADMIN_GMAIL
        msg['To'] = ADMIN_GMAIL
        msg['Subject'] = "Admin Signup Request - Flora Matrix"
        body = f"A new user requested Admin access.\nUsername: {username}\nEmail: {email}\nVerification Code: {verification_code}"
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(ADMIN_GMAIL, GMAIL_APP_PASSWORD)
        server.sendmail(ADMIN_GMAIL, ADMIN_GMAIL, msg.as_string())
        server.quit()
        
        return jsonify({"success": True, "message": "Verification code sent to Admin."})
    except Exception as e:
        return jsonify({"success": False, "message": "Failed to send email."}), 500

@app.route("/admin/verify", methods=["GET", "POST"])
def admin_verify():
    if request.method == "GET":
        if "pending_admin" not in session:
            return redirect(url_for("admin_signup"))
        return render_template("admin_verify.html")
        
    data = request.json
    code = data.get("code")
    
    if "pending_admin" not in session:
        return jsonify({"success": False, "message": "Session expired."}), 400
        
    pending = session["pending_admin"]
    if str(code) != pending["code"]:
        return jsonify({"success": False, "message": "Invalid verification code."}), 400
        
    registration_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    try:
        with conn.cursor() as c:
            c.execute("INSERT INTO users (user_name, password, date_of_register, is_admin) VALUES (%s, %s, %s, 1)", 
                      (pending["username"], pending["password"], registration_date))
        conn.commit()
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()
        
    session.pop("pending_admin", None)
    return jsonify({"success": True, "message": "Admin account verified!"})

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    metrics = {}
    users_list = []
    images_list = []
    feedback_list = []
    
    try:
        with conn.cursor() as c:
            c.execute("SELECT COUNT(*) as total FROM users")
            metrics['total_users'] = c.fetchone()['total']
            
            c.execute("SELECT SUM(size_of_image) as total_size FROM images")
            res = c.fetchone()
            metrics['total_size_bytes'] = res['total_size'] if res['total_size'] else 0
            metrics['total_size_mb'] = round(metrics['total_size_bytes'] / (1024 * 1024), 2)
            
            c.execute("SELECT status, COUNT(*) as count FROM images GROUP BY status")
            status_counts = c.fetchall()
            metrics['success_count'] = next((item['count'] for item in status_counts if item['status'] == 1), 0)
            metrics['fail_count'] = next((item['count'] for item in status_counts if item['status'] == 0), 0)
            
            c.execute("SELECT id, user_name, date_of_register, is_admin FROM users ORDER BY id DESC LIMIT 10")
            users_list = c.fetchall()
            
            c.execute("SELECT id, user_id, upload_date, size_of_image, status FROM images ORDER BY id DESC LIMIT 10")
            images_list = c.fetchall()
            
            c.execute("""
                SELECT f.feedback_id, f.feedback, f.date_of_feedback, f.feedback_status, u.user_name 
                FROM user_feedback f 
                JOIN users u ON f.user_id = u.id 
                WHERE f.feedback_status = 0
                ORDER BY f.date_of_feedback DESC
            """)
            feedback_list = c.fetchall()
    finally:
        conn.close()
        
    aws_metrics = {'cpu': 'N/A', 's3_objects': 'N/A'}
    try:
        cpu_response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/RDS',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': 'flora-db'}],
            StartTime=datetime.datetime.utcnow() - datetime.timedelta(hours=1),
            EndTime=datetime.datetime.utcnow(),
            Period=3600,
            Statistics=['Average']
        )
        if cpu_response['Datapoints']:
            aws_metrics['cpu'] = f"{round(cpu_response['Datapoints'][0]['Average'], 2)}%"
            
        s3_response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/S3',
            MetricName='NumberOfObjects',
            Dimensions=[{'Name': 'BucketName', 'Value': S3_BUCKET}, {'Name': 'StorageType', 'Value': 'AllStorageTypes'}],
            StartTime=datetime.datetime.utcnow() - datetime.timedelta(days=2),
            EndTime=datetime.datetime.utcnow(),
            Period=86400,
            Statistics=['Average']
        )
        if s3_response['Datapoints']:
            aws_metrics['s3_objects'] = int(s3_response['Datapoints'][0]['Average'])
    except:
        pass

    return render_template("admin_dashboard.html", username=session["user_name"], metrics=metrics, aws_metrics=aws_metrics, users=users_list, images=images_list, feedbacks=feedback_list)

if __name__ == "__main__":
    app.run(debug=True, port=8000,use_reloader=False)