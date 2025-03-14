import hashlib # lai varētu paroli hash
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import oracledb
import os
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, BadSignature
from admini import admin_bp
from pasniedzejs import pasn_bp
from stud import stud_bp

app = Flask(
    __name__,
    template_folder=os.path.abspath('../../Frontend/src/Pages'),  # Veidņu mape
    static_folder=os.path.abspath('../../Frontend/src/Styles')    # Statisko failu mape
)
app.secret_key = 'your_secret_key'

app.config['MAIL_SERVER'] = 'mail.inbox.lv'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'vangogilicock123@inbox.lv'  # Our email
app.config['MAIL_PASSWORD'] = '7P92BrGysP'  # Our password
app.config['MAIL_DEFAULT_SENDER'] = 'vangogilicock123@inbox.lv'
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

mail = Mail(app)

# Database connection parameters
DB_USERNAME = 'ADMIN'
DB_PASSWORD = 'msu8nTwIkf6isAR5qBmp'
DB_DSN = "v9n3ba1erzl8nuba_high"
DB_WALLET_PASSWORD = "dR3kQd8utf5jLyqRyeFx"
#DB_WALLET_LOCATION = r"C:\\Users\\Boris\\Desktop\\Wallet_V9N3BA1ERZL8NUBA"
DB_WALLET_LOCATION = r"D:\\SYSTEM_FOLDERS\\Downloads\\Wallet_V9N3BA1ERZL8NUBA"
#6

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
    
def generate_reset_token(user_id, user_type):
    # Create a dictionary to hold the user_id and user_type
    data = {
        'user_id': user_id,
        'user_type': user_type
    }

    # Serialize the data dictionary into a token
    return serializer.dumps(data, salt='password-reset')

def verify_reset_token(token, expiration=3600):
    
    try:
        # Load the data from the token
        data = serializer.loads(token, salt='password-reset', max_age=expiration)
        # Extract email and user_type from the data
        user_id = data.get('user_id')
        user_type = data.get('user_type')
        
        # Ensure the email and user_type are valid
        if user_id and user_type:
            return user_id, user_type
        else:
            return None, None
    except (BadSignature, TypeError):
        return None, None
        
# E-pasta sūtīšanas funkcija
def send_email(to_email, subject, body):
    msg = Message(subject, recipients=[to_email])
    msg.html = body

    try:
        mail.send(msg)
    except Exception as e:
        print(f"Kļūda, sūtot e-pastu: {e}")   

