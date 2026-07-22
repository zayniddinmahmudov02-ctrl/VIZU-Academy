import app.models

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security.password import hash_password
EMAIL = "zayniddin.mahmudov.02@gmail.com"
NEW_PASSWORD = "12345678"

db = SessionLocal()

user = db.query(User).filter(User.email == EMAIL).first()

if user is None:
    print("User topilmadi!")
    raise SystemExit

user.password_hash = hash_password(NEW_PASSWORD)

db.commit()
db.close()

print("Password muvaffaqiyatli yangilandi!")