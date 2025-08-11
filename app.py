from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import json, os

app = Flask(__name__, template_folder="templates")

RADNO_VREME = {
    "pon-petak": {"start": 10, "end": 20},
    "subota": {"start": 10, "end": 13},
    "nedelja": None
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

def ucitaj_posebne_datume():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def sacuvaj_posebne_datume(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    sada = datetime.now()
    dan = sada.weekday()
    sat = sada.hour

    posebni = ucitaj_posebne_datume()
    datum_str = sada.strftime("%Y-%m-%d")

    if datum_str in posebni:
        # podrži i listu [start,end] i tuple
        start, end = posebni[datum_str]
    else:
        if dan < 5:
            sv = RADNO_VREME["pon-petak"]
            start, end = sv["start"], sv["end"]
        elif dan == 5:
            sv = RADNO_VREME["subota"]
            start, end = sv["start"], sv["end"]
        else:
            start, end = None, None

    if start is None:
        poruka = "Danas je nedelja. Ordinacija ne radi."
    elif not (start <= sat < end):
        poruka = f"Radno vrijeme ordinacije je od {start} do {end} časova."
    else:
        poruka = "Ordinacija je trenutno otvorena."

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
    # sortiran prikaz
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
    # Lokalno pokretanje
    port = int(os.environ.get("PORT", 5091))
    app.run(host="0.0.0.0", port=port, debug=True)