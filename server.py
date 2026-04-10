from fastapi import FastAPI, Request, Header
from fastapi.responses import HTMLResponse
import cv2
import numpy as np
import base64

app = FastAPI()

# 🔐 CLAVE
API_KEY = "ecoia123"

# 📸 última imagen recibida
last_image = None


@app.get("/")
def home():
    return {"msg": "Servidor EcoIA con visor en vivo 🔥"}


# 📥 RECIBE IMAGEN
@app.post("/upload")
async def upload(request: Request, x_api_key: str = Header(None)):

    global last_image

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

    # ===== DETECTOR QR =====
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(gray)

    id = "NA"
    nombre = "NA"
    grado = "NA"

    if data:
        parts = data.split("|")
        if len(parts) == 3:
            id, nombre, grado = parts

        # Dibujar cuadro del QR
        if bbox is not None:
            bbox = bbox.astype(int)
            for i in range(len(bbox[0])):
                pt1 = tuple(bbox[0][i])
                pt2 = tuple(bbox[0][(i + 1) % len(bbox[0])])
                cv2.line(img, pt1, pt2, (0, 255, 0), 2)

    # ===== GUARDAR IMAGEN PARA WEB =====
    _, buffer = cv2.imencode('.jpg', img)
    last_image = base64.b64encode(buffer).decode('utf-8')

    print(f"📦 {id} | {nombre} | {grado}")

    return {
        "id": id,
        "nombre": nombre,
        "grado": grado,
        "objeto": "pendiente",
        "puntos": 10
    }


# 🌐 VISOR EN VIVO
@app.get("/view", response_class=HTMLResponse)
def view_image():

    return """
    <html>
        <head>
            <title>EcoIA Cámara</title>
        </head>
        <body style="text-align:center; font-family:sans-serif;">
            <h2>📷 Cámara ESP32 en vivo</h2>

            <img id="cam" width="400" style="border:2px solid #333;"/>

            <script>
                setInterval(() => {
                    fetch('/last?t=' + new Date().getTime())
                        .then(res => res.text())
                        .then(data => {
                            if (data && data.length > 100) {
                                document.getElementById('cam').src =
                                "data:image/jpeg;base64," + data;
                            }
                        });
                }, 1000);
            </script>
        </body>
    </html>
    """


# 📡 endpoint que devuelve solo la imagen
@app.get("/last")
def get_last():
    global last_image
    if last_image is None:
        return ""
    return last_image
