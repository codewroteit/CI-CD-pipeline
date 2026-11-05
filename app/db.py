import hashlib
import hmac
import os
import time 

from sqlalchemy import Column, Integer, String , create_engine, select 
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite://")

if DATABASE_URL.startswith("sqlite"):
   engine = create_engine(
       DATABASE_URL,
       connect_args={"check_same_thread": False},
       poolclass=StaticPool
   )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt,200_000)
    return salt.hex() + "$" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$")
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return hmac.compare_digest(digest.hex(), digest_hex)

def init_db():
    for _ in range(30):
        try:
            Base.metadata.create_all(engine)
            break
        except OperationalError:
            time.sleep(1)
    else:
        raise RuntimeError("Database is not reachable")
    user = os.getenv("DASH_USER", "")
    password = os.getenv("DASH_PASS" "")
    if user and password:
        add_user(user, password)


def add_user(username: str, password: str) -> bool:
    with Session(engine) as session:
        session.add(User(username=username, password_hash=hash_password(password)))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return False
    return True


def check_login(username: str, password: str) -> bool:
    with Session(engine) as session:
        user = session.scalar(select(User).where(User.username == username))
        if user is None:
            return False
        return verify_password(password, user.password_hash)


def change_password(username: str, new_password: str) -> None:
    with Session(engine) as session:
        user = session.scalar(select(User).where(User.username == username))
        user.password_hash = hash_password(new_password)
        session.commit()
