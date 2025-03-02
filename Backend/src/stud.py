from flask import Flask, jsonify, Blueprint, render_template, request
import cx_Oracle
from flask import session
import oracledb

# Database connection parameters
DB_USERNAME = 'ADMIN'
DB_PASSWORD = 'msu8nTwIkf6isAR5qBmp'
DB_DSN = "v9n3ba1erzl8nuba_high"
DB_WALLET_PASSWORD = "dR3kQd8utf5jLyqRyeFx"
#DB_WALLET_LOCATION = r"C:\\Users\\Boris\\Desktop\\Wallet_V9N3BA1ERZL8NUBA"
DB_WALLET_LOCATION = r"D:\\SYSTEM_FOLDERS\\Downloads\\Wallet_V9N3BA1ERZL8NUBA"
# Function to get database connection
def get_db_connection():
    try:
        connection = oracledb.connect(
            config_dir=DB_WALLET_LOCATION,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            dsn=DB_DSN,
            wallet_location=DB_WALLET_LOCATION,
            wallet_password=DB_WALLET_PASSWORD
        )
        return connection
    except oracledb.DatabaseError as e:
        error, = e.args
        print(f"Database connection error: {error.message}")
        return None 

# Create a Blueprint
stud_bp = Blueprint('students', __name__)

@stud_bp.route('/')
def index():
    # Fetch student data from the database
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        # Assuming you have a way to identify the current student (e.g., from session or authentication)
        student_id = 1  # Replace with the actual student ID
        cursor.execute("SELECT STUD_ID, VARDS, UZVARDS, LIETOTAJVARDS, EPASTS FROM STUDENTI WHERE STUD_ID = :student_id", 
                       {"student_id": student_id})
        student_data = cursor.fetchone()

        if student_data:
            student_info = {
                "id": student_data[0],  # ID
                "name": student_data[1],  # NAME
                "surname": student_data[2],  # SURNAME
                "username": student_data[3],  # USERNAME
                "email": student_data[4]  # EMAIL
            }
            return render_template('Students_page.html', students=student_info)
        else:
            return jsonify({"error": "Student not found"}), 404
    
    except cx_Oracle.DatabaseError as e:
        return jsonify({"error": "Database query failed"}), 500
    
    finally:
        cursor.close()
        conn.close()

# API, lai iegūtu visus rakstus no RAKSTI tabulas
@stud_bp.route('/get-papers', methods=['GET'])
def get_papers():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT RAKSTANR, FILE_NAME, STUD_ID FROM RAKSTI")

        papers = []
        for row in cursor:
            papers.append({
                "id": row[0],  # RAKSTANR
                "title": row[1],  # FILE_NAME
                "student_id": row[2]  # STUD_ID
            })

        return jsonify({"papers": papers})
    
    except cx_Oracle.DatabaseError as e:
        return jsonify({"error": "Database query failed"}), 500
    
    finally:
        cursor.close()
        conn.close()

# Maršruts, lai atsauktu rakstu
@stud_bp.route('/decline-paper/<int:paper_id>', methods=['POST'])
def decline_paper(paper_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    user_id = session.get('user_id')  # Ielogotā studenta ID

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 403  # Neatļauts pieprasījums

    try:
        cursor = conn.cursor()

        # Pārbaudām, vai students ir raksta īpašnieks
        cursor.execute("""
            SELECT STUD_ID FROM RAKSTI WHERE RAKSTANR = :paper_id
        """, {"paper_id": paper_id})
        paper = cursor.fetchone()

        if not paper:
            return jsonify({"error": "Paper not found"}), 404

        if paper[0] != user_id:
            return jsonify({"error": "You can only decline your own paper"}), 403

        # Ja viss ok, atiestatām STUD_ID
        cursor.execute("""
            UPDATE RAKSTI SET STUD_ID = NULL WHERE RAKSTANR = :paper_id
        """, {"paper_id": paper_id})
        conn.commit()

        return jsonify({"success": True})

    except cx_Oracle.DatabaseError as e:
        return jsonify({"error": "Database query failed"}), 500

    finally:
        cursor.close()
        conn.close()


@stud_bp.route('/choose-paper/<int:paper_id>', methods=['POST'])
def choose_paper(paper_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        # Get student_id from the request body
        data = request.get_json()
        student_id = data.get('student_id')

        if not student_id:
            return jsonify({"error": "Student ID is required"}), 400

        cursor = conn.cursor()
        cursor.execute("UPDATE RAKSTI SET STUD_ID = :student_id WHERE RAKSTANR = :paper_id", 
                       {"student_id": student_id, "paper_id": paper_id})
        conn.commit()
        return jsonify({"success": True})
    
    except cx_Oracle.DatabaseError as e:
        print("Database error:", e)  # Debugging
        return jsonify({"error": "Database query failed"}), 500
    
    finally:
        cursor.close()
        conn.close()

@stud_bp.route('/edit_profile', methods=['PUT'])
def edit_profile():
    """Edit an existing profile in the database."""
    data = request.json
    print(data)
    stud_id = data.get('stud-id')
    name = data.get('name', '').strip()
    surname = data.get('surname', '').strip()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()

        # Check if the student exists by ID
        cursor.execute("SELECT COUNT(*) FROM STUDENTI WHERE STUD_ID = :1", (stud_id,))
        exists = cursor.fetchone()[0]

        if not exists:
            return jsonify({"error": "Student not found"}), 404

        # Update the student based on ID
        cursor.execute(
            """
            UPDATE STUDENTI
            SET VARDS = :1, UZVARDS = :2, LIETOTAJVARDS = :3, EPASTS = :4
            WHERE STUD_ID = :5
            """,
            (name, surname, username, email, stud_id)
        )
        conn.commit()

        return jsonify({"success": True, "message": "Student updated successfully!"})
    except cx_Oracle.DatabaseError as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()    

@stud_bp.route('/parole')
def parole():
        return render_template('new_password.html')   

if __name__ == '__main__':
    stud_bp.run(debug=True)
