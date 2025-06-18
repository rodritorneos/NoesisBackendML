from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

# Base de datos
from database import init_db, engine, get_db

# Modelos y esquemas
from models import Usuario, Favorito, Visita, Puntaje, Base
from schemas import (
    UsuarioRegistro, UsuarioLogin, UsuarioResponse, UsuarioInfo,
    FavoritoRequest, FavoritoResponse, FavoritosUsuarioResponse, FavoritoAddResponse,
    VisitaRequest, VisitaResponse, VisitasUsuarioResponse,
    PuntajeRequest, PuntajeResponse, PuntajeUpdateResponse,
    MessageResponse, RegistroResponse, LoginResponse,
    HealthResponse, RootResponse
)

# Modelo predictivo
from modelo_predictor import router as predictor_router

# Crear app
app = FastAPI(
    title="API Usuarios, Favoritos, Visitas, Puntajes y Modelo ML Noesis",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Reemplaza con dominio en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar BD
Base.metadata.create_all(bind=engine)
init_db()

# Funciones auxiliares
def get_user_by_email(db: Session, email: str):
    return db.query(Usuario).filter(Usuario.email == email).first()

def create_user(db: Session, email: str, password: str):
    db_user = Usuario(email=email, password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    db_puntaje = Puntaje(
        usuario_id=db_user.id,
        puntaje_obtenido=0,
        puntaje_total=20,
        nivel="Básico"
    )
    db.add(db_puntaje)
    db.commit()
    return db_user

# Endpoints: Usuarios
@app.get("/usuarios", response_model=List[UsuarioResponse])
async def get_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(Usuario).all()
    return [{"email": user.email, "password": user.password} for user in usuarios]

@app.post("/usuarios/registro", response_model=RegistroResponse)
async def registrar_usuario(usuario: UsuarioRegistro, db: Session = Depends(get_db)):
    if get_user_by_email(db, usuario.email):
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    create_user(db, usuario.email, usuario.password)
    return {"message": "Usuario registrado exitosamente", "email": usuario.email}

@app.post("/usuarios/login", response_model=LoginResponse)
async def login_usuario(usuario: UsuarioLogin, db: Session = Depends(get_db)):
    usuario_encontrado = get_user_by_email(db, usuario.email)
    if not usuario_encontrado:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if usuario_encontrado.password != usuario.password:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    return {"message": "Login exitoso", "email": usuario.email}

@app.get("/usuarios/{email}", response_model=UsuarioInfo)
async def obtener_usuario(email: str, db: Session = Depends(get_db)):
    usuario = get_user_by_email(db, email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"email": usuario.email}

@app.delete("/usuarios/{email}", response_model=MessageResponse)
async def eliminar_usuario(email: str, db: Session = Depends(get_db)):
    usuario = get_user_by_email(db, email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(usuario)
    db.commit()
    return {"message": "Usuario, favoritos, visitas y puntajes eliminados exitosamente"}

# Endpoints: Favoritos
@app.post("/usuarios/{email}/favoritos", response_model=FavoritoAddResponse)
async def agregar_favorito(email: str, favorito: FavoritoRequest, db: Session = Depends(get_db)):
    usuario = get_user_by_email(db, email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    favorito_existente = db.query(Favorito).filter(
        Favorito.usuario_id == usuario.id,
        Favorito.clase_id == favorito.clase_id
    ).first()
    if favorito_existente:
        raise HTTPException(status_code=400, detail="La clase ya está en favoritos")
    nuevo_favorito = Favorito(
        usuario_id=usuario.id,
        clase_id=favorito.clase_id,
        nombre_clase=favorito.nombre_clase,
        imagen_path=favorito.imagen_path
    )
    db.add(nuevo_favorito)
    db.commit()
    db.refresh(nuevo_favorito)
    return {
        "message": "Favorito agregado exitosamente",
        "favorito": {
            "clase_id": nuevo_favorito.clase_id,
            "nombre_clase": nuevo_favorito.nombre_clase,
            "imagen_path": nuevo_favorito.imagen_path
        }
    }

@app.delete("/usuarios/{email}/favoritos/{clase_id}", response_model=MessageResponse)
async def remover_favorito(email: str, clase_id: str, db: Session = Depends(get_db)):
    usuario = get_user_by_email(db, email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    favorito = db.query(Favorito).filter(
        Favorito.usuario_id == usuario.id,
        Favorito.clase_id == clase_id
    ).first()
    if not favorito:
        raise HTTPException(status_code=404, detail="Favorito no encontrado")
    db.delete(favorito)
    db.commit()
    return {"message": "Favorito removido exitosamente"}

@app.get("/usuarios/{email}/favoritos", response_model=FavoritosUsuarioResponse)
async def obtener_favoritos_usuario(email: str, db: Session = Depends(get_db)):
    usuario = get_user_by_email(db, email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    favoritos = db.query(Favorito).filter(Favorito.usuario_id == usuario.id).all()
    favoritos_list = [
        {
            "clase_id": fav.clase_id,
            "nombre_clase": fav.nombre_clase,
            "imagen_path": fav.imagen_path
        } for fav in favoritos
    ]
    return {
        "email": email,
        "favoritos": favoritos_list,
        "total": len(favoritos_list)
    }

# Endpoints: Visitas
@app.post("/usuarios/{email}/visitas", response_model=MessageResponse)
async def registrar_visita(email: str, visita: VisitaRequest, db: Session = Depends(get_db)):
    usuario = get_user_by_email(db, email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    visita_existente = db.query(Visita).filter(
        Visita.usuario_id == usuario.id,
        Visita.clase_id == visita.clase_id
    ).first()
    if visita_existente:
        visita_existente.count += 1
    else:
        nueva_visita = Visita(
            usuario_id=usuario.id,
            clase_id=visita.clase_id,
            count=1
        )
        db.add(nueva_visita)
    db.commit()
    return {"message": "Visita registrada exitosamente"}

@app.get("/usuarios/{email}/visitas", response_model=VisitasUsuarioResponse)
async def obtener_visitas_usuario(email: str, db: Session = Depends(get_db)):
    usuario = get_user_by_email(db, email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    visitas = db.query(Visita).filter(Visita.usuario_id == usuario.id).all()
    visitas_list = [
        {
            "clase_id": visita.clase_id,
            "count": visita.count
        } for visita in visitas
    ]
    total_visitas = sum(visita.count for visita in visitas)
    return {
        "email": email,
        "visitas": visitas_list,
        "total_visitas": total_visitas
    }

# Endpoints: Puntajes
@app.get("/usuarios/{email}/puntajes", response_model=PuntajeResponse)
async def obtener_puntajes_usuario(email: str, db: Session = Depends(get_db)):
    usuario = get_user_by_email(db, email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    puntaje = db.query(Puntaje).filter(Puntaje.usuario_id == usuario.id).first()
    if not puntaje:
        puntaje = Puntaje(
            usuario_id=usuario.id,
            puntaje_obtenido=0,
            puntaje_total=20,
            nivel="Básico"
        )
        db.add(puntaje)
        db.commit()
        db.refresh(puntaje)
    return {
        "email": email,
        "puntaje_obtenido": puntaje.puntaje_obtenido,
        "puntaje_total": puntaje.puntaje_total,
        "nivel": puntaje.nivel
    }

@app.post("/usuarios/{email}/puntajes", response_model=PuntajeUpdateResponse)
async def actualizar_puntajes_usuario(email: str, puntaje_request: PuntajeRequest, db: Session = Depends(get_db)):
    usuario = get_user_by_email(db, email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    puntaje = db.query(Puntaje).filter(Puntaje.usuario_id == usuario.id).first()
    is_new_best = False
    porcentaje_nuevo = (puntaje_request.puntaje_obtenido / puntaje_request.puntaje_total) * 100
    if not puntaje:
        puntaje = Puntaje(
            usuario_id=usuario.id,
            puntaje_obtenido=puntaje_request.puntaje_obtenido,
            puntaje_total=puntaje_request.puntaje_total,
            nivel=puntaje_request.nivel
        )
        db.add(puntaje)
        is_new_best = True
    else:
        porcentaje_actual = (puntaje.puntaje_obtenido / puntaje.puntaje_total) * 100
        if porcentaje_nuevo > porcentaje_actual:
            puntaje.puntaje_obtenido = puntaje_request.puntaje_obtenido
            puntaje.puntaje_total = puntaje_request.puntaje_total
            puntaje.nivel = puntaje_request.nivel
            is_new_best = True
    db.commit()
    return {
        "message": "Puntaje procesado exitosamente",
        "data": {
            "is_new_best": is_new_best,
            "puntaje_obtenido": puntaje_request.puntaje_obtenido,
            "puntaje_total": puntaje_request.puntaje_total,
            "nivel": puntaje_request.nivel
        }
    }

# Información general
@app.get("/", response_model=RootResponse)
async def root():
    return {
        "message": "API de usuarios, favoritos, visitas, puntajes y modelo ML",
        "version": "2.0.0",
        "database": "PostgreSQL",
        "endpoints": {
            "usuarios": "/usuarios/{email}",
            "registro": "/usuarios/registro",
            "login": "/usuarios/login",
            "favoritos": "/usuarios/{email}/favoritos",
            "visitas": "/usuarios/{email}/visitas",
            "puntajes": "/usuarios/{email}/puntajes",
            "modelo_predictivo": "/predecir_nivel"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    try:
        return {
            "status": "healthy",
            "database": "PostgreSQL",
            "usuarios_registrados": db.query(Usuario).count(),
            "total_favoritos": db.query(Favorito).count(),
            "total_visitas": db.query(Visita).count(),
            "total_puntajes": db.query(Puntaje).count(),
            "database_ok": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_ok": False
        }


# Incluir modelo predictivo
app.include_router(predictor_router, tags=["Modelo Predictivo"])