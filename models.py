from pydantic import BaseModel, EmailStr
from typing import Optional

class Usermodel(BaseModel):
    firstname: str
    lastname:str
    email: str
    password:str
    phone:int
 
