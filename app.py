from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import pandas as pd
import logging
from dotenv import load_dotenv
import os
from waitress import serve

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Setting up logging
logging.basicConfig(level=logging.DEBUG)
load_dotenv()
# MySQL Connection
def get_mysql_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
# Upload CSV data to MySQL
@app.route('/upload_students_csv', methods=['POST'])
def upload_students_csv():
    try:
        if 'csv_file' not in request.files:
            return jsonify({"success": False, "message": "No CSV file uploaded"}), 400

        csv_file = request.files['csv_file']
        if csv_file.filename == '':
            return jsonify({"success": False, "message": "Empty CSV file uploaded"}), 400

        df = pd.read_csv(csv_file)

        conn = get_mysql_connection()
        cursor = conn.cursor()

        query = """INSERT INTO students1 (student_id, student_name, student_phone, parent_phone)
                   VALUES (%s, %s, %s, %s)"""

        data = df[['student_id', 'student_name', 'student_phone', 'parent_phone']].values.tolist()

        cursor.executemany(query, data)
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": f"{len(df)} students uploaded successfully"}), 201
    except Exception as e:
        logging.error(f"Error uploading CSV: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# Fetch a specific student by ID
@app.route('/get_student_data', methods=['GET'])
def get_student_data():
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({"success": False, "message": "Student ID is required"}), 400

    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM students1 WHERE student_id = %s"
        cursor.execute(query, (student_id,))
        student = cursor.fetchone()
        conn.close()

        if student:
            return jsonify({"success": True, "data": student}), 200
        else:
            return jsonify({"success": False, "message": "Student not found"}), 404
    except Exception as e:
        logging.error(f"Error fetching student: {str(e)}")
        return jsonify({"success": False, "message": "Error fetching student"}), 500

if __name__ == "__main__":
    port = os.environ.get('PORT', 8080)  # Use Railway's dynamic port or default to 5000
    serve(app, host='0.0.0.0', port=int(port))
