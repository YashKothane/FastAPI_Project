from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import bcrypt
from enum import IntEnum

# Assuming these are imported from your other files
from models import Usermodel
from db import engine, User

app = FastAPI()

# ==========================================
# JWT & SECURITY CONFIGURATION
# ==========================================
SECRET_KEY = "my_super_secret_key_for_jwt" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- Password Helpers (bcrypt) ---
def get_password_hash(password: str):
    pwd_bytes = password.encode('utf-8')
    if len(pwd_bytes) > 72:
        raise HTTPException(status_code=400, detail="Password too long.")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    pwd_bytes = plain_password.encode('utf-8')
    if len(pwd_bytes) > 72:
        return False
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))
    except (ValueError, TypeError):
        return False

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- Database Dependency ---
def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


# ==========================================
# ENUMERATED ROLES (The Integer Mapping)
# ==========================================
class Role(IntEnum):
    ADMIN = 1
    MANAGER = 2
    USER = 3


# ==========================================
# 1. CORE AUTH DEPENDENCY (Upgraded)
# ==========================================
# We upgraded this to fetch the actual User object from the database, 
# not just the email string. This allows us to check their role!
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    # Query the database for the user
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
        
    # Return the entire user object
    return user


# ==========================================
# 2. ROLE CHECKER DEPENDENCY (Integer Version)
# ==========================================
class RoleChecker:
    """
    Checks if the user's integer role matches our allowed Enums.
    """
    def __init__(self, allowed_roles: list):
        self.allowed_roles = [role.value for role in allowed_roles]

    def __call__(self, user: User = Depends(get_current_user)):
        # user.role is an integer in the database (e.g., 1, 2, or 3)
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Operation not permitted. You do not have the required role level."
            )
        return user


# Instantiate our role locks using the readable Enums!
allow_admin_only = RoleChecker([Role.ADMIN])
allow_admin_and_manager = RoleChecker([Role.ADMIN, Role.MANAGER])


# ==========================================
# 3. ENDPOINTS
# ==========================================

@app.post("/registration", status_code=status.HTTP_201_CREATED)
def user_register(user_details: Usermodel):
    
    # 1. Hash the password using raw bcrypt (with length check)
    pwd_bytes = user_details.password.encode('utf-8')
    if len(pwd_bytes) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is too long. Maximum length is 72 bytes."
        )
    # Generate salt and hash, then decode back to a string for the database
    hashed_pw = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode('utf-8')

    # 2. Manually open the session
    db = Session(engine)
    try:
        # Check for duplicates first
        existing_user = db.query(User).filter(User.email == user_details.email.lower()).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user and assign the integer role!
        new_user = User(
            email=user_details.email.lower(),
            firstname=user_details.firstname,
            lastname=user_details.lastname,
            password=hashed_pw,
            phone=user_details.phone,
            role=Role.USER.value  # Assigns the integer 3 automatically
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "message": "User registered successfully!", 
            "user_id": new_user.id,
            "assigned_role_id": new_user.role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback() 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Database error: {str(e)}"
        )
    finally:
        db.close()


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# --- STANDARD PROTECTED ROUTE (Any logged-in user) ---
@app.get("/my_profile")
def get_my_profile(current_user: User = Depends(get_current_user)):
    # We can cast the integer back to a string name for the frontend if we want
    role_name = Role(current_user.role).name
    return {"message": "You are logged in!", "your_role_id": current_user.role, "role_name": role_name}


# --- ADMIN ONLY ROUTE ---
# Notice we added the `allow_admin_only` dependency!
@app.delete("/delete_all_users")
def delete_everything(current_user: User = Depends(allow_admin_only)):
    return {"message": f"Hello Admin {current_user.firstname}, executing deletion..."}


# --- ADMIN OR MANAGER ROUTE ---
@app.get("/view_reports")
def view_financial_reports(current_user: User = Depends(allow_admin_and_manager)):
    return {"message": f"Welcome {current_user.firstname}. Here are the reports."}