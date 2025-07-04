import os
import requests
from datetime import datetime, timedelta
import json
import urllib.parse

API_URL = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/getFlightDetails"
API_KEY = os.environ.get("RAPIDAPI_KEY")
API_HOST = os.environ.get("RAPIDAPI_HOST")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST
}

ORIGEN = "MVD"
DESTINOS = ["MIA", "PTY", "BCN", "MAD"]
MESES_ADELANTE = 6
DURACION_MINIMA_DIAS = 7

def enviar_alerta_mensaje(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=data)

def obtener_precio_ida_vuelta(origen, destino, fecha_ida, fecha_vuelta):
    params = {
        "legs": json.dumps([
            {"origin": origen, "destination": destino, "date": fecha_ida},
            {"origin": destino, "destination": origen, "date": fecha_vuelta}
        ]),
        "adults": 1,
        "cabinClass": "economy",
        "currency": "USD",
        "locale": "en-US",
        "market": "en-US",
        "countryCode": "US"
    }

    try:
        response = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
        data = response.json()

        resultados = []
        for vuelo in data.get("data", []):
            precio = vuelo.get("price")
            aerolinea = vuelo.get("airline", "Desconocida")
            escalas = vuelo.get("stops", "N/A")
            if precio:
                resultados.append({
                    "precio": precio,
                    "aerolinea": aerolinea,
                    "escalas": escalas
                })

        return min(resultados, key=lambda x: x["precio"]) if resultados else None

    except Exception as e:
        return None

# Fecha
fecha_hoy = datetime.today()
fecha_fin = fecha_hoy + timedelta(days=30*MESES_ADELANTE)
dias = (fecha_fin - fecha_hoy).days
mensajes = []

for i in range(0, dias, 3):
    fecha_ida = (fecha_hoy + timedelta(days=i)).strftime("%Y-%m-%d")
    fecha_vuelta = (fecha_hoy + timedelta(days=i + DURACION_MINIMA_DIAS)).strftime("%Y-%m-%d")

    for destino in DESTINOS:
        resultado = obtener_precio_ida_vuelta(ORIGEN, destino, fecha_ida, fecha_vuelta)
        if resultado:
            precio = resultado['precio']
            aerolinea = resultado['aerolinea']
            escalas = resultado['escalas']

            # Crear link de compra (Google Flights)
            link = f"https://www.google.com/flights?hl=es#flt={ORIGEN}.{destino}.{fecha_ida}*{destino}.{ORIGEN}.{fecha_vuelta};c:USD;e:1;sd:1;t:e"
            link_encoded = urllib.parse.quote(link, safe=':/?=&')

            mensaje = (
                f"*{ORIGEN} → {destino}*\n"
                f"💰 *USD {precio}*\n"
                f"📅 ({fecha_ida} → {fecha_vuelta})\n"
                f✈️ {aerolinea} ({escalas} escalas)\n"
                f"[🛒 Ver vuelo]({link})"
            )
            mensajes.append(mensaje)

if mensajes:
    texto_final = "\n\n".join(mensajes)
    enviar_alerta_mensaje(texto_final)
