# Blog API
A RESTful API for managing blog posts, categories, and comments, built with FastAPI, PostgreSQL, and JWT authentication.

## Endpoints
- **Users**:
  - `POST /users`: Register a user.
  - `POST /token`: Login to get a JWT.
- **Categories**:
  - `POST /categories`: Create a category (authenticated).
  - `GET /categories`: List all categories.
- **Posts**:
  - `POST /posts`: Create a post (with optional category).
  - `GET /posts?category_id={id}`: List user’s posts, filter by category.
  - `GET /posts/{id}`: Fetch a post by ID.
  - `PUT /posts/{id}`: Update a post.
  - `DELETE /posts/{id}`: Delete a post.
- **Comments**:
  - `POST /posts/{id}/comments`: Add a comment to a post (authenticated).
  - `GET /posts/{id}/comments`: List comments for a post.

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
- Tables:
  - `users`: `id`, `username`, `hashed_password`
  - `categories`: `id`, `name`
  - `posts`: `id`, `title`, `content`, `created_at`, `author_id`, `category_id`
  - `comments`: `id`, `content`, `created_at`, `post_id`, `author_id`

## Testing
- Use curl: `curl -X POST "http://127.0.0.1:8000/token" -d "username=mahmoud&password=securepassword"`.
- Use Postman: Send requests with JSON bodies and Bearer tokens.
- Visit `http://127.0.0.1:8000/docs` for interactive docs.