from flask import Flask, request, jsonify
import mysql.connector
import bcrypt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd


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


# Register User Route

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data['name']
    email = data['email']
    password = data['password']
    skills = data.get('skills', '')

    # Encode and hash password
    password_bytes = password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check for duplicate email
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 409

        # Insert user
        cursor.execute(
            "INSERT INTO users (name, email, password, skills) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_password, skills)
        )
        conn.commit()
        return jsonify({'message': 'User registered successfully!'}), 201

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400

    finally:
        cursor.close()
        conn.close()


# Login Part

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password'].encode('utf-8')  # Encode to bytes

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, password FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()

        if not result:
            return jsonify({'error': 'User not found'}), 404

        user_id, stored_hashed_password = result
        stored_hashed_password = stored_hashed_password.encode('utf-8')  # Convert to bytes

        if bcrypt.checkpw(password, stored_hashed_password):
            return jsonify({'message': 'Login successful!', 'user_id': user_id}), 200
        else:
            return jsonify({'error': 'Incorrect password'}), 401

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400

    finally:
        cursor.close()
        conn.close()


# Route List Jobs  Route 
@app.route('/jobs', methods=['GET'])
def get_jobs():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM jobs")
    jobs = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(jobs)


#  Apply for a Job  Route 

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
@app.route('/recommend/<int:user_id>', methods=['GET'])
def recommend_jobs(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get the user's skills
    cursor.execute("SELECT skills FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user_skills = user['skills']

    # Get all jobs
    cursor.execute("SELECT * FROM jobs")
    jobs = cursor.fetchall()
    if not jobs:
        return jsonify({'message': 'No jobs found'}), 200

    # Prepare data for similarity
    df = pd.DataFrame(jobs)
    df['text'] = df['title'] + ' ' + df['company'] + ' ' + df['description']

    # Compute similarity
    corpus = [user_skills] + df['text'].tolist()
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    df['score'] = cosine_similarities
    top_jobs = df.sort_values(by='score', ascending=False).head(5)

    cursor.close()
    conn.close()

    return jsonify(top_jobs[['job_id', 'title', 'company', 'location', 'description', 'score']].to_dict(orient='records'))



if __name__ == '__main__':
    app.run(debug=True)
