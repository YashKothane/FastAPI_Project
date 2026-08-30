import os
from datetime import datetime, timedelta, timezone
from enum import IntEnum

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from db import engine, User
from models import SignupRequest, LoginResponse, UserOut

from rate_limit import check_and_increment_login_attempts, reset_login_attempts
load_dotenv()

from db import engine, User, Blog
from models import SignupRequest, LoginResponse, UserOut, BlogCreate, BlogUpdate, BlogOut

app = FastAPI(title="Fare Compare API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Create a .env file with SECRET_KEY=...")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class Role(IntEnum):
    ADMIN = 1
    MANAGER = 2
    USER = 3


# ---------- password + token helpers ----------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


# ---------- auth dependencies ----------

from user_cache import get_cached_user, set_cached_user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired, please log in again")
    except jwt.PyJWTError:
        raise credentials_exception

    # 1. Try the cache first
    cached = get_cached_user(email)
    if cached:
        return User(**cached)  # rebuild a User-like object from cached dict

    # 2. Cache miss — go to the database
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    # 3. Store it for next time
    set_cached_user(email, {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "password": user.password,
        "role": user.role,
    })

    return user

class RoleChecker:
    def __init__(self, allowed_roles: list[Role]):
        self.allowed_roles = [r.value for r in allowed_roles]

    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission for this action.",
            )
        return user


allow_admin_only = RoleChecker([Role.ADMIN])
allow_admin_and_manager = RoleChecker([Role.ADMIN, Role.MANAGER])


# ---------- endpoints ----------

@app.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email.lower(),
        password=hash_password(payload.password),
        role=Role.USER.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    check_and_increment_login_attempts(form_data.username)

    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    reset_login_attempts(form_data.username)

    token = create_access_token(user.email)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/my_profile", response_model=UserOut)
def my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/admin/stats")
def admin_stats(current_user: User = Depends(allow_admin_only)):
    return {"message": f"Welcome Admin {current_user.name}, here are the stats."}


@app.get("/reports")
def reports(current_user: User = Depends(allow_admin_and_manager)):
    return {"message": f"Welcome {current_user.name}, here are the reports."}


def blog_to_out(blog: Blog) -> BlogOut:
    return BlogOut(
        id=blog.id,
        title=blog.title,
        content=blog.content,
        author_id=blog.author_id,
        author_name=blog.author.name,
        created_at=blog.created_at,
        updated_at=blog.updated_at,
    )


@app.post("/blogs", response_model=BlogOut, status_code=status.HTTP_201_CREATED)
def create_blog(
    payload: BlogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    blog = Blog(
        title=payload.title,
        content=payload.content,
        author_id=current_user.id,
    )
    db.add(blog)
    db.commit()
    db.refresh(blog)
    return blog_to_out(blog)


@app.get("/blogs", response_model=list[BlogOut])
def list_blogs(db: Session = Depends(get_db)):
    blogs = db.query(Blog).order_by(Blog.created_at.desc()).all()
    return [blog_to_out(b) for b in blogs]


@app.get("/blogs/{blog_id}", response_model=BlogOut)
def get_blog(blog_id: int, db: Session = Depends(get_db)):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return blog_to_out(blog)


@app.put("/blogs/{blog_id}", response_model=BlogOut)
def update_blog(
    blog_id: int,
    payload: BlogUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    if blog.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own blogs")

    blog.title = payload.title
    blog.content = payload.content
    db.commit()
    db.refresh(blog)
    return blog_to_out(blog)


@app.delete("/blogs/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(
    blog_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    if blog.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own blogs")

    db.delete(blog)
    db.commit()