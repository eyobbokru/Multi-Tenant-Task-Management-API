# Task Management API

A modern, scalable RESTful API service for task management built with FastAPI and PostgreSQL.

## Features

- 🔐 Secure authentication with JWT
- 👥 User and team management
- 📋 Task creation and assignment
- 🏢 Workspace organization
- 📊 Time tracking and reporting
- 🔍 Advanced task filtering and search
- 📝 Comment system with mentions
- 📨 Real-time notifications
- 🔄 Audit logging
- 📈 Performance monitoring

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migration**: Alembic
- **Caching**: Redis
- **Authentication**: JWT
- **Documentation**: OpenAPI (Swagger)
- **Testing**: Pytest
- **Container**: Docker
- **CI/CD**: GitHub Actions

## Prerequisites

- Python 3.12
- PostgreSQL 15+
- Redis 6+
- Docker & Docker Compose (optional)

## Local Development Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/task-management-api.git
cd task-management-api
```

2. Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configurations
```

5. Run database migrations:

```bash
alembic upgrade head
```

6. Start the development server:

```bash
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## Docker Setup

1. Build and start the containers:

```bash
docker-compose up -d --build
```

2. Run migrations:

```bash
docker-compose exec api alembic upgrade head
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, you can access:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
task_management_api/
├── alembic/                    # Database migrations
├── app/
│   ├── api/                    # API routes
│   ├── core/                   # Core functionality
│   ├── db/                     # Database
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/              # Business logic
│   └── utils/                 # Utility functions
├── tests/                     # Tests
└── [other configuration files]
```

## Testing

Run the test suite:

```bash
pytest
```

With coverage:

```bash
pytest --cov=app tests/
```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Create a Pull Request

## Environment Variables

Required environment variables:

```
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=task_management
SECRET_KEY=your-secret-key
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin
```

See `.env.example` for all available configurations.

## API Endpoints

### Authentication

- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout

### Users

- GET /api/v1/users/
- POST /api/v1/users/
- GET /api/v1/users/{user_id}
- PUT /api/v1/users/{user_id}
- DELETE /api/v1/users/{user_id}

### Tasks

- GET /api/v1/tasks/
- POST /api/v1/tasks/
- GET /api/v1/tasks/{task_id}
- PUT /api/v1/tasks/{task_id}
- DELETE /api/v1/tasks/{task_id}

[View complete API documentation in Swagger UI]

## Acknowledgments

- FastAPI documentation
- SQLAlchemy documentation
- PostgreSQL documentation
- All contributors who have helped with code and documentation
