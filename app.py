import json
import os
import re
from datetime import date, datetime
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "szalloda-titkos-kulcs-cserezd-le-elesben")

MAI_NAP = date.today()
ADAT_FAJL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adatok.json")

# Teszt recepciós fiókok (felhasználónév: jelszó)
RECEPCIO_FIKOK = {
    "recepcio": "1234",
    "admin": "admin123"
}

SZOBASZAMOK = [
    "110", "116",
    "121", "122", "123", "124", "125", "126", "127", "128",
    "221", "222", "223", "224", "225", "226", "227", "228",
    "322", "323", "324", "325", "326", "327", "328",
    "450", "451", "452"
]

MINTA_ADATOK = {
    "110": {
        "statusz": "Maradó",
        "becsekkolt": True,
        "becsekkolas_idopont": "2026-11-21 15:10",
        "kicsekkolt": False,
        "eltelt_napok": 2,
        "ejszakak": 3,
        "napi_takaritas_kesz": False,
        "vendeg": "Kovács család",
        "fo": "2 felnőtt, 1 gyerek",
        "be_ki": "Érkezés: 2026-11-21 • Távozás: 2026-11-24",
        "igeny": "Babágy bekészítése, laktózmentes reggeli",
        "forras": "Booking.com"
    },
    "121": {
        "statusz": "Koszos",
        "becsekkolt": False,
        "becsekkolas_idopont": "",
        "kicsekkolt": True,
        "eltelt_napok": 0,
        "ejszakak": 0,
        "napi_takaritas_kesz": False,
        "vendeg": "-",
        "fo": "-",
        "be_ki": "Kicsekkolt: 2026-11-23 10:30",
        "igeny": "",
        "forras": "Recepció"
    },
    "224": {
        "statusz": "Maradó",
        "becsekkolt": True,
        "becsekkolas_idopont": "2026-11-23 15:00",
        "kicsekkolt": False,
        "eltelt_napok": 0,
        "ejszakak": 2,
        "napi_takaritas_kesz": False,
        "vendeg": "Nagy Péter & Anna",
        "fo": "2 felnőtt",
        "be_ki": "Érkezés: 2026-11-23 • Távozás: 2026-11-25",
        "igeny": "Csendesebb oldal, allergénmentes ágynemű",
        "forras": "Booking.com"
    },
    "225": {
        "statusz": "Maradó",
        "becsekkolt": True,
        "becsekkolas_idopont": "2026-11-22 16:20",
        "kicsekkolt": False,
        "eltelt_napok": 1,
        "ejszakak": 1,
        "napi_takaritas_kesz": False,
        "vendeg": "Szabó Márk",
        "fo": "1 felnőtt",
        "be_ki": "Érkezés: 2026-11-22 • Távozás: 2026-11-23 (1 éjszakás)",
        "igeny": "",
        "forras": "Booking.com"
    },
    "450": {
        "statusz": "Tiszta",
        "becsekkolt": False,
        "becsekkolas_idopont": "",
        "kicsekkolt": False,
        "eltelt_napok": 0,
        "ejszakak": 0,
        "napi_takaritas_kesz": False,
        "vendeg": "-",
        "fo": "-",
        "be_ki": "Kiadható",
        "igeny": "",
        "forras": "-"
    }
}

szimulalt_booking_sablons = [
    {
        "statusz": "Érkező",
        "becsekkolt": False,
        "becsekkolas_idopont": "",
        "kicsekkolt": False,
        "eltelt_napok": 0,
        "ejszakak": 4,
        "napi_takaritas_kesz": False,
        "vendeg": "Tóth Gábor",
        "fo": "2 felnőtt, 2 gyerek",
        "be_ki": "Érkezés: 2026-11-23 • Távozás: 2026-11-27",
        "igeny": "Késői érkezés (21:30), 2 extra törölköző",
        "forras": "Booking.com"
    },
    {
        "statusz": "Érkező",
        "becsekkolt": False,
        "becsekkolas_idopont": "",
        "kicsekkolt": False,
        "eltelt_napok": 0,
        "ejszakak": 2,
        "napi_takaritas_kesz": False,
        "vendeg": "Horváth Júlia",
        "fo": "1 felnőtt",
        "be_ki": "Érkezés: 2026-11-24 • Távozás: 2026-11-26",
        "igeny": "Vízforraló + tea válogatás",
        "forras": "Booking.com"
    },
    {
        "statusz": "Érkező",
        "becsekkolt": False,
        "becsekkolas_idopont": "",
        "kicsekkolt": False,
        "eltelt_napok": 0,
        "ejszakak": 3,
        "napi_takaritas_kesz": False,
        "vendeg": "Molnár Bence & Réka",
        "fo": "2 felnőtt",
        "be_ki": "Érkezés: 2026-11-23 • Távozás: 2026-11-26",
        "igeny": "Gluténmentes reggeli, magasabb párna",
        "forras": "Booking.com"
    },
    {
        "statusz": "Érkező",
        "becsekkolt": False,
        "becsekkolas_idopont": "",
        "kicsekkolt": False,
        "eltelt_napok": 0,
        "ejszakak": 1,
        "napi_takaritas_kesz": False,
        "vendeg": "Varga Dániel",
        "fo": "1 felnőtt, 1 gyerek",
        "be_ki": "Érkezés: 2026-11-23 • Távozás: 2026-11-24 (1 éjszakás)",
        "igeny": "Babágy a szobába",
        "forras": "Booking.com"
    }
]


