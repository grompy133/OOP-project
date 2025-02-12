from flask import Flask, Blueprint, render_template, jsonify, request
import cx_Oracle

# Datu bāzes savienojuma parametri
DB_USERNAME = 'C##sistema'
DB_PASSWORD = '=dAb21Jm09'
DB_DSN = 'localhost:1521/ORCL'

# Funkcija savienošanai ar datu bāzi
def get_db_connection():
    try:
        return cx_Oracle.connect(user=DB_USERNAME, password=DB_PASSWORD, dsn=DB_DSN)
    except cx_Oracle.DatabaseError as e:
        print("Savienošanas kļūda:", e)
        return None
    
pasn_bp = Blueprint('pasniedzejs', __name__)

@pasn_bp.route('/')
def index():
    """Ielādē HTML lapu ar pasniedzēja profila informāciju."""
    conn = get_db_connection()
    if conn is None:
        return "Nevar izveidot savienojumu ar datu bāzi", 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE FROM PASNIEDZEJI WHERE PASN_ID = 1")
        pasn_data = cursor.fetchone()
        
        if pasn_data:
            pasniedzejs = {
                "name": pasn_data[0],
                "surname": pasn_data[1],
                "username": pasn_data[2],
                "email": pasn_data[3],
                "password": pasn_data[4]
            }
        else:
            pasniedzejs = None
    
        return render_template('teacher_page.html', pasniedzejs=pasniedzejs)
    except cx_Oracle.DatabaseError as e:
        return f"Kļūda: {str(e)}", 500
    finally:
        cursor.close()
        conn.close()

@pasn_bp.route('/get_students', methods=['GET'])
def get_students():
    """Fetch the list of students from the database."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT STUDENTA_ID, VARDS, UZVARDS, EPASTS, STUDENTA_ID FROM STUDENTI")
        students = [{"id": row[0], "name": row[1], "surname": row[2], "email": row[3], "studentID": row[4]} for row in cursor]
        return jsonify(students)
    except cx_Oracle.DatabaseError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@pasn_bp.route('/add_student', methods=['POST'])
def add_student():
    """Add a new student to the database."""
    data = request.json
    name = data.get('name')
    surname = data.get('surname')
    email = data.get('email')
    studentID = data.get('studentID')

    # Validate input data
    if not name or not surname or not email or not studentID:
        return jsonify({"error": "All fields are required!"}), 400

    # Get database connection
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()

        # Define a variable to hold the returned ID
        student_id = cursor.var(cx_Oracle.NUMBER)

        # Insert the new student and return the generated ID
        cursor.execute(
            "INSERT INTO STUDENTI (VARDS, UZVARDS, EPASTS, STUD_ID) VALUES (:1, :2, :3, :4) RETURNING STUDENTA_ID INTO :5",
            (name, surname, email, studentID, student_id)
        )
        conn.commit()

        # Fetch the generated ID
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

if __name__ == '__main__':
    pasn_bp.run(debug=True)
