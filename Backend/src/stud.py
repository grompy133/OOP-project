from flask import Flask, jsonify, Blueprint, render_template, request
import cx_Oracle
from flask import session

# Datu bāzes savienojuma detaļas
DB_USERNAME = 'C##sistema'
DB_PASSWORD = '=dAb21Jm09'
DB_DSN = 'localhost:1521/ORCL'

# Funkcija, lai izveidotu savienojumu ar datu bāzi
def get_db_connection():
    try:
        conn = cx_Oracle.connect(user=DB_USERNAME, password=DB_PASSWORD, dsn=DB_DSN)
        print("Savienojums ar datu bāzi veiksmīgi izveidots!")
        return conn
    except cx_Oracle.DatabaseError as e:
        print("Datu bāzes savienojuma kļūda:", e)
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

if __name__ == '__main__':
    stud_bp.run(debug=True)