# Funkcija paroles šifrēšanai ar SHA-256
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
    
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
    try:
        email_or_username = request.form.get('email_or_username')
        password = request.form.get('password')
        user = User.authenticate(email_or_username, password)  # Authenticate user

        if user:
            session['user_id'] = user.user_id  # Store user ID in session
            session['user_type'] = user.user_type  # Store user type
            print(f"Session after login: user_id={session['user_id']}, user_type={session['user_type']}")  # Debugging

            # Send JSON response with redirect URL instead of redirecting in Flask
            if user.user_type == 'administrators':
                return jsonify({"success": True, "redirect_url": url_for('admin_page')})
            elif user.user_type == 'pasniedzējs':
                return jsonify({"success": True, "redirect_url": url_for('teacher_page')})
            elif user.user_type == 'students':
                return jsonify({"success": True, "redirect_url": url_for('student_page')})

        # If authentication fails
        print("Authentication failed: Invalid username or password")  # Debugging
        return jsonify({"success": False, "message": "Wrong email or password"}), 401

    except Exception as e:
        print(f"Error in /login route: {e}")  # Print the actual error for debugging
        return jsonify({"success": False, "message": "Internal server error"}), 500

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
                        "id": user_id,
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
                """, (user_id,))
                user_data = cursor.fetchone()
                
                if user_data:
                    students = {
                        "id": user_id,
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
                        "id": user_id,
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

# --- PASSWORD RESET FUNCTIONALITY ---
@app.route('/update_password', methods=['POST'])
def update_password():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "User not authenticated"}), 401

    data = request.get_json()
    new_password = data.get('new_password')
    token = data.get('token')  # Token is optional
    if not new_password:
        return jsonify({"success": False, "message": "New password is required"}), 400
    
    if token:
        user_id, user_type = verify_reset_token(token)
        if not user_id:
            return jsonify({"success": False, "message": "Invalid or expired token"}), 400
    else:
        user_id = session['user_id']
        user_type = session['user_type']
        if 'user_id' not in session:
            return jsonify({"success": False, "message": "User not authenticated"}), 401

    hashed_password = hash_password(new_password)
    table_map = {
        'students': 'STUDENTI',
        'pasniedzējs': 'PASNIEDZEJI',
        'administrators': 'ADMINISTRATORS'
    }

    if user_type not in table_map:
        return jsonify({"success": False, "message": "Invalid user type"}), 400

    table_name = table_map[user_type]

    if table_name == "ADMINISTRATORS":
        id_column = "ADMIN_ID"  
    elif table_name == "PASNIEDZEJI":
        id_column = "PASN_ID"
    elif table_name == "STUDENTI":
        id_column = "STUD_ID"

    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        
        query = f"UPDATE {table_name} SET PAROLE = :1 WHERE {id_column} = :2"
        print(query + '. Password: ' + str(new_password) + ' . User ID: ' + str(user_id) + ' . User type: ' + str(user_type))
        cursor.execute(query, (hashed_password, user_id))
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "No rows updated. Check user_id."}), 400

        return jsonify({"success": True, "message": "Password updated successfully"})
    
    finally:
        cursor.close()  
        connection.close()

@app.route('/tologin')
def toLogin():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear() #notīra datus no sesijas
    return redirect(url_for('index')) #pāradrese uz sākumlapu

@app.route('/parole')
def parole():
        return render_template('paroles_atjau.html')
    # To enter register new admin page, add to the link http://127.0.0.1:5000/register_new_admin
@app.route('/register_new_admin')
def register_new_admin():
    return render_template('Register_new_admin.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        # Get data from the request
        data = request.get_json()

        # Extract values
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Validate data
        if not password or not username or not email:
            return jsonify({'Can not get from the request username/email/password'}), 400

        # Hash the password before saving
        hashed_password = hash_password(password)

        # Connect to the database
        connection = get_db_connection()
        if not connection:
            return jsonify({'errors': ["Neizdevās savienoties ar datu bāzi."]}), 500

        try:
            cursor = connection.cursor()
            sql = """
                INSERT INTO ADMINISTRATORS (LIETOTAJVARDS, EPASTS, PAROLE)
                VALUES (:1, :2, :3)
            """
            cursor.execute(sql, [username, email, hashed_password])
            connection.commit()

            select_created_admin = """
                SELECT ADMIN_ID FROM ADMINISTRATORS WHERE EPASTS=:1 AND LIETOTAJVARDS=:2
            """
            cursor.execute(select_created_admin, [email, username])

            user_id= cursor.fetchone()[0]

            reset_token = generate_reset_token(user_id, 'administrators')
            reset_link = url_for('reset_password_page', token=reset_token, _external=True)

            # Prepare the email content
            subject = "Uzaicinājums lietot sistēmu"
            body = f"""
                Hello, {username}!<br><br>
                You have been invited to use our system. <br>
                To start, please click the link bellow: <br> <a href="{reset_link}">{reset_link}</a>.<br><br>
                If you have any questions, please contact us.
                """

            # Send invitation email
            send_email(email, subject, body)

            return jsonify({'message': f"Administrator {username} is successfully registered! An invitation email has been sent to {email}."}), 200

        except cx_Oracle.DatabaseError as e:
            return jsonify({'errors': [f"Error: {str(e)}"]}), 500

        finally:
            connection.close()

    except Exception as e:
        return jsonify({'errors': [str(e)]}), 500
    

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_page(token):
    # logic to verify token and allow password reset
    return render_template('new_password.html', token=token)

@app.route('/send-reset-email', methods=['POST'])
def send_reset_email():
    email = request.json.get('email')
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT 'students' AS user_type, STUD_ID AS user_id FROM STUDENTI WHERE EPASTS = :1
                UNION
                SELECT 'pasniedzējs' AS user_type, PASN_ID AS user_id FROM PASNIEDZEJI WHERE EPASTS = :1
                UNION
                SELECT 'administrators' AS user_type, ADMIN_ID AS user_id FROM ADMINISTRATORS WHERE EPASTS = :1
            """, (email,))
            user_data = cursor.fetchone()
            
            if user_data:
                user_type = user_data[0]
                user_id = user_data[1]

                reset_token = generate_reset_token(user_id, user_type)
                reset_link = url_for('reset_password_page', token=reset_token, _external=True)

                subject = 'Password Reset Request'
                body=f"Please click the link below to reset your password: <br> {reset_link}"
                
                send_email(email, subject, body)
                
                return jsonify({"success": True, "message": "A password reset email has been sent to your email."})
            else:
                return jsonify({"success": False, "message": "Email not found."})
        
        finally:
            cursor.close()
            connection.close()
    
    return jsonify({"success": False, "message": "Failed to check email in the database."})

@app.route('/send_invitation', methods=['POST'])
def send_invitation():
    email = request.json.get('email')
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT 'students' AS user_type, STUD_ID AS user_id FROM STUDENTI WHERE EPASTS = :1
                UNION
                SELECT 'pasniedzējs' AS user_type, PASN_ID AS user_id FROM PASNIEDZEJI WHERE EPASTS = :1
                UNION
                SELECT 'administrators' AS user_type, ADMIN_ID AS user_id FROM ADMINISTRATORS WHERE EPASTS = :1
            """, (email,))
            user_data = cursor.fetchone()
            
            if user_data:
                user_type = user_data[0]
                user_id = user_data[1]

                reset_token = generate_reset_token(user_id, user_type)
                reset_link = url_for('reset_password_page', token=reset_token, _external=True)

                subject = "Uzaicinājums lietot sistēmu"
                body = f"""
                    Hello!<br><br>
                    You have been invited to use our system. <br>
                    To start, please click the link bellow: <br> <a href="{reset_link}">{reset_link}</a>.<br><br>
                    If you have any questions, please contact us.
                    """
                
                send_email(email, subject, body)
                
                return jsonify({"success": True, "message": "Invitation email sent successfully!"})
            else:
                return jsonify({"success": False, "message": "Email not found."})
        
        finally:
            cursor.close()
            connection.close()
    
    return jsonify({"success": False, "message": "Failed to check email in the database."})


if __name__ == '__main__':
    app.run(debug=True)
