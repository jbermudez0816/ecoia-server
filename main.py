from fastapi import FastAPI, Request, Header, HTTPException
import cv2
import numpy as np
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

app = FastAPI()

API_KEY = "ecoia123"

# Firebase
cred = credentials.Certificate("./firebase_key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://ecoia-bbb33-default-rtdb.firebaseio.com/'
})

qr_detector = cv2.QRCodeDetector()

@app.get("/")
def home():
    return {"msg": "Servidor EcoIA activo 🔥"}

@app.post("/upload")
async def upload(request: Request, x_api_key: str = Header(None)):

    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="No autorizado")

    body = await request.body()

    np_arr = np.frombuffer(body, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return {"error": "Imagen inválida"}

    # 🔍 Leer QR con OpenCV
    data, bbox, _ = qr_detector.detectAndDecode(img)

    if not data:
        return {"msg": "No QR detectado"}

    try:
        codigo, nombre, objeto, puntos = data.split("|")
        puntos = int(puntos)
    except:
        return {"error": "Formato QR incorrecto"}

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
