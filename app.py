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

@app.route("/")
def index():
    sada = datetime.now(ZoneInfo("Europe/Podgorica"))
    dan = sada.weekday()  # 0=pon ... 6=ned
    sat = sada.hour
    ime_dana = DANI_PUNIM[dan]

    posebni = ucitaj_posebne_datume()
    datum_str = sada.strftime("%Y-%m-%d")

    # default
    if dan < 5:
        sv = RADNO_VRIJEME["ponedjeljak-petak"]
        start, end = sv["start"], sv["end"]
    elif dan == 5:
        sv = RADNO_VRIJEME["subota"]
        start, end = sv["start"], sv["end"]
    else:
        start, end = None, None  # nedjelja

    # override posebnim datumom
    if datum_str in posebni:
        ps = posebni[datum_str]
        start, end = (ps[0], ps[1]) if isinstance(ps, (list, tuple)) else (None, None)

    if start is None:
        poruka = "Danas je Nedjelja. Ordinacija ne radi."
    elif start <= sat < end:
        poruka = f"Ordinacija je trenutno otvorena. Danas ({ime_dana}) radimo od {start}:00 do {end}:00."
    else:
        poruka = f"Ordinacija je trenutno zatvorena. Danas ({ime_dana}) radimo od {start}:00 do {end}:00."

    return render_template("index.html", poruka=poruka)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    posebni = ucitaj_posebne_datume()

    if request.method == "POST":
        datum = request.form["datum"].strip()
        neradni = request.form.get("neradni") == "on"

        if neradni:
            posebni[datum] = [None, None]
        else:
            # prazno ili nevalidno -> ignoriši
            start_raw = request.form.get("start", "").strip()
            end_raw = request.form.get("end", "").strip()
            if start_raw == "" or end_raw == "":
                # ako je nešto prazno, tretiraj kao neradni
                posebni[datum] = [None, None]
            else:
                start = int(start_raw)
                end = int(end_raw)
                posebni[datum] = [start, end]

        sacuvaj_posebne_datume(posebni)
        return redirect(url_for("admin"))

    # priprema podataka za tabelu sa statusom za današnji dan
    sada = datetime.now(ZoneInfo("Europe/Podgorica"))
    today = sada.strftime("%Y-%m-%d")
    hour_now = sada.hour

    # sortirano po datumu
    sortirano = dict(sorted(posebni.items()))
    rows = []
    for d, se in sortirano.items():
        st, en = (se[0], se[1]) if isinstance(se, (list, tuple)) else (None, None)
        if d == today:
            if st is None:
                status = "Neradan dan (danas)"
            else:
                status = "Otvoreno sada" if st <= hour_now < en else "Zatvoreno sada"
        else:
            status = "—"
        rows.append({"datum": d, "start": st, "end": en, "status": status})

    return render_template("admin.html", posebni_rows=rows, danas=today)

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
