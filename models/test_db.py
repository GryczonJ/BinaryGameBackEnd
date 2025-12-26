from db import SessionLocal
from models.User import User

db = SessionLocal()

# Tworzymy nowego gracza
new_user = User(username="Gracz1", email="test@example.com")
new_user.set_password("tajnehaslo123")

db.add(new_user)
db.commit()
db.refresh(new_user)

print(f"Dodano użytkownika o ID: {new_user.id}")
db.close()