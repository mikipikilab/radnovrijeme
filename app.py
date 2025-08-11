from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from zoneinfo import ZoneInfo
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

def ucitaj_posebne_datume():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def sacuvaj_posebne_datume(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def sat_label(h):
    """Vrati cijeli sat kao string (npr. 10)."""
    try:
        return str(int(h))
    except Exception:
        return str(h)

@app.route("/")
def index():
    sada = datetime.now(ZoneInfo("Europe/Podgorica"))
    dan = sada.weekday()  # 0=pon ... 6=ned
    sat = sada.hour
    ime_dana = DANI_PUNIM[dan]

    posebni = ucitaj_posebne_datume()
    datum_str = sada.strftime("%Y-%m-%d")

    # default raspored po danu
    if dan < 5:
        sv = RADNO_VRIJEME["ponedjeljak-petak"]
        start, end = sv["start"], sv["end"]
    elif dan == 5:
        sv = RADNO_VRIJEME["subota"]
        start, end = sv["start"], sv["end"]
    else:
        start, end = None, None  # nedjelja

    # posebni datum prepisuje default (dozvoli [None, None] = neradni)
    if datum_str in posebni:
        ps = posebni[datum_str]
        if isinstance(ps, (list, tuple)) and len(ps) == 2:
            start, end = ps[0], ps[1]

    # poruka sa "časova" (bez :00 i bez "h")
    if start is None:
        poruka = "Danas je Nedjelja. Ordinacija ne radi."
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
        start = int(request.form["start"])
        end = int(request.form["end"])
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
