back-end/
│── app/                     # Main application package
│   ├── __init__.py          # Initializes the app as a package
│   ├── api/                 # API endpoints
│   │   ├── __init__.py      
│   │   ├── routes.py        # Route definitions
│   │   ├── controllers.py   # Handles requests and responses
│   ├── models/             
│   │   ├── __init__.py
│   │   ├── login.py
│   │   ├── new_user.py
│   │   ├── admini.py
│   │   ├── pasniedzejs.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── auth_service.py
│   ├── core/                # Core settings & configurations
│   │   ├── config.py        # App configuration
│   │   ├── database.py      # DB connection setup
│   ├── utils/               # Utility functions
│   │   ├── __init__.py
│   │   ├── hash.py          # Password hashing
│   │   ├── jwt.py           # JWT handling
│   ├── middlewares/         # Custom middleware (e.g., logging, authentication)
│   ├── main.py              # Entry point (FastAPI/Flask app)
│── tests/                   # Unit & integration tests
│── migrations/              # Database migrations (Alembic)
│── .env                     # Environment variables
│── requirements.txt         # Dependencies
│── Dockerfile               # Docker configuration
│── README1.md                # Documentation
