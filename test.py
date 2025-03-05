import oracledb

DB_USERNAME = 'ADMIN'
DB_PASSWORD = 'msu8nTwIkf6isAR5qBmp'
DB_DSN = "v9n3ba1erzl8nuba_high"
DB_WALLET_PASSWORD="dR3kQd8utf5jLyqRyeFx"
DB_WALLET_LOCATION=r"D:\\SYSTEM_FOLDERS\\Downloads\\Wallet_V9N3BA1ERZL8NUBA"

connection = oracledb.connect(
    config_dir=DB_WALLET_LOCATION,
    user=DB_USERNAME,
    password=DB_PASSWORD,
    dsn=DB_DSN,
    wallet_location=DB_WALLET_LOCATION,
    wallet_password=DB_WALLET_PASSWORD
)

print("Connected successfully.")

try:
    cursor = connection.cursor()
    cursor.execute("SELECT RAKSTANR, FILE_NAME, STUD_ID FROM RAKSTI")

    papers = []
    for row in cursor:
        papers.append({
            "id": row[0],  # RAKSTANR
            "title": row[1],  # FILE_NAME
            "student_id": row[2]  # STUD_ID
        })

    print(papers)

except oracledb.DatabaseError as e:
    print("Database query failed")