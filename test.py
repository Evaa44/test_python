from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
import json

from flask import Flask, render_template, request


app = Flask(__name__)

WEATHER_CODES = {
	0: ("Ciel dégagé", "☀️"),
	1: ("Principalement dégagé", "🌤️"),
	2: ("Partiellement nuageux", "⛅"),
	3: ("Couvert", "☁️"),
	45: ("Brouillard", "🌫️"),
	48: ("Brouillard givrant", "🌫️"),
	51: ("Bruine légère", "🌦️"),
	53: ("Bruine modérée", "🌦️"),
	55: ("Bruine dense", "🌧️"),
	61: ("Pluie légère", "🌦️"),
	63: ("Pluie modérée", "🌧️"),
	65: ("Pluie forte", "🌧️"),
	71: ("Neige légère", "🌨️"),
	73: ("Neige modérée", "❄️"),
	75: ("Neige forte", "❄️"),
	80: ("Averses légères", "🌦️"),
	81: ("Averses modérées", "🌧️"),
	82: ("Averses violentes", "⛈️"),
	95: ("Orage", "⛈️"),
	96: ("Orage et grêle", "⛈️"),
	99: ("Orage et forte grêle", "⛈️"),
}


def fetch_json(url):
	with urlopen(url, timeout=10) as response:
		return json.loads(response.read().decode("utf-8"))


def get_weather(city):
	geo_params = urlencode({"name": city, "count": 1, "language": "fr", "format": "json"})
	locations = fetch_json(f"https://geocoding-api.open-meteo.com/v1/search?{geo_params}")
	results = locations.get("results", [])
	if not results:
		return None

	location = results[0]
	forecast_params = urlencode({
		"latitude": location["latitude"],
		"longitude": location["longitude"],
		"current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
		"daily": "temperature_2m_max,temperature_2m_min",
		"timezone": "auto",
		"forecast_days": 1,
	})
	forecast = fetch_json(f"https://api.open-meteo.com/v1/forecast?{forecast_params}")
	current = forecast["current"]
	description, icon = WEATHER_CODES.get(current["weather_code"], ("Conditions variables", "🌡️"))

	return {
		"name": location["name"],
		"region": location.get("admin1"),
		"country": location.get("country"),
		"temperature": round(current["temperature_2m"]),
		"feels_like": round(current["apparent_temperature"]),
		"humidity": current["relative_humidity_2m"],
		"wind": round(current["wind_speed_10m"]),
		"description": description,
		"icon": icon,
		"high": round(forecast["daily"]["temperature_2m_max"][0]),
		"low": round(forecast["daily"]["temperature_2m_min"][0]),
	}


@app.route("/", methods=["GET", "POST"])
def index():
	city = request.values.get("city", "").strip()
	weather = None
	error = None

	if request.method == "POST":
		if not city:
			error = "Saisissez le nom d’une ville pour lancer la recherche."
		else:
			try:
				weather = get_weather(city)
				if weather is None:
					error = f"Nous n’avons pas trouvé « {city} ». Vérifiez l’orthographe et réessayez."
			except (HTTPError, URLError, TimeoutError, KeyError, ValueError):
				error = "La météo est momentanément indisponible. Réessayez dans quelques instants."

	return render_template("index.html", city=city, weather=weather, error=error)


if __name__ == "__main__":
	app.run(debug=True)