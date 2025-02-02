import hashlib # lai varētu paroli hash
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import cx_Oracle

app = Flask(__name__)
app.secret_key = 'your_secret_key'

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

# Lietotāja klase
class User:
    def __init__(self, user_id, vards, uzvards, lietotajvards, epasts, parole, user_type):
        self.user_id = user_id
        self.vards = vards
        self.uzvards = uzvards
        self.lietotajvards = lietotajvards
        self.epasts = epasts
        self.parole = parole.strip() # Noņem nevajadzīgās atstarpes
        self.user_type = user_type # Lietotāja tips (students, pasniedzējs, administrators)

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest() # Hashē paroli ar SHA-256

    @staticmethod
    def authenticate(email_or_username, password):
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                # Meklē lietotāju pēc e-pasta vai lietotājvārda visās lietotāju tabulās
                cursor.execute("""
                    SELECT PASN_ID, VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE, 'pasniedzējs' AS user_type 
                    FROM PASNIEDZEJI 
                    WHERE EPASTS = :1 OR LIETOTAJVARDS = :1
                    UNION
                    SELECT ADMIN_ID, VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE, 'administrators' AS user_type 
                    FROM ADMINISTRATORS 
                    WHERE EPASTS = :1 OR LIETOTAJVARDS = :1
                    UNION
                    SELECT STUD_ID, VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE, 'students' AS user_type 
                    FROM STUDENTI 
                    WHERE EPASTS = :1 OR LIETOTAJVARDS = :1
                """, (email_or_username,))
                
                user_data = cursor.fetchone() #iegūst pirmo atrasto lietotāju
                if user_data:
                    user = User(*user_data)#izveido lietotāja objektu
                    if user.parole == User.hash_password(password): #salīdzina paroli ar hash vērtībām
                        return user
            finally:
                cursor.close() #aizver kursoru
                connection.close() #aizver savienojum ar datu bāzi
        return None #ja neatrod lietotāju atgriež none

# Flask maršrutēšana
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email_or_username = request.form.get('email_or_username')  # Pieņem gan e-pastu vai lietotājvārdu no formas
    password = request.form.get('password') #iegūst paroli no formas

    user = User.authenticate(email_or_username, password) #mēģina autentificēt lietotāju

    if user:
        session['user_id'] = user.user_id # saglabā lietotāja ID sesijā
        session['user_type'] = user.user_type #saglabā lietotāja tipu sesijā

        if user.user_type == 'administrators':
            return redirect(url_for('admin_instructor_list')) #pāradresē pasniedzēju
        elif user.user_type == 'pasniedzējs':
            return redirect(url_for('teacher_page')) #pāradresē pasniedzēju
        elif user.user_type == 'students':
            return redirect(url_for('student_page')) #pāradresē studentu

    return jsonify({"success": False, "message": "Nepareizs lietotājvārds vai parole"}), 401

@app.route('/teacher_page')
def teacher_page():
    if session.get('user_type') == 'pasniedzējs': # Pārbauda, vai sesijā ir pasniedzējs
        return render_template('teacher_page.html')
    return redirect(url_for('index')) # Pāradresē uz sākumlapu, ja nav pasniedzējs

@app.route('/admin_instructor_list')
def admin_instructor_list():
    if session.get('user_type') == 'administrators': # Pārbauda, vai sesijā ir administrators
        return render_template('admin_instructor_list.html')
    return redirect(url_for('index')) # Pāradresē uz sākumlapu, ja nav administrators

@app.route('/student_page')
def student_page():
    if session.get('user_type') == 'students': # Pārbauda, vai sesijā ir students
        return render_template('student_page.html')
    return redirect(url_for('index')) # Pāradresē uz sākumlapu, ja nav students

@app.route('/password_reset')
def password_reset():
    return render_template('paroles_atjau.html')

@app.route('/logout')
def logout():
    session.clear() #notīra datus no sesijas
    return redirect(url_for('index')) #pāradrese uz sākumlapu

if __name__ == '__main__':
    app.run(debug=True)