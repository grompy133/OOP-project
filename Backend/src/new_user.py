from flask import Flask, request, jsonify, render_template, url_for
import hashlib
import cx_Oracle
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, BadSignature
import os


app = Flask(
    __name__,
    template_folder=os.path.abspath('../../Frontend/src/Pages'),  # Veidņu mape
    static_folder=os.path.abspath('../../Frontend/src/Styles')    # Statisko failu mape
)
app.secret_key = 'your_secret_key'

# Mail configuration
app.config['MAIL_SERVER'] = 'mail.inbox.lv'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'vangogilicock123@inbox.lv'  # Your email
app.config['MAIL_PASSWORD'] = '7P92BrGysP'  # Your password
app.config['MAIL_DEFAULT_SENDER'] = 'vangogilicock123@inbox.lv'
mail = Mail(app)

# Datu bāzes savienojuma parametri
DB_USERNAME = 'SYS'
DB_PASSWORD = 'mypassword1'
DB_DSN = 'localhost:1521/ORCLCDB'

# Funkcija savienošanai ar datu bāzi
def get_db_connection():
    try:
        connection = cx_Oracle.connect(user=DB_USERNAME, password=DB_PASSWORD, dsn=DB_DSN, mode=cx_Oracle.SYSDBA)
        return connection
    except cx_Oracle.DatabaseError as e:
        print("Savienošanas kļūda:", e)
        return None

# Funkcija paroles šifrēšanai ar SHA-256
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# E-pasta sūtīšanas funkcija
def send_email(to_email, subject, body):
    msg = Message(subject, recipients=[to_email])
    msg.html = body

    try:
        mail.send(msg)
    except Exception as e:
        print(f"Kļūda, sūtot e-pastu: {e}")


# Flask maršrutētāji
@app.route('/')
def index():
    return render_template('Register_new_admin.html')

@app.route('/tologin')
def toLogin():
    return render_template('login.html')

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


            # Generate activation link
            login_link = url_for('toLogin', _external=True)

            # Prepare the email content
            subject = "Uzaicinājums lietot sistēmu"
            body = f"""
                Sveicināti, {email}!<br><br>
                Your credentials are: username={username} and password={password}
                Jūs esat uzaicināts lietot mūsu sistēmu. <br>
                Lai sāktu, lūdzu, noklikšķiniet uz šīs saites: <a href="{login_link}">{login_link}</a>.<br><br>
                Ja jums ir kādi jautājumi, lūdzu, sazinieties ar mums.
                """

            # Send invitation email
            send_email(email, subject, body)

            return jsonify({'message': f"Administrators {username} veiksmīgi reģistrēts! E-pasts ar uzaicinājumu nosūtīts uz {email}."}), 200

        except cx_Oracle.DatabaseError as e:
            return jsonify({'errors': [f"Kļūda: {str(e)}"]}), 500

        finally:
            connection.close()

    except Exception as e:
        return jsonify({'errors': [str(e)]}), 500


@app.route('/activate')
def activate():
    token = request.args.get('token')

    if not token:
        return "<p>Token nav atrasts!</p>", 400

    try:
        # Decrypt the token
        serializer = URLSafeTimedSerializer(app.secret_key)
        user_info = serializer.loads(token, salt='email-activation-salt', max_age=3600)  # Max age of 1 hour
        username, email = user_info

        # Perform the necessary actions, like updating the user as active in your DB
        # For example, update the user status in the database to "active"

        return f"<p>Lietotājs {username} ar e-pastu {email} veiksmīgi aktivizēts!</p>"

    except BadSignature:
        return "<p>Nepareizs vai beidzies token!</p>", 400
    except Exception as e:
        return f"<p>Kļūda: {str(e)}</p>", 500
    

if __name__ == '__main__':
    app.run(debug=True)