def alap_szoba(szam):
    return {
        "szam": szam,
        "statusz": "Üres",
        "becsekkolt": False,
        "becsekkolas_idopont": "",
        "kicsekkolt": False,
        "eltelt_napok": 0,
        "ejszakak": 0,
        "napi_takaritas_kesz": False,
        "vendeg": "-",
        "fo": "-",
        "be_ki": "-",
        "igeny": "",
        "forras": "-"
    }


def szobak_letrehozasa():
    lista = []
    for szam in SZOBASZAMOK:
        adat = alap_szoba(szam)
        if szam in MINTA_ADATOK:
            adat.update(MINTA_ADATOK[szam])
        lista.append(adat)
    return lista


def allapot_betoltese():
    if os.path.exists(ADAT_FAJL):
        try:
            with open(ADAT_FAJL, "r", encoding="utf-8") as f:
                mentett = json.load(f)
            if isinstance(mentett, dict) and "szobak" in mentett:
                return (
                    mentett["szobak"],
                    mentett.get("utolso_ertesites", ""),
                    mentett.get("hiba_uzenet", ""),
                    int(mentett.get("booking_szamlalo", 0))
                )
        except Exception:
            pass
    return szobak_letrehozasa(), "", "", 0


def allapot_mentese():
    adatok = {
        "szobak": szobak,
        "utolso_ertesites": utolso_ertesites,
        "hiba_uzenet": hiba_uzenet,
        "booking_szamlalo": booking_szamlalo
    }
    with open(ADAT_FAJL, "w", encoding="utf-8") as f:
        json.dump(adatok, f, ensure_ascii=False, indent=2)


def aktualis_idopont():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def van_aktiv_vendeg(szoba):
    return (
        szoba.get("vendeg", "-") != "-"
        and szoba.get("vendeg", "").strip() != ""
        and not szoba.get("kicsekkolt", False)
    )


def letszam_szam(fo_szoveg):
    if not fo_szoveg or fo_szoveg == "-":
        return 0
    szamok = re.findall(r"\d+", str(fo_szoveg))
    return sum(int(s) for s in szamok)


def vendegadatok_torlese(szoba, be_ki_szoveg="-"):
    szoba["vendeg"] = "-"
    szoba["fo"] = "-"
    szoba["be_ki"] = be_ki_szoveg
    szoba["forras"] = "-"
    szoba["becsekkolt"] = False
    szoba["becsekkolas_idopont"] = ""
    szoba["eltelt_napok"] = 0
    szoba["ejszakak"] = 0
    szoba["napi_takaritas_kesz"] = False
    szoba["igeny"] = ""


def szoba_kiertekelese(szoba):
    m = szoba.copy()
    st = m["statusz"]
    aktiv_vendeg = van_aktiv_vendeg(m)
    eltelt = int(m.get("eltelt_napok", 0))
    ejszakak = int(m.get("ejszakak", 0))

    if m.get("kicsekkolt"):
        m["aktiv_statusz"] = "Koszos"
        m["napi_takaritas_kell"] = False
        m["van_aktiv_vendeg"] = False
        m["allapot_megjegyzes"] = "Kicsekkolt – takarítás szükséges"
        return m

    if aktiv_vendeg and ejszakak == 1 and eltelt >= 1:
        m["aktiv_statusz"] = "Koszos"
        m["napi_takaritas_kell"] = False
        m["van_aktiv_vendeg"] = True
        m["allapot_megjegyzes"] = "1 éjszakás távozási nap – Koszos (piros), még nem csekkolt ki"
        return m

    if aktiv_vendeg and m.get("becsekkolt"):
        m["aktiv_statusz"] = "Maradó"
        m["van_aktiv_vendeg"] = True
        if eltelt == 0:
            m["napi_takaritas_kell"] = False
            m["allapot_megjegyzes"] = "Érkezési nap (0. nap) – ma nem kell napi takarítás"
        else:
            if m.get("napi_takaritas_kesz"):
                m["napi_takaritas_kell"] = False
                m["allapot_megjegyzes"] = "Maradó • Napi takarítás elvégezve"
            else:
                m["napi_takaritas_kell"] = True
                m["allapot_megjegyzes"] = "Maradó • Napi takarítás szükséges!"
        return m

    if st == "Távozó":
        m["aktiv_statusz"] = "Koszos" if m.get("kicsekkolt") else "Maradó"
        m["napi_takaritas_kell"] = False
        m["van_aktiv_vendeg"] = aktiv_vendeg
        m["allapot_megjegyzes"] = ""
        return m

    m["aktiv_statusz"] = st
    m["napi_takaritas_kell"] = False
    m["van_aktiv_vendeg"] = aktiv_vendeg
    m["allapot_megjegyzes"] = ""
    return m


