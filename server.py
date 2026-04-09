from fastapi import FastAPI, Request, Header
import cv2
import numpy as np
import random

app = FastAPI()

API_KEY = "ecoia123"

@app.get("/")
def home():
    return {"msg": "Servidor EcoIA estable con OpenCV 🔥"}

@app.post("/upload")
async def upload(request: Request, x_api_key: str = Header(None)):

    if x_api_key != API_KEY:
        return {"error": "No autorizado"}

    body = await request.body()
    npimg = np.frombuffer(body, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    if img is None:
        return {"error": "Imagen inválida"}

    # ===== PROCESAMIENTO =====
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    # ===== QR CON OPENCV =====
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(gray)

    id = "NA"
    nombre = "NA"
    grado = "NA"

    if data:
        parts = data.split("|")
        if len(parts) == 3:
            id, nombre, grado = parts

    # ===== IA SIMULADA =====
    objeto = random.choice(["plastico", "carton", "vidrio", "lata"])

    print(f"📦 {id} | {nombre} | {grado} | {objeto}")

    return {
        "id": id,
        "nombre": nombre,
        "grado": grado,
        "objeto": objeto,
        "puntos": 10
    }
