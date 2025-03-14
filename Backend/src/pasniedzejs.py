from flask import Blueprint, render_template, jsonify, request, send_file
import pandas as pd
import io
import random
import oracledb

# Database connection details
DB_USERNAME = 'ADMIN'
DB_PASSWORD = 'msu8nTwIkf6isAR5qBmp'
DB_DSN = "v9n3ba1erzl8nuba_high"
DB_WALLET_PASSWORD = "dR3kQd8utf5jLyqRyeFx"
DB_WALLET_LOCATION = r"../../Wallet_V9N3BA1ERZL8NUBA"

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
    if 'files' not in request.files:
        return jsonify({"error": "No file part"}), 400

    files = request.files.getlist('files')
    if not files or all(file.filename == '' for file in files):
        return jsonify({"error": "No selected files"}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Cannot connect to the database"}), 500

        cursor = conn.cursor()
        results = []

        for file in files:
            if file and file.filename.endswith('.pdf'):
                file_content = file.read()

                # Generate a new RAKSTANR
                cursor.execute("SELECT RAKSTI_SEQ.NEXTVAL FROM DUAL")
                raksta_nr = cursor.fetchone()[0]

                # Insert the file into the RAKSTI table
                cursor.execute(
                    "INSERT INTO RAKSTI (RAKSTANR, FILE_NAME, FILES) VALUES (:1, :2, :3)",
                    (raksta_nr, file.filename, file_content)
                )
                results.append({
                    "id": raksta_nr,
                    "title": file.filename,
                    "student_name": "No student assigned"
                })

        conn.commit()
        return jsonify({
            "success": True,
            "message": "PDFs uploaded successfully!",
            "files": results  # Atgriežam masīvu ar failiem
        })
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
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

@pasn_bp.route('/add-seminar', methods=['POST'])
def add_seminar():
    data = request.get_json()
    seminar_name = data.get("name")

    if not seminar_name:
        return jsonify({"success": False, "message": "Seminar name is required"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()

        # Check if a seminar with the same name already exists
        cursor.execute("SELECT COUNT(*) FROM SEMINARI WHERE NOSAUKUMS = :seminar_name", {"seminar_name": seminar_name})
        count = cursor.fetchone()[0]
        if count > 0:
            return jsonify({"success": False, "message": "Seminar already exists."}), 409

        # If not, insert the new seminar and return the new seminar ID
        seminar_id = cursor.var(cx_Oracle.NUMBER)
        cursor.execute(
            "INSERT INTO SEMINARI (NOSAUKUMS) VALUES (:seminar_name) RETURNING SEMINARANR INTO :seminar_id", 
            {"seminar_name": seminar_name, "seminar_id": seminar_id}
        )
        conn.commit()
        new_seminar_id = seminar_id.getvalue()[0]
        return jsonify({"success": True, "id": new_seminar_id, "message": "Seminar added successfully"})

    except cx_Oracle.DatabaseError as e:
        conn.rollback()
        error_message = str(e)
        print(f"Database error: {error_message}")
        return jsonify({"success": False, "message": "Database query failed", "error": error_message}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@pasn_bp.route('/get_seminar', methods=['GET'])
def get_seminar():
    """Fetch the list of seminars from the database."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SEMINARANR, NOSAUKUMS FROM SEMINARI")
        seminars = [{"id": row[0], "name": row[1]} for row in cursor]
        return jsonify(seminars)
    except cx_Oracle.DatabaseError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@pasn_bp.route('/get-seminar-papers/<int:seminar_nr>', methods=['GET'])
def get_seminar_papers(seminar_nr):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT R.RAKSTANR, R.FILE_NAME, G.NOSAUKUMS AS STUDENTUGRUPA, S.VARDS, S.UZVARDS
            FROM RAKSTI R
            JOIN STUDENTI S ON R.STUD_ID = S.STUD_ID
            JOIN GRUPA G ON S.GRUPA_ID = G.GRUPA_ID
            JOIN SEMINARI_RAKSTI SR ON R.RAKSTANR = SR.RAKSTANR
            WHERE SR.SEMINARANR = :seminar_nr
        """, {"seminar_nr": seminar_nr})

        papers = []
        for row in cursor.fetchall():
            student_name = f"{row[3]} {row[4]}" if row[3] else "No student assigned"
            papers.append({
                "id": row[0],
                "title": row[1],
                "group": row[2],
                "student_name": student_name
            })

        return jsonify({"papers": papers})

    except cx_Oracle.DatabaseError as e:
        print("Database error:", e)
        return jsonify({"error": "Database query failed"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@pasn_bp.route('/export_students', methods=['GET'])
def export_students():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT VARDS, UZVARDS, EPASTS FROM STUDENTI")
        students = cursor.fetchall()

        # Convert the data to a pandas DataFrame
        df = pd.DataFrame(students, columns=['Vārds', 'Uzvārds', 'E-pasts'])

        # Create an in-memory buffer to store the Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Students')

        # Seek to the beginning of the stream
        output.seek(0)

        # Return the Excel file as a response
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='students.xlsx'
        )

    except cx_Oracle.DatabaseError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# 1. Saglabā komandas un piešķir studentus
@pasn_bp.route('/register_teams/<int:seminar_nr>', methods=['POST'])
def register_teams(seminar_nr):
    # Pārbauda, vai seminar_nr ir saņemts
    if not seminar_nr:
        return jsonify({"error": "Seminar number (seminar_nr) is missing"}), 400

    # Pārbauda, vai seminar_nr ir skaitlis
    if not isinstance(seminar_nr, int):
        return jsonify({"error": "Seminar number (seminar_nr) must be an integer"}), 400

    # Ielogojam saņemto seminar_nr
    print(f"Received seminar_nr: {seminar_nr}")  # Atkļūdošanas ziņojums

    data = request.json
    teams = data.get('teams', [])

    if not teams:
        return jsonify({"error": "No teams provided"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()

    try:
        # Pārbauda, vai SEMINARANR eksistē SEMINARI tabulā
        cursor.execute("SELECT COUNT(*) FROM SEMINARI WHERE SEMINARANR = :seminar_nr", {"seminar_nr": seminar_nr})
        seminar_exists = cursor.fetchone()[0]

        if seminar_exists == 0:
            return jsonify({"error": f"Seminar with SEMINARANR {seminar_nr} does not exist"}), 400

        # Ielogojam esošās grupas
        cursor.execute("SELECT GRUPA_ID FROM GRUPA WHERE SEMINARANR = :seminar_nr ORDER BY GRUPA_ID", {"seminar_nr": seminar_nr})
        existing_grupa_ids = [row[0] for row in cursor.fetchall()]
        print(f"Existing GRUPA_IDs for seminar_nr {seminar_nr}: {existing_grupa_ids}")  # Atkļūdošanas ziņojums

        # Iegūstam maksimālo GRUPA_ID
        cursor.execute("SELECT NVL(MAX(GRUPA_ID), 0) FROM GRUPA")
        max_grupa_id = cursor.fetchone()[0]
        print(f"Max GRUPA_ID for seminar_nr {seminar_nr}: {max_grupa_id}")  # Atkļūdošanas ziņojums

        for i, team_name in enumerate(teams):
            if i < len(existing_grupa_ids):
                # Atjaunina esošo grupu
                cursor.execute("""
                    UPDATE GRUPA 
                    SET NOSAUKUMS = :team_name 
                    WHERE GRUPA_ID = :grupa_id AND SEMINARANR = :seminar_nr
                """, {"team_name": team_name, "grupa_id": existing_grupa_ids[i], "seminar_nr": seminar_nr})
            else:
                # Pievieno jaunu grupu
                max_grupa_id += 1
                cursor.execute("""
                    INSERT INTO GRUPA (GRUPA_ID, NOSAUKUMS, SEMINARANR) 
                    VALUES (:grupa_id, :team_name, :seminar_nr)
                """, {"grupa_id": max_grupa_id, "team_name": team_name, "seminar_nr": seminar_nr})

        conn.commit()

               # Atjaunina studentus, kuriem ir raksti seminārā
        cursor.execute("""
            SELECT DISTINCT S.STUD_ID
            FROM STUDENTI S
            JOIN RAKSTI R ON S.STUD_ID = R.STUD_ID
            JOIN SEMINARI_RAKSTI SR ON R.RAKSTANR = SR.RAKSTANR
            WHERE SR.SEMINARANR = :seminar_nr
        """, {"seminar_nr": seminar_nr})

        student_ids_with_papers = [row[0] for row in cursor.fetchall()]
        print(f"Students with papers in seminar {seminar_nr}: {student_ids_with_papers}")  # Atkļūdošanas ziņojums

        if student_ids_with_papers:
            random.shuffle(student_ids_with_papers)
            cursor.execute("""
                SELECT GRUPA_ID FROM GRUPA WHERE SEMINARANR = :seminar_nr ORDER BY GRUPA_ID
            """, {"seminar_nr": seminar_nr})
            grupa_ids = [row[0] for row in cursor.fetchall()]
            print(f"GRUPA_IDs for seminar_nr {seminar_nr}: {grupa_ids}")  # Atkļūdošanas ziņojums

            for i, student_id in enumerate(student_ids_with_papers):
                assigned_team = grupa_ids[i % len(grupa_ids)]
                cursor.execute("""
                    UPDATE STUDENTI 
                    SET GRUPA_ID = :grupa_id 
                    WHERE STUD_ID = :student_id
                """, {"grupa_id": assigned_team, "student_id": student_id})

        conn.commit()
        return jsonify({"message": "Teams updated and students assigned"})

    except cx_Oracle.DatabaseError as e:
        conn.rollback()
        error_message = f"Database error: {e}"
        print(error_message)  # Atkļūdošanas ziņojums
        return jsonify({"error": "Database operation failed", "details": error_message}), 500
    except Exception as e:
        conn.rollback()
        error_message = f"Unexpected error: {e}"
        print(error_message)  # Atkļūdošanas ziņojums
        return jsonify({"error": "An unexpected error occurred", "details": error_message}), 500
    finally:
        cursor.close()
        conn.close()

@pasn_bp.route('/edit_profile', methods=['PUT'])
def edit_profile():
    """Edit an existing profile in the database."""
    data = request.json  
    print(data)

    # Extract and clean up data
    pasn_id = data.get('pasn-id')
    name = data.get('name', '').strip()
    surname = data.get('surname', '').strip()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()

        # Check if the instructor exists by ID
        cursor.execute("SELECT COUNT(*) FROM PASNIEDZEJI WHERE PASN_ID = :1", (pasn_id,))
        exists = cursor.fetchone()[0]
        print(exists)

        if not exists:
            return jsonify({"error": "Instructor not found"}), 404

        # Update the instructor's data in the database
        cursor.execute(
            """
            UPDATE PASNIEDZEJI
            SET VARDS = :1, UZVARDS = :2, LIETOTAJVARDS = :3, EPASTS = :4
            WHERE PASN_ID = :5
            """,
            (name, surname, username, email, pasn_id)
        )
        conn.commit()

        return jsonify({"success": True, "message": "Instructor updated successfully!"})

    except cx_Oracle.DatabaseError as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@pasn_bp.route('/parole')
def parole():
        return render_template('new_password.html')


@pasn_bp.route('/get-student-groups', methods=['GET'])
def get_student_groups():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT G.GRUPA_ID, G.NOSAUKUMS, S.STUD_ID, S.VARDS, S.UZVARDS
            FROM GRUPA G
            LEFT JOIN STUDENTI S ON G.GRUPA_ID = S.GRUPA_ID
            ORDER BY G.GRUPA_ID
        """)
        
        groups_dict = {}
        for row in cursor.fetchall():
            group_id, group_name, student_id, student_name, student_surname = row
            if group_id not in groups_dict:
                groups_dict[group_id] = {
                    "id": group_id,
                    "name": group_name,
                    "students": []
                }
            if student_id:
                groups_dict[group_id]["students"].append({
                    "id": student_id,
                    "name": f"{student_name} {student_surname}"
                })

        result = list(groups_dict.values())
        print("DEBUG API RESPONSE:", result)  # <--- Pievieno šo, lai redzētu API atbildi

        return jsonify(result)

    except cx_Oracle.DatabaseError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@pasn_bp.route('/update-student-group', methods=['POST'])
def update_student_group():
    try:
        data = request.get_json()
        print("DEBUG: Received data:", data)

        if not data:
            return jsonify({"error": "No data received"}), 400

        student_id = data.get('studentId')
        new_group = data.get('newGroup')

        if student_id is None or new_group is None:
            return jsonify({"error": "studentId or newGroup missing"}), 400

        try:
            student_id = int(student_id)
            new_group = int(new_group)
        except ValueError:
            return jsonify({"error": "studentId and newGroup must be numbers"}), 400

        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()
        try:
            print(f"DEBUG: Updating student {student_id} with group {new_group}")

            cursor.execute("""
                UPDATE STUDENTI
                SET GRUPA_ID = :group_id
                WHERE STUD_ID = :student_id
            """, {"group_id": new_group, "student_id": student_id})

            if cursor.rowcount == 0:
                return jsonify({"error": "Student not found"}), 404

            conn.commit()
            return jsonify({"success": True, "message": "Student group updated successfully!"})
        except cx_Oracle.DatabaseError as e:
            conn.rollback()
            print("DEBUG: Database error:", str(e))
            return jsonify({"error": str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print("DEBUG: Unexpected error:", str(e))
        return jsonify({"error": str(e)}), 500
