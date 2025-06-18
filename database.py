from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Insertar la URL de la base de datos desde Render
DATABASE_URL = os.getenv("DATABASE_URL")

# Crear el motor de conexión para PostgreSQL
engine = create_engine(DATABASE_URL)

# Crear la sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declaración base para los modelos
Base = declarative_base()

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Crear las tablas si no existen
def init_db():
    from models import Base  # evitar ciclos de importación
    Base.metadata.create_all(bind=engine)