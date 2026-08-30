
import sys
from db import engine, User
from sqlalchemy.orm import Session

from user_cache import invalidate_cached_user

def set_role(email: str, role: int):
    with Session(engine) as db:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user:
            print(f"No user found with email {email}")
            return
        user.role = role
        db.commit()
        invalidate_cached_user(user.email)
        print(f"{user.email} is now role {role} ({user.name})")

import sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python set_role.py <email> <role_int>  (1=Admin, 2=Manager, 3=User)")
    else:
        set_role(sys.argv[1], int(sys.argv[2]))
# To use this role setter functionality enter the below command
# python set_role.py you@example.com 1