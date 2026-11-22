from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime, timezone
import os
import uvicorn

app = FastAPI(title="DrinkAdvisor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)

#os.environ para despliegue. Descomente cuando ya probó todo local.
#client = MongoClient(os.environ["MONGO_URI"])
# TODO: conectarse al cluster Admonsis  
# client = MongoClient("mongodb://<usuario>:<contraseña>@157.253.236.88:8087")

client = MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=10000)
# TODO: conectarse a la base de datos Admonsis  
# db = client["ISIS*******"]
db = client[os.environ["MONGO_DB"]]


@app.get("/")
def inicio():
    return {"estado": "API funcionando correctamente"}

@app.get('/bares/{bar_id}/comentarios')
def get_comentarios(bar_id: int):
    filtro = {"bar_id": bar_id}
    return list(db["comentarios_bares"].find(filtro, {"_id": 0}))

@app.post('/bares/{bar_id}/comentarios')
def post_comentario(bar_id: int, datos: dict):
    texto = datos.get("texto")
    if not isinstance(texto, str) or not texto.strip():
        raise HTTPException(422, "Escribe el texto del comentario.")

    if "calificacion" in datos:
        nota = datos["calificacion"]
        if type(nota) is not int or not 1 <= nota <= 5:
            raise HTTPException(422, "La calificacion debe ser un entero de 1 a 5.")

    datos.pop("_id", None)
    datos["texto"] = texto.strip()
    datos["bar_id"] = bar_id
    datos["fecha"] = datetime.now(timezone.utc).isoformat()
    db["comentarios_bares"].insert_one(datos)
    return {"mensaje": "Comentario guardado"}

# TODO: implementar GET /bares/{bar_id}/eventos
# Debe retornar todos los eventos del bar desde la colección 'eventos'
@app.get("/bares/{bar_id}/eventos")
def get_eventos(bar_id: int):
    filtro = {"bar_id": bar_id}
    return list(db["eventos"].find(filtro, {"_id": 0}))

# TODO: implementar POST /bares/{bar_id}/eventos  
# Debe insertar el evento en la colección 'eventos'
# Recuerde agregar bar_id y fecha_creacion al documento antes de insertar
@app.post("/bares/{bar_id}/eventos")
def post_evento(bar_id: int, datos: dict):
    nombre = datos.get("nombre")
    if not isinstance(nombre, str) or not nombre.strip():
        raise HTTPException(422, "Escribe el nombre del evento.")

    evento = {}
    for campo, valor in datos.items():
        if isinstance(valor, str):
            valor = valor.strip()
        if campo != "_id" and valor is not None and valor != "":
            evento[campo] = valor

    evento["bar_id"] = bar_id
    evento["fecha_creacion"] = datetime.now(timezone.utc).isoformat()
    db["eventos"].insert_one(evento)
    return {"mensaje": "Evento guardado"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
