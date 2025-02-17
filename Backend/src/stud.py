from flask import Flask, jsonify, Blueprint, render_template
import cx_Oracle

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
    """Load the HTML page."""
    return render_template('Students_page.html')

# API, lai iegūtu visus rakstus no RAKSTI tabulas
@stud_bp.route('/get-papers', methods=['GET'])
def get_papers():
    conn = get_db_connection()
    if conn is None:
        print("ERROR: Database connection failed!")  # Debugging log
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        print("Executing query...")  # Debugging log
        cursor.execute("SELECT RAKSTANR, NOSAUKUMS, STUDENTUGRUPA, STUD_ID FROM RAKSTI")

        papers = []
        for row in cursor:
            papers.append({
                "id": row[0],
                "title": row[1],
                "group": row[2],
                "student_id": row[3]
            })
        
        print("Data retrieved:", papers)  # Debugging log
        return jsonify({"papers": papers})
    
    except cx_Oracle.DatabaseError as e:
        print("Query error:", e)  # Debugging log
        return jsonify({"error": "Database query failed"}), 500
    
    finally:
        cursor.close()
        conn.close()

# Flask app initialization
app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)