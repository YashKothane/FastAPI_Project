from fastapi import FastAPI
from models import Usermodel
from db import engine
from sqlalchemy.orm import Session 
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from fastapi import FastAPI, HTTPException, status

from passlib.context import CryptContext
# This is used for hashing out the password

from db import User
from datetime import timedelta, timezone
from fastapi import APIRouter
from jose import jwt,JWTError