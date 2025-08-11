from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import json, os

app = Flask(__name__, template_folder="templates")

RADNO_VRIJEME = {
    "ponedjeljak-petak": {"start": 10, "end": 20},
    "subota": {"start": 10, "end": 13},
    "nedjelja": None
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

DANI_PUNIM = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota", "Nedjelja"]

def now_podgorica():
    try:
        return datetime.now(ZoneInfo("Europe/Podgorica"))
    except Exception:
        return datetime.now()  # fallback da ne padne app ako nema tzdata

def ucitaj_posebne_datume():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def sacuvaj_posebne_datume(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def to_int_or_none(x):
    try:
        return int(x)
    except (ValueError, TypeError):
        return None

def sat_label(h):
    try:
        return str(int(h))
    except Exception:
        return str(h)

@app.route("/")
def index():
    sada = now_podgorica()
    dan = sada.weekday()     # 0=pon ... 6=ned
    sat = sada.hour
    ime_dana = DANI_PUNIM[dan]

    # default raspored po danu
    if dan < 5:
        sv = RADNO_VRIJEME["ponedjeljak-petak"]
        start, end = sv["start"], sv["end"]
    elif dan == 5:
        sv = RADNO_VRIJEME["subota"]
        start, end = sv["start"], sv["end"]
    else:
        start, end = None, None  # nedjelja

    # posebni datum prepisuje default
    posebni = ucitaj_posebne_datume()
    datum_str = sada.strftime("%Y-%m-%d")
    ps = posebni.get(datum_str)
    if isinstance(ps, (list, tuple)) and len(ps) == 2:
        start = ps[0] if ps[0] is not None else None
        end   = ps[1] if ps[1] is not None else None

    # poruka sa "časova"
    if start is None or end is None:
        poruka = "Danas je neradni dan."
    elif isinstance(start, int) and isinstance(end, int) and start <= sat < end:
        poruka = f"Ordinacija je trenutno otvorena. Danas ({ime_dana}) radimo od {sat_label(start)} do {sat_label(end)} časova."
    elif isinstance(start, int) and isinstance(end, int):
        poruka = f"Ordinacija je trenutno zatvorena. Danas ({ime_dana}) radimo od {sat_label(start)} do {sat_label(end)} časova."
    else:
        poruka = f"Danas ({ime_dana}) je neradni dan."

    return render_template("index.html", poruka=poruka)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    posebni = ucitaj_posebne_datume()
    if request.method == "POST":
        datum = request.form["datum"].strip()
        if "neradni" in request.form:
            start, end = None, None
        else:
            start = to_int_or_none(request.form.get("start"))
            end   = to_int_or_none(request.form.get("end"))
            if start is None or end is None:
                start = end = None  # ako je nešto prazno/neispravno, tretiraj kao neradni
        posebni[datum] = [start, end]
        sacuvaj_posebne_datume(posebni)
        return redirect(url_for("admin"))

    sortirano = dict(sorted(posebni.items()))
    return render_template("admin.html", posebni=sortirano)

@app.route("/obrisi/<datum>")
def obrisi(datum):
    posebni = ucitaj_posebne_datume()
    if datum in posebni:
        del posebni[datum]
        sacuvaj_posebne_datume(posebni)
    return redirect(url_for("admin"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5091))
    app.run(host="0.0.0.0", port=port, debug=True)
