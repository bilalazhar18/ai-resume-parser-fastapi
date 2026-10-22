# AI Resume Parser API

A Python backend that extracts structured information from PDF resumes using Google Gemini. Built with FastAPI, it also includes persistent user CRUD, password hashing, and JWT authentication through HTTP-only cookies.

This project demonstrates REST API development, Pydantic validation, SQLAlchemy database integration, external AI service integration, and authentication. It is a backend API; use its interactive documentation or an HTTP client to explore it.

## Project preview

Upload a PDF resume through the interactive Swagger UI. The API extracts its text and returns resume data as JSON.

![Swagger UI showing the PDF upload form for POST /resume/parse-resume](images/resume%20parser%20api.png)

## Features

- **AI resume parsing:** Upload a text-based PDF and extract contact details, skills, work experience, and education into a JSON object.
- **Upload validation:** Reject non-PDF filenames, empty files, unreadable PDFs, and files larger than 2 MiB.
- **User management:** Register, list, retrieve, update, and delete users stored in SQLite, with duplicate-email handling.
- **Authentication:** Validate login credentials, issue an HS256 JWT in an HTTP-only cookie, and clear the cookie on logout.
- **Password security:** Hash new passwords with Argon2 and verify existing bcrypt hashes using `pwdlib`.
- **API documentation:** Explore request schemas and endpoints through Swagger UI and ReDoc.
- **Validation example:** A small product endpoint demonstrates typed JSON request handling without database persistence.

## How resume parsing works

![Six-step resume parsing workflow from the client request through FastAPI and Gemini to the JSON response](images/overflow%20chart%20of%20parser1.png)

FastAPI validates the upload and extracts PDF text before constructing the Gemini prompt. The service decodes the AI response into a Python dictionary and returns it as JSON.

The PDF is processed in memory. Extracted resume text is sent to Google Gemini, so use sample or consented data when trying the service. Parsed resumes are returned to the caller and are not saved to SQLite. Scanned, image-only resumes require OCR, which is not implemented.

### Example result

The screenshot below shows an HTTP `200` response with extracted contact details and skills from a resume.

![Swagger UI displaying a successful resume parsing response with extracted fields and skills](images/parse%20reusme%20json%20object.png)

The prompt requests the following structure. This is an illustrative response, not a guarantee of schema validation: the service currently checks that Gemini returns a valid JSON object.

```json
{
  "name": "Alex Morgan",
  "email": "alex@example.com",
  "phone": null,
  "skills": ["Python", "FastAPI", "SQLAlchemy"],
  "work_experience": [
    {"company": "Example Company", "role": "Backend Developer", "duration": "2024–2025"}
  ],
  "education": [
    {"institution": "Example University", "degree": "BS Computer Science", "year": "2024"}
  ]
}
```

## Run locally

Use Python 3.10 or newer. A Gemini API key and network access are required for resume parsing. User and product endpoints do not require a Gemini key.

Run these commands from the project root after cloning the repository.

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure Gemini

Create a `.env` file in the project root:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
# Optional: override the model name used by the service.
# GEMINI_MODEL=your_available_model_id
```

`GEMINI_API_KEY` is required for parsing. `GEMINI_MODEL` is optional; the current code defaults to `gemini-3.5-flash-lite`. Select a model available to your Gemini account if needed. Keep `.env` out of version control.

### 4. Initialize the local database

The application uses `app.db` in the project root. It does not create tables automatically on startup. For a fresh checkout, initialize the users table with:

```bash
python -c "from app.database import Base, engine; from app.models.user import User; Base.metadata.create_all(bind=engine)"
```

This creates missing tables and preserves existing data. It does not migrate an existing schema.

### 5. Start the server

```bash
python -m uvicorn main:app --reload
```

| URL | Purpose |
| --- | --- |
| `http://127.0.0.1:8000/` | API status message |
| `http://127.0.0.1:8000/docs` | Interactive Swagger UI |
| `http://127.0.0.1:8000/redoc` | ReDoc reference |
| `http://127.0.0.1:8000/openapi.json` | OpenAPI schema |

The login cookie has `Secure=True`, so use HTTPS when testing cookie authentication reliably. The command above serves local HTTP and is sufficient for registration, CRUD, and resume parsing.

## API endpoints

