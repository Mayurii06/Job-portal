from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

# MySQL connection configuration
db_config = {
    'host': 'localhost',
    'user': 'mayuri',
    'password': 'mypassword123',
    'database': 'job_portal'
}


def get_db_connection():
    return mysql.connector.connect(**db_config)

# Route: Register User
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data['name']
    email = data['email']
    password = data['password']
    skills = data.get('skills', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name, email, password, skills) VALUES (%s, %s, %s, %s)",
                       (name, email, password, skills))
        conn.commit()
        return jsonify({'message': 'User registered successfully!'}), 201
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Route: List Jobs
@app.route('/jobs', methods=['GET'])
def get_jobs():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM jobs")
    jobs = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(jobs)

# Route: Apply for a job
@app.route('/apply', methods=['POST'])
def apply():
    data = request.json
    user_id = data['user_id']
    job_id = data['job_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO applications (user_id, job_id) VALUES (%s, %s)", (user_id, job_id))
        conn.commit()
        return jsonify({'message': 'Application submitted successfully!'}), 201
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
