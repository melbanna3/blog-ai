from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, field_validator
from typing import List, Optional
from enum import Enum
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from os import getenv
from dotenv import load_dotenv

# Load environment variables
load_dotenv()  # Add at the top of main.py
# Database setup
DATABASE_URL = getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy models
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class CategoryDB(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

class PostDB(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

class CommentDB(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

# Create tables
Base.metadata.drop_all(bind=engine)  # Drop existing tables to avoid schema conflicts
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str

class CategoryCreate(BaseModel):
    name: str

    @field_validator("name")
    def check_non_empty(cls, value):
        if not value.strip():
            raise ValueError("Field cannot be empty")
        return value

class Category(BaseModel):
    id: int
    name: str

class PostCreate(BaseModel):
    title: str
    content: str
    category_id: Optional[int] = None  # Optional category

    @field_validator("title", "content")
    def check_non_empty(cls, value):
        if not value.strip():
            raise ValueError("Field cannot be empty")
        return value

class Post(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    author_id: int
    category_id: Optional[int]

class CommentCreate(BaseModel):
    content: str

    @field_validator("content")
    def check_non_empty(cls, value):
        if not value.strip():
            raise ValueError("Comment cannot be empty")
        return value

class Comment(BaseModel):
    id: int
    content: str
    created_at: datetime
    post_id: int
    author_id: int

# JWT setup
SECRET_KEY = getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db: Session, username: str):
    return db.query(UserDB).filter(UserDB.username == username).first()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user

# Endpoints
@app.post("/users", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    db_user = UserDB(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/categories", response_model=Category)
def create_category(category: CategoryCreate, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    db_category = db.query(CategoryDB).filter(CategoryDB.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="Category already exists")
    db_category = CategoryDB(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.get("/categories", response_model=List[Category])
def get_categories(db: Session = Depends(get_db)):
    return db.query(CategoryDB).all()

@app.post("/posts", response_model=Post)
def create_post(post: PostCreate, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    if post.category_id:
        category = db.query(CategoryDB).filter(CategoryDB.id == post.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    db_post = PostDB(title=post.title, content=post.content, author_id=current_user.id, category_id=post.category_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.get("/posts", response_model=List[Post])
def get_posts(category_id: Optional[int] = None, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(PostDB).filter(PostDB.author_id == current_user.id)
    if category_id:
        query = query.filter(PostDB.category_id == category_id)
    return query.all()

@app.get("/posts/{post_id}", response_model=Post)
def get_post(post_id: int, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(PostDB).filter(PostDB.id == post_id, PostDB.author_id == current_user.id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@app.put("/posts/{post_id}", response_model=Post)
def update_post(post_id: int, updated_post: PostCreate, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    db_post = db.query(PostDB).filter(PostDB.id == post_id, PostDB.author_id == current_user.id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if updated_post.category_id:
        category = db.query(CategoryDB).filter(CategoryDB.id == updated_post.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    db_post.title = updated_post.title
    db_post.content = updated_post.content
    db_post.category_id = updated_post.category_id
    db.commit()
    db.refresh(db_post)
    return db_post

@app.delete("/posts/{post_id}")
def delete_post(post_id: int, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    db_post = db.query(PostDB).filter(PostDB.id == post_id, PostDB.author_id == current_user.id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(db_post)
    db.commit()
    return {"message": "Post deleted"}

@app.post("/posts/{post_id}/comments", response_model=Comment)
def create_comment(post_id: int, comment: CommentCreate, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(PostDB).filter(PostDB.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db_comment = CommentDB(content=comment.content, post_id=post_id, author_id=current_user.id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@app.get("/posts/{post_id}/comments", response_model=List[Comment])
def get_comments(post_id: int, db: Session = Depends(get_db)):
    post = db.query(PostDB).filter(PostDB.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return db.query(CommentDB).filter(CommentDB.post_id == post_id).all()