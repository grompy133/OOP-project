from flask import Blueprint, render_template, jsonify, request, send_file
import cx_Oracle
import pandas as pd
import io

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
def delete_instructor():
    """Delete an instructor from the database by name and surname."""
    data = request.json
    print("Received data:", data)  # Add this line to check if data is coming through correctly
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

        # Check if any row was deleted
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
    """Edit an existing instructor in the database."""
    data = request.json
    student_id = data.get('id')
    name = data.get('name', '').strip()
    surname = data.get('surname', '').strip()
    email = data.get('email', '').strip()

    # Check if any field is missing or empty
    if not all([name, surname, email]):
        return jsonify({"error": "All fields are required!"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()
        # Check if the instructor exists by ID
        cursor.execute("SELECT COUNT(*) FROM STUDENTI WHERE STUD_ID = :1", (student_id,))
        exists = cursor.fetchone()[0]

        if not exists:
            return jsonify({"error": "Student not found"}), 404

        # Update the instructor based on ID
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

@pasn_bp.route('/import_students', methods=['POST'])
def import_students():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.xlsx'):
        conn = None
        cursor = None
        try:
            df = pd.read_excel(file)
            conn = get_db_connection()
            if conn is None:
                return jsonify({"error": "Cannot connect to the database"}), 500

            cursor = conn.cursor()
            for index, row in df.iterrows():
                cursor.execute(
                    "INSERT INTO STUDENTI (VARDS, UZVARDS, EPASTS) VALUES (:1, :2, :3)",
                    (row['Vards'], row['Uzvards'], row['Epasts'])
                )
            conn.commit()
            return jsonify({"success": True, "message": "Students imported successfully!"})
        except Exception as e:
            if conn:
                conn.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    else:
        return jsonify({"error": "Invalid file format. Please upload an Excel file."}), 400
    
@pasn_bp.route('/get-papers', methods=['GET'])
def get_papers():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT R.RAKSTANR, R.FILE_NAME, R.STUDENTUGRUPA, S.VARDS, S.UZVARDS
            FROM RAKSTI R
            LEFT JOIN STUDENTI S ON R.STUD_ID = S.STUD_ID
        """)
        
        papers = []
        for row in cursor:
            student_name = f"{row[3]} {row[4]}" if row[3] else "No student assigned"
            papers.append({
                "id": row[0],
                "title": row[1],
                "group": row[2],
                "student_name": student_name
            })
        
        return jsonify({"papers": papers})
    
    except cx_Oracle.DatabaseError as e:
        return jsonify({"error": "Database query failed"}), 500
    
    finally:
        cursor.close()
        conn.close()


@pasn_bp.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        print("No file part in request")  # Debug log
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if not file or file.filename == '':
        print("No file selected")  # Debug log
        return jsonify({"error": "No selected file"}), 400

    print("Received file:", file.filename, file.content_type, file.content_length)  # Debug log

    if file and file.filename.endswith('.pdf'):
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if conn is None:
                print("Failed to connect to the database")  # Debug log
                return jsonify({"error": "Cannot connect to the database"}), 500

            cursor = conn.cursor()
            file_content = file.read()

            # Generate a new RAKSTANR
            cursor.execute("SELECT RAKSTI_SEQ.NEXTVAL FROM DUAL")
            raksta_nr = cursor.fetchone()[0]
            print("Generated RAKSTANR:", raksta_nr)  # Debug log

            # Insert the file into the RAKSTI table
            cursor.execute(
                "INSERT INTO RAKSTI (RAKSTANR, FILE_NAME, FILES) VALUES (:1, :2, :3)",
                (raksta_nr, file.filename, file_content)
            )
            conn.commit()
            print("File inserted into database successfully")  # Debug log
            return jsonify({"success": True, "message": "PDF uploaded successfully!"})
        except Exception as e:
            print("Error during database operation:", str(e))  # Debug log
            if conn:
                conn.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    else:
        print("Invalid file format")  # Debug log
        return jsonify({"error": "Invalid file format. Please upload a PDF file."}), 400
    
@pasn_bp.route('/download_pdf', methods=['GET'])
def download_pdf():
    file_name = request.args.get('file_name')
    if not file_name:
        return jsonify({"error": "File name is required"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT FILES FROM RAKSTI WHERE FILE_NAME = :1", (file_name,))
        file_content = cursor.fetchone()[0]

        if not file_content:
            return jsonify({"error": "File not found"}), 404

        return send_file(
            io.BytesIO(file_content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=file_name
        )
    except cx_Oracle.DatabaseError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