| Method | Path | Purpose | Request |
| --- | --- | --- | --- |
| `GET` | `/` | Check that the API is running | None |
| `POST` | `/users` | Register a user | JSON: `name`, `email`, `password` |
| `POST` | `/users/login` | Set the authentication cookie | Form: `username` (email), `password` |
| `POST` | `/users/logout` | Clear the authentication cookie | None |
| `GET` | `/users` | List users | None |
| `GET` | `/users/{user_id}` | Retrieve a user | Integer path parameter |
| `PUT` | `/users/{user_id}` | Update a user | JSON: `name`, `email`, optional `password` |
| `DELETE` | `/users/{user_id}` | Delete a user | Integer path parameter |
| `GET` | `/users/me` | Intended current-user endpoint; see current limitations | Authentication cookie |
| `POST` | `/resume/parse-resume` | Parse a PDF resume | Multipart field: `file` |
| `POST` | `/products` | Validate and echo product data | JSON: `name`, `price`, `color` |

User responses contain `id`, `name`, and `email`; password hashes are excluded. User CRUD, product creation, and resume parsing currently have no authentication requirement.

<details>
<summary>View the user endpoints in Swagger UI</summary>

![Swagger UI listing registration, login, logout, current-user, and user CRUD endpoints](images/capstone%20project.png)

This screenshot shows the registered endpoints. See the current limitations below for the `/users/me` routing issue and remaining authorization work.

</details>

### Try the API

In Swagger UI, expand `POST /users`, select **Try it out**, and submit:

```json
{
  "name": "Alex Morgan",
  "email": "alex@example.com",
  "password": "a-long-example-password"
}
```

For login, submit the email as the form field `username`. The response sets an `access_token` cookie; it does not return the JWT in the JSON body.

To parse a resume with curl, use the following command (`curl.exe` in Windows PowerShell):

```bash
curl -X POST http://127.0.0.1:8000/resume/parse-resume -F "file=@resume.pdf"
```

Upload errors return `400`, oversized files return `413`, missing Gemini configuration returns `503`, and upstream request or AI response errors return `502`.

## Project structure

```text
.
├── main.py                    # FastAPI application and router registration
├── requirements.txt           # Direct Python dependencies
├── app/
│   ├── database.py            # SQLite engine, SQLAlchemy base, session factory
│   ├── session.py             # Database session dependency
│   ├── security.py            # Password hashing and JWT helpers
│   ├── crud/users.py          # User persistence and duplicate-email handling
│   ├── models/user.py         # SQLAlchemy users table
│   ├── routes/                # User, resume, and product endpoints
│   ├── schemas/               # Pydantic data models
│   └── services/gemini_parser.py  # Gemini prompting and JSON response handling
└── tests/                     # Password tests and database/migration test files
```

<details>
<summary>View the authentication concepts diagram</summary>

![Conceptual diagram connecting an API to database schemas, operations, password hashing, JWT authorization, and session cookies](images/API%20Security%20Architecture%20Diagram.png)

This diagram summarizes the concepts behind the user module. The implementation uses Argon2 password hashing and JWT authentication through an HTTP-only cookie. Authorization checks for user CRUD remain a next step.

</details>

<details>
<summary>View the application layers through a banking analogy</summary>

![Banking analogy illustrating the roles of models, schemas, CRUD, security, and application setup](images/Secure%20Banking%20API%20Workflow%20Infographic.png)

This is a learning illustration of how application layers divide responsibilities. In this repository, those responsibilities live in `app/models/`, `app/schemas/`, `app/crud/`, `app/security.py`, and `main.py`. It illustrates code organization; the application implements resume parsing and user management.

</details>

## Tests

Run the password regression tests:

```bash
python -m unittest discover -s tests -p test_security.py -v
```

These cover correct and incorrect passwords, long Unicode passwords, and existing bcrypt hashes. The database and migration test files reference a missing `migrate.py`, and the migration tests also import a missing `hash_password` helper. Full test discovery needs those inconsistencies resolved first.

## Current limitations and next steps

This is a portfolio and learning project with implemented API features and several remaining deployment tasks:

- **Current-user route:** Move `/users/me` above `GET /users/{user_id}`. Its current order makes `/users/me` match the integer user-ID route and return a validation error.
- **Authorization:** Add authentication and ownership or role checks to user CRUD and decide which other endpoints require login.
- **JWT configuration:** Replace the hardcoded signing key with an environment-managed secret. Login currently uses the helper's 15-minute token lifetime while the cookie lasts 30 minutes; align these values.
- **Logout:** Cookie deletion ends the browser session; copied JWTs remain usable until expiry because server-side revocation is not implemented.
- **Cookie security:** Add CSRF protection for authenticated state-changing requests and configure HTTPS for cookie-based login.
- **Database migrations:** Restore a working Alembic setup and repair the database/migration tests.
- **AI output:** Validate extracted fields with a response schema and add parser tests with mocked Gemini responses.
- **Deployment:** Hosting on Render is a next step; this repository currently includes no Render deployment configuration. A deployment needs HTTPS, managed secrets, and persistent storage for SQLite or a hosted database.

