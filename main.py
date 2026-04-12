from fastapi import FastAPI, Request, Header, HTTPException
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

app = FastAPI()

# 🔐 API KEY
API_KEY = "ecoia123"

# 🔥 Inicializar Firebase
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://ecoia-bbb33-default-rtdb.firebaseio.com/'

})

# 🏠 Ruta base
@app.get("/")
def home():
    return {"msg": "Servidor EcoIA activo 🔥"}

# 📤 Endpoint principal
@app.post("/upload")
async def upload(request: Request, x_api_key: str = Header(None)):

    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="No autorizado")

    body = await request.body()

    # Convertir imagen
    np_arr = np.frombuffer(body, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return {"error": "Imagen inválida"}

    # 🔍 Leer QR
    qr_codes = decode(img)

    if not qr_codes:
        return {"msg": "No QR detectado"}

    data = qr_codes[0].data.decode("utf-8")

    # 🧾 Ejemplo formato QR: 10A-001|Juan|Botella|10
    try:
        codigo, nombre, objeto, puntos = data.split("|")
        puntos = int(puntos)
    except:
        return {"error": "Formato QR incorrecto"}

    # 🔥 Guardar en Firebase
    ref = db.reference("reciclaje")

    nuevo = {
        "codigo": codigo,
        "nombre": nombre,
        "objeto": objeto,
        "puntos": puntos,
        "fecha": datetime.now().isoformat()
    }

    ref.push(nuevo)

    return {
        "msg": "Registro exitoso",
        "data": nuevo
    }