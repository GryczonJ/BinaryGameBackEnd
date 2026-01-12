from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


#DATABASE_URL = "postgresql://user:password@localhost:5432/binarygame"
DATABASE_URL = r"mssql+pyodbc://@(localdb)\MSSQLLocalDB/BinaryGame?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

#engine = create_engine(DATABASE_URL, echo=True)
engine = create_engine(
    DATABASE_URL, 
    echo=True,
    # Dodatkowe parametry dla stabilności połączenia na Windows
    connect_args={'check_same_thread': False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
