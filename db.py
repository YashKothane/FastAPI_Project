from sqlalchemy import String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from models import Usermodel
from sqlalchemy import create_engine
# Create the Declarative Base Class
engine = create_engine("sqlite:///app.db", echo=True)
class Base(DeclarativeBase):
    pass

# Define the User model mapped to the "users" table
class User(Base):
    __tablename__ = "user"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    firstname: Mapped[str] = mapped_column(String(50))
    lastname: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(50))
    phone: Mapped[int] = mapped_column(Integer)
    role: Mapped[int] = mapped_column(Integer,default=3)
# Automatically create tables in the database if they don't exist
Base.metadata.create_all(engine)
