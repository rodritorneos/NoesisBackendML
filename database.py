from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Detectar si estás en Render o local
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app_database.db")

# Si es SQLite, crea carpeta y conecta con argumentos especiales
if DATABASE_URL.startswith("sqlite"):
    # Crear el directorio data si no existe
    os.makedirs("data", exist_ok=True)
    # Crear motor de base de datos
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# Crear sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa
Base = declarative_base()

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función para crear las tablas si no existen
def init_db():
    from models import Base  # Se importa aquí para evitar ciclos
    Base.metadata.create_all(bind=engine)