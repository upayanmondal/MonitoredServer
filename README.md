# MonitoredServer

**A Role-Based Project and Task Management System built with FastAPI and PostgreSQL.**

MonitoredServer is a backend-driven project and task management application designed to simulate a business environment. It provides role-based access control, project and group management, task assignment, account management, and file operations through REST APIs and a web-based frontend.

## Features

- **Authentication and Account Management**
  - User registration and login
  - JWT-based authentication
  - Account management and access restrictions

- **User and Group Management**
  - Admin-controlled user management
  - Group creation and management
  - Manager assignment

- **Project Management**
  - Project creation and assignment
  - Project status management
  - Archive and restore functionality
  - Group-based project organization

- **Task Management**
  - Task creation and assignment
  - Task status and priority management
  - Developer task tracking
  - Task progress monitoring

- **Dashboard**
  - Project overview
  - Task progress visibility
  - Group and project information

- **File Management**
  - User-specific file listing
  - File downloading
  - File deletion

## Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Authentication | JWT |
| Frontend | HTML, CSS, JavaScript |
| API Communication | REST API, Fetch API |
| Server | Uvicorn |

## Project Structure

```text
MonitoredServer/
│
├── admin/
│   └── admin_routes.py
│
├── business/
│   ├── business_routes.py
│   └── task_routes.py
│
├── frontend/
│   ├── index.html
│   ├── dashboard.html
│   ├── tasks.html
│   ├── admin.html
│   ├── style.css
│   ├── app.js
│   ├── dashboard.js
│   ├── tasks.js
│   └── admin.js
│
├── main.py
├── database.py
├── models.py
├── auth.py
├── dependencies.py
├── account.py
├── list_files.py
├── detele_file.py
├── download.py
├── requirements.txt
└── README.md
```

## User Roles

| Role | Responsibilities |
|---|---|
| Admin | Manages users, groups, projects, and administrative operations. |
| Manager | Oversees assigned groups and monitors project progress. |
| Tech Lead | Creates tasks, assigns them to developers, and manages task status and priority. |
| Developer | Receives assigned tasks and manages assigned work. |

## Getting Started

### 1. Prerequisites

Install the following:

- Python
- PostgreSQL
- pip
- A modern web browser

### 2. Clone the Repository

```bash
git clone https://github.com/upayanmondal/MonitoredServer.git
cd MonitoredServer
```

### 3. Create a Virtual Environment

```bash
python -m venv v_env
```

Activate it:

**Windows**
```bash
v_env\Scripts\activate
```

**Linux / macOS**
```bash
source v_env/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure the Database

Open `database.py` and update the PostgreSQL connection URL with your own database credentials.

Create a PostgreSQL database named `monitored_server`, or update the connection URL to use another database.

### 6. Configure the JWT Secret

Open `auth.py` and replace the placeholder secret key with your own strong, unique secret.

### 7. Run the Backend

From the project root directory, execute:

```bash
uvicorn main:app --host 0.0.0.0 --port 12345
```

The backend will be available at:

```text
http://127.0.0.1:12345
```

### 8. Access API Documentation

FastAPI provides interactive API documentation at:

```text
http://127.0.0.1:12345/docs
```

### 9. Run the Frontend

Open the `frontend` directory using a local development server, such as VS Code Live Server.

The frontend uses the following API base URL:

```javascript
const API_BASE_URL = "http://127.0.0.1:12345";
```

Update this value in the frontend JavaScript files if your backend uses a different address or port.

## Security Notes

- Replace all placeholder credentials and secret keys before running the application.
- Do not publish database passwords, private credentials, or real secret keys.
- Do not commit virtual environments or local configuration files.
- Configure appropriate CORS restrictions before deploying the application.

## Future Improvements

- Enhanced monitoring and reporting
- More detailed activity tracking
- Additional administrative controls
- Improved dashboard functionality

## Author

**Upayan Mondal**

B.Tech in Information Technology

- [LinkedIn](https://linkedin.com/in/upayan-mondal-3b9235247)
- [LeetCode](https://leetcode.com/u/Upayan_Mondal/)

---

MonitoredServer is an independent project demonstrating backend development, REST API design, authentication, role-based access control, database management, and frontend-backend integration.
