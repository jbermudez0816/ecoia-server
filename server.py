from fastapi import FastAPI, Request, Header
from fastapi.responses import HTMLResponse, StreamingResponse, PlainTextResponse
import cv2
import numpy as np
import base64
import time

app = FastAPI()

# 🔐 CLAVE
API_KEY = "ecoia123"

# 📸 última imagen
last_image = None


@app.get("/")
def home():
    return {"msg": "Servidor EcoIA PRO 🔥"}


# =========================
# 📥 RECIBE IMAGEN
# =========================
@app.post("/upload")
async def upload(request: Request, x_api_key: str = Header(None)):

    global last_image

    if x_api_key != API_KEY:
        return {"error": "No autorizado"}

    body = await request.body()

    print(f"📦 Tamaño recibido: {len(body)} bytes")

    npimg = np.frombuffer(body, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    # 🔥 FALLBACK (si OpenCV falla)
    if img is None:
        print("⚠️ OpenCV falló, usando imagen RAW")
        last_image = base64.b64encode(body).decode('utf-8')
        return {"ok": True}

    # =========================
    # 🧠 PROCESAMIENTO
    # =========================
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(gray)

    id = "NA"
    nombre = "NA"
    grado = "NA"

    if data:
        parts = data.split("|")
        if len(parts) == 3:
            id, nombre, grado = parts

        # 🟩 Dibujar cuadro QR
        if bbox is not None:
            bbox = bbox.astype(int)
            for i in range(len(bbox[0])):
                pt1 = tuple(bbox[0][i])
                pt2 = tuple(bbox[0][(i + 1) % len(bbox[0])])
                cv2.line(img, pt1, pt2, (0, 255, 0), 2)

    # =========================
    # 📝 TEXTO EN PANTALLA
    # =========================
    texto = f"{nombre} - {grado}"

    cv2.putText(img, texto,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2)

    cv2.putText(img, "EcoIA",
                (10, img.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2)

    # =========================
    # 💾 GUARDAR IMAGEN
    # =========================
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


# =========================
# 🎥 STREAM EN TIEMPO REAL
# =========================
def generate_stream():
    global last_image

    while True:
        if last_image:
            frame = base64.b64decode(last_image)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03)  # 🔥 fluidez


@app.get("/stream")
def stream():
    return StreamingResponse(
        generate_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


# =========================
# 🌐 VISOR WEB
# =========================
@app.get("/view", response_class=HTMLResponse)
def view():
    return """
    <html>
    <head>
        <title>EcoIA PRO</title>
    </head>
    <body style="text-align:center; font-family:sans-serif;">
        <h2>📷 Cámara en tiempo real</h2>

        <img src="/stream" width="500" style="border:3px solid black;"/>

    </body>
    </html>
    """


# =========================
# 📡 DEBUG
# =========================
@app.get("/last")
def get_last():
    global last_image
    if last_image is None:
        return ""
    return PlainTextResponse(last_image)
