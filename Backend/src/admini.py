from flask import Blueprint, render_template, jsonify, request
import cx_Oracle
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

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
def index():
    """Load the HTML page."""
    return render_template('admin_instructor_list.html')

@admin_bp.route('/get_admins', methods=['GET'])
def get_admins():
    """Fetch the list of instructors from the database."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT PASN_ID, VARDS, UZVARDS, EPASTS FROM PASNIEDZEJI")
        admins = [{"id": row[0], "name": row[1], "surname": row[2], "email": row[3]} for row in cursor]
        return jsonify(admins)
    except cx_Oracle.DatabaseError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@admin_bp.route('/add_instructor', methods=['POST'])
def add_instructor():
    """Add a new instructor to the database."""
    data = request.json
    name = data.get('name')
    surname = data.get('surname')
    email = data.get('email')

    # Validate input data
    if not name or not surname or not email:
        return jsonify({"error": "All fields are required!"}), 400

    # Get database connection
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()

        # Define a variable to hold the returned ID
        instructor_id = cursor.var(cx_Oracle.NUMBER)

        # Insert the new instructor and return the generated ID
        cursor.execute(
            "INSERT INTO PASNIEDZEJI (VARDS, UZVARDS, EPASTS) VALUES (:1, :2, :3) RETURNING PASN_ID INTO :4",
            (name, surname, email, instructor_id)
        )
        conn.commit()

        # Fetch the generated ID
        instructor_id = instructor_id.getvalue()[0]

        return jsonify({
            "success": True,
            "id": instructor_id,
            "message": "Instructor added successfully!"
        })
    except cx_Oracle.DatabaseError as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@admin_bp.route('/delete_instructor', methods=['DELETE'])
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
            "DELETE FROM PASNIEDZEJI WHERE VARDS = :1 AND UZVARDS = :2",
            (name, surname)
        )
        conn.commit()

        # Check if any row was deleted
        if cursor.rowcount == 0:
            return jsonify({"error": "Instructor not found"}), 404

        return jsonify({"success": True, "message": "Instructor deleted successfully!"})
    except cx_Oracle.DatabaseError as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@admin_bp.route('/edit_instructor', methods=['PUT'])
def edit_instructor():
    """Edit an existing instructor in the database."""
    data = request.json
    instructor_id = data.get('id')
    name = data.get('name', '').strip()
    surname = data.get('surname', '').strip()
    email = data.get('email', '').strip()

    # Check if any field is missing or empty
    if not all([instructor_id, name, surname, email]):
        return jsonify({"error": "All fields are required!"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Cannot connect to the database"}), 500

    try:
        cursor = conn.cursor()

        # Check if the instructor exists by ID
        cursor.execute("SELECT COUNT(*) FROM PASNIEDZEJI WHERE PASN_ID = :1", (instructor_id,))
        exists = cursor.fetchone()[0]

        if not exists:
            return jsonify({"error": "Instructor not found"}), 404

        # Update the instructor based on ID
        cursor.execute(
            """
            UPDATE PASNIEDZEJI
            SET VARDS = :1, UZVARDS = :2, EPASTS = :3
            WHERE PASN_ID = :4
            """,
            (name, surname, email, instructor_id)
        )
        conn.commit()

        return jsonify({"success": True, "message": "Instructor updated successfully!"})
    except cx_Oracle.DatabaseError as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
