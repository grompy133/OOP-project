import hashlib # lai varētu paroli hash
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import cx_Oracle
import oracledb
import os
from admini import admin_bp
from pasniedzejs import pasn_bp
from stud import stud_bp

app = Flask(
    __name__,
    template_folder=os.path.abspath('../../Frontend/src/Pages'),  # Veidņu mape
    static_folder=os.path.abspath('../../Frontend/src/Styles')    # Statisko failu mape
)
app.secret_key = 'your_secret_key'

# Database connection parameters
DB_USERNAME = 'ADMIN'
DB_PASSWORD = 'msu8nTwIkf6isAR5qBmp'
DB_DSN = "v9n3ba1erzl8nuba_high"
DB_WALLET_PASSWORD = "dR3kQd8utf5jLyqRyeFx"
DB_WALLET_LOCATION = r"C:\\Users\\Boris\\Desktop\\Wallet_V9N3BA1ERZL8NUBA"

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
    
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(pasn_bp, url_prefix='/pasniedzejs')
app.register_blueprint(stud_bp, url_prefix='/students')

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
                """, (email_or_username,)*6)
                
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
    email_or_username = request.form.get('email_or_username')
    password = request.form.get('password')

    user = User.authenticate(email_or_username, password)  # Authenticate the user

    if user:
        session['user_id'] = user.user_id  # Store the user's ID in the session
        session['user_type'] = user.user_type  # Store the user's type in the session
        print(f"Session after login: user_id={session['user_id']}, user_type={session['user_type']}")  # Debugging

        if user.user_type == 'administrators':
            return redirect(url_for('admin_page'))  # Redirect to admin page
        elif user.user_type == 'pasniedzējs':
            return redirect(url_for('teacher_page'))  # Redirect to teacher page
        elif user.user_type == 'students':
            return redirect(url_for('student_page'))  # Redirect to student page

    return jsonify({"success": False, "message": "Nepareizs lietotājvārds vai parole"}), 401

@app.route('/teacher_page')
def teacher_page():
    if session.get('user_type') == 'pasniedzējs':  # Ensure the user is a teacher
        user_id = session.get('user_id')  # Get the logged-in teacher's ID from the session
        print(f"Fetching data for teacher with ID: {user_id}")  # Debugging

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                # Fetch the teacher's data from the database
                cursor.execute("""
                    SELECT VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE
                    FROM PASNIEDZEJI WHERE PASN_ID = :1
                """, (user_id,))
                user_data = cursor.fetchone()
                print(f"Fetched teacher data: {user_data}")  # Debugging
                
                if user_data:
                    # Create a dictionary with the teacher's data
                    pasniedzejs = {
                        "name": user_data[0],
                        "surname": user_data[1],
                        "username": user_data[2],
                        "email": user_data[3],
                        "password": user_data[4]
                    }
                    # Render the template with the teacher's data
                    return render_template('teacher_page.html', pasniedzejs=pasniedzejs)
                else:
                    return "Teacher data not found", 404
            finally:
                cursor.close()
                connection.close()
    
    return redirect(url_for('index'))  # Redirect to the login page if the user is not a teacher

@app.route('/student_page')
def student_page():
    if session.get('user_type') == 'students':  # Tikai studentiem
        user_id = session.get('user_id')
        connection = get_db_connection()
        
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                    SELECT VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE
                    FROM STUDENTI WHERE STUD_ID = :1
                """, (int(user_id),))
                user_data = cursor.fetchone()
                
                if user_data:
                    students = {
                        "name": user_data[0],
                        "surname": user_data[1],
                        "username": user_data[2],
                        "email": user_data[3],
                        "password": user_data[4]
                    }
                    return render_template('Students_page.html', students=students)
            finally:
                cursor.close()
                connection.close()
    
    return redirect(url_for('index'))  # Ja nav students, sūta atpakaļ uz sākumlapu

@app.route('/admin_page')
def admin_page():
    if session.get('user_type') == 'administrators':  # Tikai administratoriem
        user_id = session.get('user_id')
        connection = get_db_connection()
        
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                    SELECT VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE
                    FROM ADMINISTRATORS WHERE ADMIN_ID = :1
                """, (user_id,))
                user_data = cursor.fetchone()
                
                if user_data:
                    admin = {
                        "name": user_data[0],
                        "surname": user_data[1],
                        "username": user_data[2],
                        "email": user_data[3],
                        "password": user_data[4]
                    }
                    return render_template('admin_instructor_list.html', admin=admin)
            finally:
                cursor.close()
                connection.close()
    
    return redirect(url_for('index'))  # Ja nav administrators, sūta atpakaļ uz sākumlapu

@app.route('/password_reset')
def password_reset():
    return render_template('paroles_atjau.html')

@app.route('/logout')
def logout():
    session.clear() #notīra datus no sesijas
    return redirect(url_for('index')) #pāradrese uz sākumlapu

if __name__ == '__main__':
    app.run(debug=True)
