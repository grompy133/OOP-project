from flask import Blueprint, render_template, jsonify, request
import cx_Oracle

# Database connection details
DB_USERNAME = 'C##sistema'
DB_PASSWORD = '=dAb21Jm09'
DB_DSN = 'localhost:1521/ORCL'

# Function to connect to the database
def get_db_connection():
    try:
        return cx_Oracle.connect(user=DB_USERNAME, password=DB_PASSWORD, dsn=DB_DSN)
    except cx_Oracle.DatabaseError as e:
        print("Database connection error:", e)
        return None

pasn_bp = Blueprint('pasniedzejs', __name__)

@pasn_bp.route('/')
def index():
    """Load the HTML page."""
    return render_template('teacher_page.html')

@pasn_bp.route('/get_students', methods=['GET'])
def get_students():
    """Fetch the list of students from the database."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT STUD_ID, VARDS, UZVARDS, EPASTS FROM STUDENTI")
        students = [{"id": row[0], "name": row[1], "surname": row[2], "email": row[3]} for row in cursor]
        return jsonify(students)
    except cx_Oracle.DatabaseError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@pasn_bp.route('/add_student', methods=['POST'])
def add_student():
    data = request.json
    name = data.get('name')
    surname = data.get('surname')
    email = data.get('email')

    if not name or not surname or not email:
        return jsonify({"error": "All fields are required!"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()
        student_id = cursor.var(cx_Oracle.NUMBER)
        cursor.execute(
            "INSERT INTO STUDENTI (VARDS, UZVARDS, EPASTS) VALUES (:name, :surname, :email) RETURNING STUD_ID INTO :student_id",
            {"name": name, "surname": surname, "email": email, "student_id": student_id}
        )
        conn.commit()
        student_id = student_id.getvalue()[0]
        return jsonify({
            "success": True,
            "id": student_id,
            "message": "Student added successfully!"
        })
    except cx_Oracle.DatabaseError as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@pasn_bp.route('/delete_student', methods=['DELETE'])
def delete_student():
    data = request.json
    name = data.get('name')
    surname = data.get('surname')

    if not name or not surname:
        return jsonify({"error": "Name and surname are required!"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM STUDENTI WHERE VARDS = :1 AND UZVARDS = :2",
            (name, surname)
        )
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404

        return jsonify({"success": True, "message": "Student deleted successfully!"})
    except cx_Oracle.DatabaseError as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@pasn_bp.route('/edit_student', methods=['PUT'])
def edit_student():
    data = request.json
    student_id = data.get('id')
    name = data.get('name', '').strip()
    surname = data.get('surname', '').strip()
    email = data.get('email', '').strip()

    if not all([student_id, name, surname, email]):
        return jsonify({"error": "All fields are required!"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM STUDENTI WHERE STUD_ID = :1", (student_id,))
        exists = cursor.fetchone()[0]

        if not exists:
            return jsonify({"error": "Student not found"}), 404

        cursor.execute(
            """
            UPDATE STUDENTI
            SET VARDS = :1, UZVARDS = :2, EPASTS = :3
            WHERE STUD_ID = :4
            """,
            (name, surname, email, student_id)
        )
        conn.commit()

        return jsonify({"success": True, "message": "Student updated successfully!"})
    except cx_Oracle.DatabaseError as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
