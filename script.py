import json
import ssl
import urllib.error
import urllib.request

CITIES_FILE = "Cities.txt"


class WeatherData:
    def __init__(self, city, temperature_c, country):
        self.city = city
        self.temperature_c = temperature_c
        self.country = country


def load_cities(path):
    cities, seen = [], set()
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            for part in line.split(","):
                city = part.strip()
                if city and city.lower() not in seen:
                    seen.add(city.lower())
                    cities.append(city)
    return cities


def encode(city):
    return "".join("%{:02X}".format(b) for b in city.encode("utf-8"))


def open_url(req):
    try:
        return urllib.request.urlopen(req, timeout=30)
    except urllib.error.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" not in str(e):
            raise
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return urllib.request.urlopen(req, timeout=30, context=ctx)


def fetch(city):
    try:
        url = "https://wttr.in/" + encode(city) + "?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "weather-script/1.0"})
        with open_url(req) as response:
            data = json.loads(response.read().decode("utf-8"))

        temp = int(data["current_condition"][0]["temp_C"])
        country = data["nearest_area"][0]["country"][0]["value"] or "Unknown"
        return WeatherData(city, temp, country)
    except Exception as e:
        print("[!] {}: {}".format(city, e))
        return None


def fmt(t):
    return "{:+d} °C".format(t)


def main():
    cities = load_cities(CITIES_FILE)
    results = [w for w in (fetch(c) for c in cities) if w]

    for w in results:
        print("{}, {} {}".format(w.city, w.country, fmt(w.temperature_c)))

    print()

    by_country = {}
    for w in results:
        by_country.setdefault(w.country, []).append(w.temperature_c)

    for country in sorted(by_country):
        temps = by_country[country]
        avg = round(sum(temps) / len(temps))
        print("{} — {} cities, avg: {}, min: {}, max: {}".format(
            country, len(temps), fmt(avg), fmt(min(temps)), fmt(max(temps))))


if __name__ == "__main__":
    main()