import cv2
import requests
import numpy as np
import time

STREAM_URL = "http://TU_IP/stream"
FIREBASE_BASE = "https://ecoia-bbb33-default-rtdb.firebaseio.com"

PUNTOS_OBJETOS = {
    "Botella Plastica": 5,
    "Vidrio": 10,
    "Carton": 7,
    "Lata": 8
}

detector = cv2.QRCodeDetector()

ultimo_qr = ""
ultimo_tiempo = 0

def conectar_stream():
    while True:
        try:
            print("🔄 Conectando ESP32...")
            resp = requests.get(STREAM_URL, stream=True, timeout=5)
            if resp.status_code == 200:
                print("✅ Conectado")
                return resp
        except:
            print("❌ Error conexión")
            time.sleep(2)

def actualizar_firebase(codigo, nombre, grado, objeto):

    puntos = PUNTOS_OBJETOS.get(objeto, 0)

    registro = {
        "codigo": codigo,
        "nombre": nombre,
        "grado": grado,
        "objeto": objeto,
        "puntos": puntos,
        "timestamp": int(time.time())
    }

    requests.post(f"{FIREBASE_BASE}/registros.json", json=registro)

    url_est = f"{FIREBASE_BASE}/estudiantes/{codigo}.json"
    data_est = requests.get(url_est).json()

    total_est = data_est["puntos_totales"] if data_est else 0
    total_est += puntos

    estudiante = {
        "nombre": nombre,
        "grado": grado,
        "puntos_totales": total_est
    }

    requests.put(url_est, json=estudiante)

    url_grado = f"{FIREBASE_BASE}/grados/{grado}.json"
    data_grado = requests.get(url_grado).json()

    total_grado = data_grado["puntos_totales"] if data_grado else 0
    total_grado += puntos

    grado_data = {
        "puntos_totales": total_grado
    }

    requests.put(url_grado, json=grado_data)

    print(f"🏆 {nombre} +{puntos} pts")

def main():
    global ultimo_qr, ultimo_tiempo

    while True:
        resp = conectar_stream()
        bytes_data = bytes()

        try:
            for chunk in resp.iter_content(chunk_size=2048):

                bytes_data += chunk

                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')

                if a != -1 and b != -1:

                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]

                    if len(jpg) < 1000:
                        continue

                    img = cv2.imdecode(
                        np.frombuffer(jpg, dtype=np.uint8),
                        cv2.IMREAD_COLOR
                    )

                    if img is None:
                        continue

                    data, bbox, _ = detector.detectAndDecode(img)

                    if data:

                        ahora = time.time()

                        if data != ultimo_qr or (ahora - ultimo_tiempo > 5):

                            ultimo_qr = data
                            ultimo_tiempo = ahora

                            print("🟢 QR:", data)

                            try:
                                codigo, nombre, grado = data.split("|")
                                objeto = "Botella Plastica"

                                actualizar_firebase(
                                    codigo,
                                    nombre,
                                    grado,
                                    objeto
                                )

                            except Exception as e:
                                print("⚠️ Error:", e)

        except:
            print("🔄 Reconectando...")
            time.sleep(1)

if __name__ == "__main__":
    main()
