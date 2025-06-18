from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import joblib
import os

# Crear router
router = APIRouter()

# Cargar modelo entrenado
modelo_path = os.path.join(os.path.dirname(__file__), "modelo_noesis.pkl")
try:
    modelo = joblib.load(modelo_path)
except Exception as e:
    raise RuntimeError(f"No se pudo cargar el modelo: {e}")

# Mapear salidas numéricas a etiquetas
mapa_niveles = {
    0: "Básico",
    1: "Intermedio",
    2: "Avanzado"
}

# Entrada esperada para predicción
class EntradaNivel(BaseModel):
    puntaje_obtenido: int
    puntaje_total: int
    clase_mas_recurrida_cod: int

# Salida de predicción
class NivelPredicho(BaseModel):
    nivel_predicho: str

@router.post("/predecir_nivel", response_model=NivelPredicho)
def predecir_nivel(datos: EntradaNivel):
    try:
        relacion_puntaje = datos.puntaje_obtenido / datos.puntaje_total
        entrada = [[
            datos.puntaje_obtenido,
            datos.puntaje_total,
            relacion_puntaje,
            datos.clase_mas_recurrida_cod
        ]]
        pred = modelo.predict(entrada)[0]
        return {"nivel_predicho": mapa_niveles[pred]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al predecir nivel: {str(e)}")