def telitettseg_szamitasa(kiertekelt_szobak):
    osszes_szoba = len(kiertekelt_szobak)
    foglalt_szobak = 0
    osszes_vendeg = 0

    for sz in kiertekelt_szobak:
        van_nev = sz.get("vendeg", "-") != "-" and sz.get("vendeg", "").strip() != ""
        if sz["aktiv_statusz"] in ["Maradó", "Érkező"] or van_nev:
            foglalt_szobak += 1
        if van_nev and not sz.get("kicsekkolt", False):
            osszes_vendeg += letszam_szam(sz.get("fo", ""))

    szazalek = round((foglalt_szobak / osszes_szoba) * 100) if osszes_szoba else 0
    return {
        "foglalt_szobak": foglalt_szobak,
        "osszes_szoba": osszes_szoba,
        "osszes_vendeg": osszes_vendeg,
        "szazalek": szazalek
    }


def recepcios_jogosult():
    return bool(session.get("recepcios_felhasznalo"))


szobak, utolso_ertesites, hiba_uzenet, booking_szamlalo = allapot_betoltese()

HTML_SABLON = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hotel Szobák ({{ szobak|length }} db)</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #eef1f5;
            margin: 0;
            padding: 16px;
            display: flex;
            justify-content: center;
        }
        .mobil-keret {
            width: 100%;
            max-width: 440px;
        }
        h2 {
            margin: 0 0 4px 0;
            color: #111827;
            font-size: 20px;
        }
        .alcim {
            font-size: 13px;
            color: #6b7280;
            margin-bottom: 12px;
        }
        .telitettseg-panel {
            background: #1e293b;
            color: white;
            border-radius: 12px;
            padding: 12px 14px;
            margin-bottom: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.12);
        }
        .telitettseg-cim {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #94a3b8;
            margin-bottom: 8px;
            font-weight: 700;
        }
        .telitettseg-sor {
            display: flex;
            justify-content: space-between;
            gap: 8px;
        }
        .stat-doboz {
            flex: 1;
            background: rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 8px 10px;
        }
        .stat-ertek {
            font-size: 17px;
            font-weight: 800;
            color: #f8fafc;
        }
        .stat-cimke {
            font-size: 11px;
            color: #cbd5e1;
            margin-top: 2px;
        }
        .ertesites-box {
            background: #ecfdf5;
            border: 1px solid #6ee7b7;
            border-left: 4px solid #059669;
            color: #065f46;
            padding: 10px 12px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        .hiba-box {
            background: #fef2f2;
            border: 1px solid #fca5a5;
            border-left: 4px solid #dc2626;
            color: #991b1b;
            padding: 10px 12px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        .jelmagyarazat {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 12px;
        }
        .chip {
            font-size: 11px;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 999px;
        }

        details.recepcio-blokk {
            background: white;
            border-radius: 12px;
            margin-bottom: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            overflow: hidden;
        }
        summary.recepcio-fejlec {
            list-style: none;
            cursor: pointer;
            padding: 12px 14px;
            background: #0f172a;
            color: white;
            font-size: 14px;
            font-weight: 700;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
        }
        summary.recepcio-fejlec::-webkit-details-marker {
            display: none;
        }
        .recepcio-tartalom {
            padding: 14px;
        }
        .al-panel {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 12px;
        }
        .panel-cim {
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 8px;
            color: #111827;
        }
        .belepes-info {
            font-size: 12px;
            color: #475569;
            margin-bottom: 10px;
            line-height: 1.4;
        }
        .bejelentkezve-sor {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
            font-size: 13px;
            color: #065f46;
            font-weight: 600;
        }

        input, select {
            width: 100%;
            box-sizing: border-box;
            padding: 8px 10px;
            margin-bottom: 8px;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            font-size: 14px;
            background: white;
        }
        .ket-oszlop {
            display: flex;
            gap: 8px;
        }
        .ket-oszlop > div {
            flex: 1;
        }
        .mezo-cimke {
            display: block;
            font-size: 12px;
            color: #4b5563;
            margin-bottom: 3px;
            font-weight: 600;
        }
        .checkbox-sor {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            font-size: 13px;
            color: #374151;
        }
        .checkbox-sor input[type="checkbox"] {
            width: auto;
            margin: 0;
        }
        button {
            width: 100%;
            padding: 10px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
        }
        .btn-belepes {
            background: #1d4ed8;
            color: white;
        }
        .btn-kilepes {
            background: #64748b;
            color: white;
            width: auto;
            padding: 6px 10px;
            font-size: 12px;
        }
        .btn-mentes {
            background: #2563eb;
            color: white;
        }
        .btn-booking {
            background: #0f766e;
            color: white;
        }
        .gomb-sav {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }
        .btn-napi-tak {
            background: #0284c7;
            color: white;
            padding: 8px;
            font-size: 12px;
        }
        .btn-kicsekk {
            background: #dc2626;
            color: white;
            padding: 8px;
            font-size: 12px;
        }
        .btn-tiszta {
            background: #16a34a;
            color: white;
            padding: 8px;
            font-size: 12px;
        }
        .btn-torol {
            background: #4b5563;
            color: white;
            padding: 8px;
            font-size: 12px;
        }

        .st-Tiszta { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
        .st-Koszos { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
        .st-Maradó { background: #dbeafe; color: #1d4ed8; border: 1px solid #93c5fd; }
        .st-Érkező { background: #fef9c3; color: #a16207; border: 1px solid #fde047; }
        .st-Üres   { background: #f3f4f6; color: #4b5563; border: 1px solid #d1d5db; }

        details.szoba-sav {
            border-radius: 10px;
            margin-bottom: 8px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.07);
            scroll-margin-top: 16px;
            overflow: hidden;
        }
        details.szoba-sav.sav-Tiszta { background: #dcfce7; border: 1px solid #86efac; color: #14532d; }
        details.szoba-sav.sav-Koszos { background: #fee2e2; border: 1px solid #fca5a5; color: #7f1d1d; }
        details.szoba-sav.sav-Maradó { background: #dbeafe; border: 1px solid #93c5fd; color: #1e3a8a; }
        details.szoba-sav.sav-Érkező { background: #fef9c3; border: 1px solid #fde047; color: #713f12; }
        details.szoba-sav.sav-Üres   { background: #f3f4f6; border: 1px solid #d1d5db; color: #374151; }

        summary.szoba-fejlec {
            list-style: none;
            cursor: pointer;
            padding: 11px 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 700;
            user-select: none;
        }
        summary.szoba-fejlec::-webkit-details-marker {
            display: none;
        }
        .bal-csoport {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .szobaszam {
            font-size: 16px;
            font-weight: 800;
        }
        .mini-jel {
            font-size: 11px;
            padding: 2px 7px;
            border-radius: 999px;
            background: rgba(255,255,255,0.75);
            font-weight: 700;
        }
        .jobb-csoport {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
        }
        .nyil {
            transition: transform 0.2s ease;
            font-size: 12px;
        }
        details[open] .nyil {
            transform: rotate(90deg);
        }

        .szoba-tartalom {
            background: white;
            color: #374151;
            padding: 12px 14px 14px 14px;
            border-top: 1px solid rgba(0,0,0,0.08);
        }
        .sor {
            font-size: 14px;
            color: #374151;
            margin: 4px 0;
        }
        .becsekk-jegyzet {
            margin-top: 6px;
            padding: 6px 10px;
            background: #f8fafc;
            border-left: 3px solid #0284c7;
            border-radius: 4px;
            font-size: 12px;
            color: #0f172a;
        }
        .napi-takaritas-box {
            margin-top: 8px;
            padding: 8px 10px;
            background: #eff6ff;
            border: 1px solid #93c5fd;
            border-left: 4px solid #2563eb;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            color: #1e40af;
        }
        .napi-kesz-box {
            margin-top: 8px;
            padding: 7px 10px;
            background: #f0fdf4;
            border-left: 4px solid #16a34a;
            border-radius: 6px;
            font-size: 12px;
            color: #166534;
        }
        .igeny-doboz {
            margin-top: 8px;
            padding: 8px 10px;
            background: #fffbeb;
            border-left: 4px solid #f59e0b;
            border-radius: 4px;
            font-size: 13px;
            color: #92400e;
        }
    </style>
</head>
<body>
    <div class="mobil-keret">
        <h2>🏨 Szobaállapotok</h2>
        <div class="alcim">Összesen {{ szobak|length }} szoba (110 – 452) • Takarítás bejelentkezés nélkül is elérhető</div>

        <div class="telitettseg-panel">
            <div class="telitettseg-cim">📊 Szálloda telítettség</div>
            <div class="telitettseg-sor">
                <div class="stat-doboz">
                    <div class="stat-ertek">{{ telitettseg.foglalt_szobak }} / {{ telitettseg.osszes_szoba }}</div>
                    <div class="stat-cimke">Foglalt / aktív szoba ({{ telitettseg.szazalek }}%)</div>
                </div>
                <div class="stat-doboz">
                    <div class="stat-ertek">{{ telitettseg.osszes_vendeg }} fő</div>
                    <div class="stat-cimke">Összes vendég a házban</div>
                </div>
            </div>
        </div>

        {% if hiba %}
        <div class="hiba-box">
            ⛔ {{ hiba }}
        </div>
        {% endif %}

        {% if ertesites %}
        <div class="ertesites-box">
            ✅ {{ ertesites }}
        </div>
        {% endif %}

        <div class="jelmagyarazat">
            <span class="chip st-Tiszta">Tiszta (zöld)</span>
            <span class="chip st-Koszos">Koszos (piros)</span>
            <span class="chip st-Maradó">Maradó (kék)</span>
            <span class="chip st-Érkező">Érkező (sárga)</span>
            <span class="chip st-Üres">Üres (szürke)</span>
        </div>

        <details id="recepcio-panel" class="recepcio-blokk">
            <summary class="recepcio-fejlec">
                <span>
                    {% if recepcios_bejelentkezve %}
                    🔓 Recepciós rész ({{ recepcios_felhasznalo }})
                    {% else %}
                    🔒 Recepciós rész (Bejelentkezés szükséges)
                    {% endif %}
                </span>
                <span class="nyil">▶</span>
            </summary>

            <div class="recepcio-tartalom">
                {% if not recepcios_bejelentkezve %}
                <div class="al-panel">
                    <div class="panel-cim">🔑 Recepciós bejelentkezés</div>
                    <div class="belepes-info">
                        A szobaszerkesztéshez, Booking-szimulációhoz, kicsekkoláshoz és vendégtörléshez add meg a felhasználónevet és jelszót.
                    </div>
                    <form method="POST" action="{{ url_for('recepcio_belepes') }}">
                        <input type="text" name="felhasznalonev" placeholder="Felhasználónév" required>
                        <input type="password" name="jelszo" placeholder="Jelszó" required>
                        <button type="submit" class="btn-belepes">Belépés a recepciós részbe</button>
                    </form>
                </div>
                {% else %}
                <div class="bejelentkezve-sor">
                    <span>Bejelentkezve: {{ recepcios_felhasznalo }}</span>
                    <form method="POST" action="{{ url_for('recepcio_kilepes') }}" style="margin:0;">
                        <button type="submit" class="btn-kilepes">Kijelentkezés</button>
                    </form>
                </div>

                <div class="al-panel">
                    <div class="panel-cim">📲 Vendég / Booking szimuláció</div>
                    <form method="POST" action="{{ url_for('booking_szimulacio') }}">
                        <button type="submit" class="btn-booking">+ Új Booking foglalás beérkezése (üres szobába)</button>
                    </form>
                </div>

                <div class="al-panel">
                    <div class="panel-cim">🛠️ Szoba szerkesztése (Recepció / Csere)</div>
                    <form method="POST" action="{{ url_for('szoba_szerkesztese') }}">
                        <label class="mezo-cimke">Szoba kiválasztása</label>
                        <select name="szobaszam">
                            {% for szoba in szobak %}
                            <option value="{{ szoba.szam }}">
                                Szoba {{ szoba.szam }} ({{ szoba.aktiv_statusz }} – {{ szoba.vendeg }})
                            </option>
                            {% endfor %}
                        </select>

                        <input type="text" name="vendeg" placeholder="Vendég neve (pl. Kiss Péter)...">
                        <input type="text" name="fo" placeholder="Létszám (pl. 2 felnőtt, 1 gyerek)...">

                        <div class="ket-oszlop">
                            <div>
                                <label class="mezo-cimke">Érkezés dátuma</label>
                                <input type="date" name="erkezes_datum">
                            </div>
                            <div>
                                <label class="mezo-cimke">Távozás dátuma</label>
                                <input type="date" name="tavozas_datum">
                            </div>
                        </div>

                        <input type="text" name="be_ki" placeholder="Egyedi Ki/Be szöveg (opcionális)...">
                        <input type="text" name="becsekkolas_idopont" placeholder="Becsekkolás időpontja (üresen hagyva: most)">
                        <input type="text" name="igeny" placeholder="Különleges igény (pl. babágy, allergia)...">

                        <div class="ket-oszlop">
                            <div>
                                <label class="mezo-cimke">Hány napja van itt? (0 = érkezési nap)</label>
                                <input type="number" name="eltelt_napok" min="0" placeholder="pl. 0, 1, 2">
                            </div>
                            <div>
                                <label class="mezo-cimke">Foglalás hossza (éjszaka)</label>
                                <input type="number" name="ejszakak" min="0" placeholder="pl. 1, 2, 3">
                            </div>
                        </div>

                        <label class="mezo-cimke">Státusz</label>
                        <select name="statusz">
                            <option value="">Státusz változatlan</option>
                            <option value="Maradó">Maradó (kék, ha már legalább 1 napos)</option>
                            <option value="Távozó">Távozó (kicsekkolás után Koszos/piros)</option>
                            <option value="Érkező">Érkező (sárga)</option>
                            <option value="Koszos">Koszos (piros)</option>
                            <option value="Tiszta">Tiszta (zöld – csak ha nincs aktív vendég)</option>
                            <option value="Üres">Üres (szürke – csak ha nincs aktív vendég)</option>
                        </select>

                        <label class="checkbox-sor">
                            <input type="checkbox" name="becsekkolt" value="1">
                            Vendég már becsekkolt (rögzíti a pontos becsekkolási időt)
                        </label>

                        <label class="checkbox-sor">
                            <input type="checkbox" name="kicsekkolt" value="1">
                            Vendég kicsekkolt (törli a vendéget és Koszos/piros lesz)
                        </label>

                        <label class="checkbox-sor">
                            <input type="checkbox" name="vendeget_torol" value="1">
                            Vendégek törlése a szobából (nincsenek ott / szobacsere)
                        </label>

                        <button type="submit" class="btn-mentes">Módosítások mentése</button>
                    </form>
                </div>
                {% endif %}
            </div>
        </details>

        {% for szoba in szobak %}
        <details id="szoba-{{ szoba.szam }}" data-szoba="{{ szoba.szam }}" class="szoba-sav sav-{{ szoba.aktiv_statusz }}">
            <summary class="szoba-fejlec">
                <span class="bal-csoport">
                    <span class="szobaszam">{{ szoba.szam }}</span>
                    <span>{{ szoba.aktiv_statusz }}</span>
                    {% if szoba.napi_takaritas_kell %}
                    <span class="mini-jel">🧹 Napi tak.</span>
                    {% endif %}
                    {% if szoba.igeny %}
                    <span class="mini-jel">⚠️ Igény</span>
                    {% endif %}
                </span>
                <span class="jobb-csoport">
                    {% if szoba.vendeg != "-" %}
                    <span>{{ szoba.vendeg }}</span>
                    {% endif %}
                    <span class="nyil">▶</span>
                </span>
            </summary>

            <div class="szoba-tartalom">
                <div class="sor"><strong>Státusz:</strong> {{ szoba.aktiv_statusz }}</div>
                <div class="sor"><strong>Vendég:</strong> {{ szoba.vendeg }} ({{ szoba.forras }})</div>
                <div class="sor"><strong>Létszám:</strong> {{ szoba.fo }}</div>
                <div class="sor"><strong>Ki/Be:</strong> {{ szoba.be_ki }}</div>

                {% if szoba.becsekkolt and szoba.becsekkolas_idopont %}
                <div class="becsekk-jegyzet">
                    🕒 <strong>Becsekkolva:</strong> {{ szoba.becsekkolas_idopont }}
                </div>
                {% endif %}

                {% if szoba.vendeg != "-" %}
                <div class="sor">
                    <strong>Tartózkodás:</strong> {{ szoba.eltelt_napok }}. nap • {{ szoba.ejszakak }} éjszakás
                </div>
                {% endif %}

                {% if szoba.napi_takaritas_kell %}
                <div class="napi-takaritas-box">
                    🧹 Maradó vendég – napi takarítás szükséges!
                </div>
                {% elif szoba.allapot_megjegyzes %}
                <div class="napi-kesz-box">
                    ℹ️ {{ szoba.allapot_megjegyzes }}
                </div>
                {% endif %}

                {% if szoba.igeny %}
                <div class="igeny-doboz">
                    ⚠️ <strong>Különleges igény:</strong> {{ szoba.igeny }}
                </div>
                {% endif %}

                <div class="gomb-sav">
                    {% if szoba.napi_takaritas_kell %}
                    <form method="POST" action="{{ url_for('gyors_muvelet') }}" style="flex:1;">
                        <input type="hidden" name="szobaszam" value="{{ szoba.szam }}">
                        <input type="hidden" name="muvelet" value="napi_takaritas">
                        <button type="submit" class="btn-napi-tak">🧹 Napi takarítás kész</button>
                    </form>
                    {% endif %}

                    {% if not szoba.van_aktiv_vendeg and szoba.aktiv_statusz != "Tiszta" %}
                    <form method="POST" action="{{ url_for('gyors_muvelet') }}" style="flex:1;">
                        <input type="hidden" name="szobaszam" value="{{ szoba.szam }}">
                        <input type="hidden" name="muvelet" value="kitakaritva">
                        <button type="submit" class="btn-tiszta">✓ Kitakarítva (Zöld)</button>
                    </form>
                    {% endif %}

                    {% if recepcios_bejelentkezve and szoba.van_aktiv_vendeg %}
                    <form method="POST" action="{{ url_for('gyors_muvelet') }}" style="flex:1;">
                        <input type="hidden" name="szobaszam" value="{{ szoba.szam }}">
                        <input type="hidden" name="muvelet" value="kicsekkolas">
                        <button type="submit" class="btn-kicsekk">Kicsekkolás</button>
                    </form>
                    {% endif %}

                    {% if recepcios_bejelentkezve and szoba.vendeg != "-" %}
                    <form method="POST" action="{{ url_for('gyors_muvelet') }}" style="flex:1;">
                        <input type="hidden" name="szobaszam" value="{{ szoba.szam }}">
                        <input type="hidden" name="muvelet" value="vendeg_torles">
                        <button type="submit" class="btn-torol">Vendég törlése</button>
                    </form>
                    {% endif %}
                </div>
            </div>
        </details>
        {% endfor %}
    </div>

    <script>
        function nyitottSzobakMentese() {
            const nyitott = [];
            document.querySelectorAll("details.szoba-sav[open]").forEach(function(el) {
                nyitott.push(el.getAttribute("data-szoba"));
            });
            sessionStorage.setItem("hotelNyitottSzobak", JSON.stringify(nyitott));

            const recPanel = document.getElementById("recepcio-panel");
            if (recPanel) {
                sessionStorage.setItem("hotelRecepcioNyitva", recPanel.open ? "1" : "0");
            }
        }

        document.querySelectorAll("details").forEach(function(el) {
            el.addEventListener("toggle", nyitottSzobakMentese);
        });

        document.querySelectorAll("form").forEach(function(form) {
            form.addEventListener("submit", function() {
                nyitottSzobakMentese();
                sessionStorage.setItem("hotelScrollY", String(window.scrollY));
            });
        });

        window.addEventListener("load", function() {
            const nyitottRaw = sessionStorage.getItem("hotelNyitottSzobak");
            if (nyitottRaw) {
                try {
                    const nyitottLista = JSON.parse(nyitottRaw);
                    nyitottLista.forEach(function(szam) {
                        const elem = document.getElementById("szoba-" + szam);
                        if (elem) elem.open = true;
                    });
                } catch (e) {}
            }

            const recNyitva = sessionStorage.getItem("hotelRecepcioNyitva");
            const recPanel = document.getElementById("recepcio-panel");
            if (recPanel && recNyitva === "1") {
                recPanel.open = true;
            }

            const savedY = sessionStorage.getItem("hotelScrollY");
            if (savedY !== null) {
                window.scrollTo({ top: parseInt(savedY, 10), behavior: "instant" });
                sessionStorage.removeItem("hotelScrollY");
            }
        });
    </script>
</body>
</html>
"""


def oldal_renderelese():
    megjelenitheto_szobak = [szoba_kiertekelese(szoba) for szoba in szobak]
    telitettseg = telitettseg_szamitasa(megjelenitheto_szobak)
    return render_template_string(
        HTML_SABLON,
        szobak=megjelenitheto_szobak,
        telitettseg=telitettseg,
        ertesites=utolso_ertesites,
        hiba=hiba_uzenet,
        recepcios_bejelentkezve=recepcios_jogosult(),
        recepcios_felhasznalo=session.get("recepcios_felhasznalo", "")
    )


@app.route("/", methods=["GET"])
def fooldal():
    return oldal_renderelese()


@app.route("/recepcio-belepes", methods=["POST"])
def recepcio_belepes():
    global hiba_uzenet, utolso_ertesites
    felhasznalonev = request.form.get("felhasznalonev", "").strip()
    jelszo = request.form.get("jelszo", "")

    if felhasznalonev in RECEPCIO_FIKOK and RECEPCIO_FIKOK[felhasznalonev] == jelszo:
        session["recepcios_felhasznalo"] = felhasznalonev
        hiba_uzenet = ""
        utolso_ertesites = f"Sikeres belépés recepciós jogosultsággal ({felhasznalonev})."
    else:
        utolso_ertesites = ""
        hiba_uzenet = "Hibás felhasználónév vagy jelszó!"

    allapot_mentese()
    return redirect(url_for("fooldal"))


@app.route("/recepcio-kilepes", methods=["POST"])
def recepcio_kilepes():
    global utolso_ertesites, hiba_uzenet
    session.pop("recepcios_felhasznalo", None)
    hiba_uzenet = ""
    utolso_ertesites = "Kijelentkeztél a recepciós részből."
    allapot_mentese()
    return redirect(url_for("fooldal"))


@app.route("/szerkesztes", methods=["POST"])
def szoba_szerkesztese():
    global utolso_ertesites, hiba_uzenet
    if not recepcios_jogosult():
        hiba_uzenet = "A szobák szerkesztéséhez recepciós bejelentkezés szükséges!"
        allapot_mentese()
        return redirect(url_for("fooldal"))

    hiba_uzenet = ""
    kivalasztott_szam = request.form.get("szobaszam", "").strip()
    uj_vendeg = request.form.get("vendeg", "").strip()
    uj_fo = request.form.get("fo", "").strip()
    erkezes_datum = request.form.get("erkezes_datum", "").strip()
    tavozas_datum = request.form.get("tavozas_datum", "").strip()
    uj_be_ki = request.form.get("be_ki", "").strip()
    uj_becsekk_ido = request.form.get("becsekkolas_idopont", "").strip()
    uj_igeny = request.form.get("igeny", "").strip()
    uj_statusz = request.form.get("statusz", "").strip()

    eltelt_raw = request.form.get("eltelt_napok", "").strip()
    ejszakak_raw = request.form.get("ejszakak", "").strip()

    becsekkolt_pipa = request.form.get("becsekkolt") == "1"
    kicsekkolt_pipa = request.form.get("kicsekkolt") == "1"
    vendeget_torol_pipa = request.form.get("vendeget_torol") == "1"

    for szoba in szobak:
        if szoba["szam"] == kivalasztott_szam:
            if kicsekkolt_pipa:
                most_ido = aktualis_idopont()
                vendegadatok_torlese(szoba, be_ki_szoveg=f"Kicsekkolt: {most_ido}")
                szoba["kicsekkolt"] = True
                szoba["statusz"] = "Koszos"
                utolso_ertesites = f"Szoba {kivalasztott_szam}: vendég kicsekkolva, igények törölve, Koszos (piros) státuszra állítva."
                break

            if uj_statusz in ["Tiszta", "Üres"]:
                if not van_aktiv_vendeg(szoba) or vendeget_torol_pipa:
                    vendegadatok_torlese(
                        szoba,
                        be_ki_szoveg="Kiadható" if uj_statusz == "Tiszta" else "-"
                    )
                    szoba["statusz"] = uj_statusz
                    szoba["kicsekkolt"] = False
                    utolso_ertesites = f"Szoba {kivalasztott_szam}: státusz frissítve -> {uj_statusz}."
                break

            if vendeget_torol_pipa:
                vendegadatok_torlese(szoba, be_ki_szoveg="Vendég törölve (szobacseréhez)")

            if uj_igeny:
                szoba["igeny"] = uj_igeny

            if uj_vendeg:
                szoba["vendeg"] = uj_vendeg
                szoba["forras"] = "Recepció"
                szoba["kicsekkolt"] = False
                if not becsekkolt_pipa and not szoba["becsekkolt"]:
                    szoba["becsekkolt"] = True
            if uj_fo:
                szoba["fo"] = uj_fo

            if uj_be_ki:
                szoba["be_ki"] = uj_be_ki
            elif erkezes_datum and tavozas_datum:
                szoba["be_ki"] = f"Érkezés: {erkezes_datum} • Távozás: {tavozas_datum}"
                if not ejszakak_raw.isdigit():
                    try:
                        d1 = date.fromisoformat(erkezes_datum)
                        d2 = date.fromisoformat(tavozas_datum)
                        kulonbseg = (d2 - d1).days
                        if kulonbseg >= 0:
                            szoba["ejszakak"] = kulonbseg
                    except ValueError:
                        pass
            elif erkezes_datum:
                szoba["be_ki"] = f"Érkezés: {erkezes_datum}"
            elif tavozas_datum:
                szoba["be_ki"] = f"Távozás: {tavozas_datum}"

            if eltelt_raw.isdigit():
                szoba["eltelt_napok"] = int(eltelt_raw)
                szoba["napi_takaritas_kesz"] = False
            if ejszakak_raw.isdigit():
                szoba["ejszakak"] = int(ejszakak_raw)

            if becsekkolt_pipa:
                szoba["becsekkolt"] = True
                szoba["kicsekkolt"] = False
                szoba["statusz"] = "Maradó"
                if not eltelt_raw.isdigit():
                    szoba["eltelt_napok"] = 0

            if uj_statusz:
                szoba["statusz"] = uj_statusz
                if uj_statusz == "Maradó":
                    szoba["becsekkolt"] = True
                    szoba["kicsekkolt"] = False
                elif uj_statusz == "Érkező":
                    szoba["becsekkolt"] = False
                    szoba["becsekkolas_idopont"] = ""
                    szoba["kicsekkolt"] = False

            if uj_becsekk_ido:
                szoba["becsekkolas_idopont"] = uj_becsekk_ido
                szoba["becsekkolt"] = True
            elif (becsekkolt_pipa or uj_vendeg or uj_statusz == "Maradó") and not szoba.get("becsekkolas_idopont"):
                szoba["becsekkolas_idopont"] = aktualis_idopont()

            utolso_ertesites = f"Szoba {kivalasztott_szam}: adatok elmentve."
            break

    allapot_mentese()
    return redirect(url_for("fooldal"))


@app.route("/gyors-muvelet", methods=["POST"])
def gyors_muvelet():
    global utolso_ertesites, hiba_uzenet
    kivalasztott_szam = request.form.get("szobaszam", "").strip()
    muvelet = request.form.get("muvelet", "").strip()

    if muvelet in ["kicsekkolas", "vendeg_torles"] and not recepcios_jogosult():
        hiba_uzenet = "Kicsekkoláshoz és a vendég törléséhez recepciós bejelentkezés szükséges!"
        allapot_mentese()
        return redirect(url_for("fooldal"))

    hiba_uzenet = ""

    for szoba in szobak:
        if szoba["szam"] == kivalasztott_szam:
            if muvelet == "napi_takaritas":
                szoba["napi_takaritas_kesz"] = True
                szoba["igeny"] = ""
                utolso_ertesites = f"Szoba {kivalasztott_szam}: napi takarítás készre állítva."
            elif muvelet == "kitakaritva":
                if not van_aktiv_vendeg(szoba):
                    vendegadatok_torlese(szoba, be_ki_szoveg="Kiadható")
                    szoba["statusz"] = "Tiszta"
                    szoba["kicsekkolt"] = False
                    utolso_ertesites = f"Szoba {kivalasztott_szam}: kitakarítva -> Tiszta (zöld)."
            elif muvelet == "kicsekkolas":
                most_ido = aktualis_idopont()
                vendegadatok_torlese(szoba, be_ki_szoveg=f"Kicsekkolt: {most_ido}")
                szoba["kicsekkolt"] = True
                szoba["statusz"] = "Koszos"
                utolso_ertesites = f"Szoba {kivalasztott_szam}: vendég kicsekkolt, igények törölve -> Koszos (piros)."
            elif muvelet == "vendeg_torles":
                vendegadatok_torlese(szoba, be_ki_szoveg="Vendég törölve (szobacseréhez)")
                szoba["kicsekkolt"] = True
                szoba["statusz"] = "Koszos"
                utolso_ertesites = f"Szoba {kivalasztott_szam}: vendég és igények törölve."
            break

    allapot_mentese()
    return redirect(url_for("fooldal"))


@app.route("/booking-szimulacio", methods=["POST"])
def booking_szimulacio():
    global booking_szamlalo, utolso_ertesites, hiba_uzenet
    if not recepcios_jogosult():
        hiba_uzenet = "Új Booking foglalás szimulálásához recepciós bejelentkezés szükséges!"
        allapot_mentese()
        return redirect(url_for("fooldal"))

    hiba_uzenet = ""
    cel_index = None
    for idx, sz in enumerate(szobak):
        ki = szoba_kiertekelese(sz)
        if not ki["van_aktiv_vendeg"] and ki["aktiv_statusz"] != "Maradó":
            cel_index = idx
            break

    if cel_index is None:
        utolso_ertesites = "Nincs szabad/üres szoba új Booking foglaláshoz!"
        allapot_mentese()
        return redirect(url_for("fooldal"))

    if booking_szamlalo >= len(szimulalt_booking_sablons):
        booking_szamlalo = 0

    uj_foglalas = szimulalt_booking_sablons[booking_szamlalo].copy()
    uj_foglalas["szam"] = szobak[cel_index]["szam"]
    szobak[cel_index] = uj_foglalas

    utolso_ertesites = (
        f"Új Booking.com foglalás érkezett az üres {uj_foglalas['szam']}-es szobába: "
        f"{uj_foglalas['vendeg']} ({uj_foglalas['fo']})"
    )
    booking_szamlalo += 1

    allapot_mentese()
    return redirect(url_for("fooldal"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)