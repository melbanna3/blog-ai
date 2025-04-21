# Blog API
A RESTful API for managing blog posts, built with FastAPI, PostgreSQL, and JWT authentication.

## Endpoints
- POST /users: Register a user.
- POST /token: Login to get a JWT.
- POST /posts: Create a post.
- GET /posts: List user’s posts.
- GET /posts/{id}: Fetch a post by ID.
- PUT /posts/{id}: Update a post.
- DELETE /posts/{id}: Delete a post.

## Setup
1. Install PostgreSQL: `brew install postgresql` (macOS) and start: `brew services start postgresql`.
2. Create database: `createdb blog`.
3. Install dependencies: `pip install -r requirements.txt`.
4. Run: `uvicorn main:app --reload`.

## Authentication
- Uses JWT for securing endpoints.
- Register via `POST /users`, login via `POST /token`, include `Authorization: Bearer <token>` in headers.

## Database
- PostgreSQL with SQLAlchemy.
- Tables: `users` (id, username, hashed_password), `posts` (id, title, content, created_at, author_id).

## Testing
- Use curl: `curl -X POST "http://127.0.0.1:8000/token" -d "username=mahmoud&password=securepassword"`.
- Use Postman: Send requests with JSON bodies and Bearer tokens.
- Visit `http://127.0.0.1:8000/docs` for interactive docs.