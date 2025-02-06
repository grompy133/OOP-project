from flask import Flask, render_template, jsonify, request
import cx_Oracle

app = Flask(__name__)

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

@app.route('/')
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

if __name__ == '__main__':
    app.run(debug=True)
