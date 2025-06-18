from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    favoritos = relationship("Favorito", back_populates="usuario")
    visitas = relationship("Visita", back_populates="usuario")
    puntajes = relationship("Puntaje", back_populates="usuario")

class Favorito(Base):
    __tablename__ = 'favoritos'

    id = Column(Integer, primary_key=True, index=True)
    clase_id = Column(String, nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))

    usuario = relationship("Usuario", back_populates="favoritos")

class Visita(Base):
    __tablename__ = 'visitas'

    id = Column(Integer, primary_key=True, index=True)
    clase_id = Column(String, nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))

    usuario = relationship("Usuario", back_populates="visitas")

class Puntaje(Base):
    __tablename__ = 'puntajes'

    id = Column(Integer, primary_key=True, index=True)
    puntaje_obtenido = Column(Integer, nullable=False)
    puntaje_total = Column(Integer, nullable=False)
    nivel = Column(String, nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))

    usuario = relationship("Usuario", back_populates="puntajes")