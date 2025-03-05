from flask import Flask, request, render_template, send_from_directory
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import string
import oracledb

app = Flask(__name__)
app.secret_key = 'your_secret_key'

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

# Funkcija paroles šifrēšanai ar SHA-256
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# E-pasta sūtīšanas funkcija
def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        print("E-pasts veiksmīgi nosūtīts!")
    except Exception as e:
        print(f"Kļūda, sūtot e-pastu: {e}")

# Unikālas saites ģenerēšana
def generate_activation_link(username, email):
    token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    activation_link = f"http://yourserver.com/activate?username={username}&email={email}&token={token}"
    return activation_link

# E-pasta satura sagatavošana
def prepare_email_content(username, email):
    activation_link = generate_activation_link(username, email)
    subject = "Uzaicinājums lietot sistēmu"
    body = f"""
    <html>
        <body>
            <h2>Sveicināti, {username}!</h2>
            <p>Jūs esat uzaicināts lietot mūsu sistēmu. Lai sāktu, lūdzu, noklikšķiniet uz šīs saites:</p>
            <p><a href="{activation_link}">{activation_link}</a></p>
            <p>Ja jums ir kādi jautājumi, lūdzu, sazinieties ar mums.</p>
            <p>Ar cieņu,<br>Jūsu sistēmas administrācija</p>
        </body>
    </html>
    """
    return subject, body

# Flask maršrutētāji
@app.route('/')
def index():
    return render_template('Register_new_admin.html')

@app.route('/styles.css')
def styles():
    return send_from_directory(app.static_folder, 'styles_register.css')

@app.route('/register', methods=['POST'])
def register():
    # Iegūstam datus no formas
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    # Pārbaudām, vai visi lauki ir aizpildīti
    if not username or not email or not password:
        return "<p style='color:red;'>Visi lauki ir obligāti!</p> <a href='/'>Atgriezties</a>"

    # Šifrējam paroli pirms saglabāšanas datubāzē
    hashed_password = hash_password(password)

    # Savienojamies ar datu bāzi
    connection = get_db_connection()
    if not connection:
        return "<p style='color:red;'>Neizdevās savienoties ar datu bāzi.</p> <a href='/'>Atgriezties</a>"

    try:
        with connection.cursor() as cursor:
            # Izveidojam SQL vaicājumu ar parametriem
            sql = """
                INSERT INTO ADMINISTRATORS (LIETOTAJVARDS, EPASTS, PAROLE)
                VALUES (:1, :2, :3)
            """
            # Izpildām vaicājumu
            cursor.execute(sql, [username, email, hashed_password])
            connection.commit()

            # Nosūtām e-pastu ar uzaicinājumu
            subject, body = prepare_email_content(username, email)
            send_email(email, subject, body)

            # Atgriežam veiksmīgu ziņojumu
            return f"<script>alert('Administrators \"{username}\" veiksmīgi reģistrēts! E-pasts ar uzaicinājumu nosūtīts uz {email}.'); window.location.href='/';</script>"
    except cx_Oracle.DatabaseError as e:
        # Ja rodas kļūda, atgriežam kļūdas ziņojumu
        return f"<p style='color:red;'>Kļūda: {str(e)}</p> <a href='/'>Atgriezties</a>"
    finally:
        # Aizveram savienojumu
        connection.close()

@app.route('/activate')
def activate():
    username = request.args.get('username')
    email = request.args.get('email')
    token = request.args.get('token')

    # Pārbaudiet tokenu un veiciet nepieciešamās darbības
    # Piemēram, atzīmējiet lietotāju kā aktivizētu datu bāzē

    return f"<p>Lietotājs {username} ar e-pastu {email} veiksmīgi aktivizēts!</p>"

if __name__ == '__main__':
    app.run(debug=True)