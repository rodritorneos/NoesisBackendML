from fastapi import APIRouter
from pydantic import BaseModel
import joblib
import os

router = APIRouter()

# Ruta al archivo .pkl entrenado
modelo_path = os.path.join(os.path.dirname(__file__), "modelo_noesis.pkl")
modelo = joblib.load(modelo_path)

# Mapear salida numérica a etiqueta de nivel
mapa_niveles = {
    0: "Básico",
    1: "Intermedio",
    2: "Avanzado"
}

# Esquema de entrada para la predicción
class EntradaNivel(BaseModel):
    puntaje_obtenido: int
    puntaje_total: int
    clase_mas_recurrida_cod: int

@router.post("/predecir_nivel")
def predecir_nivel(datos: EntradaNivel):
    relacion_puntaje = datos.puntaje_obtenido / datos.puntaje_total
    entrada = [[
        datos.puntaje_obtenido,
        datos.puntaje_total,
        relacion_puntaje,
        datos.clase_mas_recurrida_cod
    ]]
    pred = modelo.predict(entrada)[0]
    return {"nivel_predicho": mapa_niveles[pred]}