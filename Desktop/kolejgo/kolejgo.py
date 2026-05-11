
import os
from datetime import datetime
import streamlit as st

from io import BytesIO

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.graphics.barcode.qr import QrCodeWidget
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics import renderPDF
except ImportError:
    os.system("pip install reportlab")
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.graphics.barcode.qr import QrCodeWidget
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics import renderPDF

st.set_page_config(page_title="KolejGO", page_icon="🚆", layout="wide")

MODES = {
    "Normalny": {"emoji": "🚆", "accent": "#1E88FF", "title": "KolejGO Normalny", "subtitle": "Pełny widok połączeń, cen i udogodnień.", "discount": 1.00, "font": "16px"},
    "Student": {"emoji": "🎓", "accent": "#18A058", "title": "KolejGO Student", "subtitle": "Najtańsze połączenia, zniżka studencka i szybka płatność.", "discount": 0.51, "font": "16px"},
    "Emeryt": {"emoji": "👴", "accent": "#7C3AED", "title": "KolejGO Senior", "subtitle": "Prosty widok, większe napisy i mniej kliknięć.", "discount": 0.63, "font": "24px"},
    "Rodzinny": {"emoji": "👨‍👩‍👧‍👦", "accent": "#F97316", "title": "KolejGO Rodzinny", "subtitle": "Miejsca razem, wózek, bagaż i rodzinne udogodnienia.", "discount": 0.70, "font": "16px"},
    "Niepełnosprawny": {"emoji": "♿", "accent": "#0EA5E9", "title": "KolejGO Dostępny", "subtitle": "Dostępność, asysta, windy i miejsca dla wózka.", "discount": 0.49, "font": "17px"},
}

TRAINS = [
    {"id":"IC 1234","name":"Tatry","depart":"09:15","arrive":"11:45","duration":"2h 30min","base":89,"changes":0,"platform":"3","track":"2","delay":"o czasie","wifi":True,"quiet":True,"bike":True,"pets":True,"family_zone":True,"seats_together":True,"stroller":True,"wheelchair":True,"lift":True,"accessible_toilet":True,"low_steps":True},
    {"id":"IC 1302","name":"Intercity","depart":"10:42","arrive":"13:18","duration":"2h 36min","base":57,"changes":0,"platform":"1","track":"4","delay":"+5 min","wifi":True,"quiet":False,"bike":True,"pets":True,"family_zone":True,"seats_together":True,"stroller":True,"wheelchair":True,"lift":True,"accessible_toilet":False,"low_steps":True},
    {"id":"EIP 3508","name":"Pendolino","depart":"12:05","arrive":"14:28","duration":"2h 23min","base":49,"changes":0,"platform":"2","track":"1","delay":"o czasie","wifi":True,"quiet":True,"bike":False,"pets":True,"family_zone":False,"seats_together":True,"stroller":False,"wheelchair":True,"lift":True,"accessible_toilet":True,"low_steps":True},
    {"id":"TLK 53104","name":"TLK","depart":"18:10","arrive":"21:45","duration":"3h 35min","base":96,"changes":1,"platform":"2","track":"4","delay":"+12 min","wifi":False,"quiet":False,"bike":True,"pets":True,"family_zone":False,"seats_together":False,"stroller":False,"wheelchair":False,"lift":True,"accessible_toilet":False,"low_steps":False},
]

CITIES = ["Warszawa Centralna", "Kraków Główny", "Gdańsk Główny", "Wrocław Główny", "Poznań Główny", "Katowice"]

mode = st.sidebar.radio("Wybierz dashboard", list(MODES.keys()))
cfg = MODES[mode]
accent = cfg["accent"]

if "offline_ticket" not in st.session_state:
    st.session_state.offline_ticket = None
if "payment_error" not in st.session_state:
    st.session_state.payment_error = False
if "internet_error" not in st.session_state:
    st.session_state.internet_error = False
if "refund_status" not in st.session_state:
    st.session_state.refund_status = None

css = """
<style>
.stApp {
    background: linear-gradient(180deg, #F3F8FF 0%, #EAF2FF 100%) !important;
    color: #10213F !important;
    font-size: __FONT__;
}
.block-container {
    padding-top: 0.7rem !important;
    padding-bottom: 1rem !important;
    max-width: 1180px !important;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #062451 0%, #0B2B5B 70%, #09234A 100%) !important;
}
section[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}
h1, h2, h3, h4, p, label, span, div {
    color: #10213F;
}
.app-shell {
    background: linear-gradient(180deg, #0B2B5B 0%, #0B2B5B 86px, transparent 86px);
    border-radius: 24px;
    padding: 18px;
    margin-bottom: 14px;
}
.header, .panel, .route {
    background: #FFFFFF;
    border-radius: 22px;
    box-shadow: 0 10px 26px rgba(11,43,91,0.10);
    border: 1px solid #DDEBFF;
}
.header {
    padding: 18px 20px;
}
.header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}
.header h1 {
    font-size: 34px;
    margin: 0;
    color: #0B2B5B !important;
}
.header p {
    margin: 5px 0 0 0;
    font-size: 16px;
    color: #49627F !important;
}
.mode-pill {
    display: inline-block;
    background: __ACCENT__;
    color: white !important;
    padding: 8px 12px;
    border-radius: 999px;
    font-weight: 800;
}
.panel {
    padding: 16px;
    margin-bottom: 14px;
}
.route {
    padding: 16px;
    margin-bottom: 12px;
}
.route h3 {
    margin: 0;
    font-size: 20px;
    color: #0B2B5B !important;
}
.route p {
    margin: 5px 0;
    font-size: 14px;
    color: #334E68 !important;
}
.badge {
    display: inline-block;
    background: #E8F2FF;
    color: #0B2B5B !important;
    border-radius: 10px;
    padding: 5px 9px;
    font-size: 12px;
    margin: 2px 4px 2px 0;
    font-weight: 800;
}
.price {
    color: __ACCENT__ !important;
    font-size: 25px;
    font-weight: 900;
}
button[kind="primary"] {
    background: #1E88FF !important;
    border-radius: 12px !important;
    font-weight: 900 !important;
}
.stDownloadButton button {
    background: #0B2B5B !important;
    color: white !important;
    border-radius: 12px !important;
    font-weight: 900 !important;
}
.senior-box {
    background: #FFFFFF;
    border: 3px solid __ACCENT__;
    border-radius: 22px;
    padding: 18px;
    font-size: 30px;
    margin-bottom: 12px;
    box-shadow: 0 10px 25px rgba(11,43,91,0.10);
}
.senior-box h2 {
    font-size: 42px !important;
    color: __ACCENT__ !important;
}
div[data-baseweb="select"] > div, input, textarea {
    background: #FFFFFF !important;
    color: #10213F !important;
    -webkit-text-fill-color: #10213F !important;
    border: 1px solid #B9D4F5 !important;
    border-radius: 12px !important;
}
div[data-baseweb="select"] span, div[data-baseweb="select"] div, div[data-baseweb="select"] input {
    color: #10213F !important;
    -webkit-text-fill-color: #10213F !important;
}
div[data-baseweb="popover"], div[role="listbox"], ul {
    background: #FFFFFF !important;
}
div[role="option"], li {
    background: #FFFFFF !important;
    color: #10213F !important;
}
div[role="option"] *, li * {
    color: #10213F !important;
    -webkit-text-fill-color: #10213F !important;
}
div[role="option"]:hover, div[role="option"][aria-selected="true"], li:hover {
    background: #E8F2FF !important;
    color: #10213F !important;
}
.info-blue {
    background: #E8F2FF;
    border-radius: 16px;
    padding: 12px 14px;
    border: 1px solid #B9D4F5;
    color: #0B2B5B !important;
}
.ticket-ready {
    background: #E8FFF2;
    color: #0F8A43 !important;
    border-radius: 16px;
    padding: 12px 14px;
    border: 1px solid #B8F0CE;
    font-weight: 800;
}

.empty-state { background:#FFF7ED; border:1px solid #FDBA74; border-radius:18px; padding:18px; margin:12px 0; }
.error-state { background:#FEF2F2; border:1px solid #FCA5A5; border-radius:18px; padding:18px; margin:12px 0; }
.offline-ticket { background:#FFFFFF; border:3px dashed #0B2B5B; border-radius:22px; padding:18px; margin:12px 0; box-shadow:0 10px 25px rgba(11,43,91,0.10); }
.refund-box { background:#F8FAFC; border:1px solid #CBD5E1; border-radius:18px; padding:16px; margin:12px 0; }

</style>
"""
css = css.replace("__ACCENT__", accent).replace("__FONT__", cfg["font"])
st.markdown(css, unsafe_allow_html=True)

if mode == "Emeryt":
    st.markdown("""
<style>
label, .stSelectbox label, .stTextInput label, .stDateInput label { font-size: 24px !important; font-weight: 800 !important; }
div[data-baseweb="select"] > div, input { min-height: 58px !important; font-size: 24px !important; }
.stButton button, .stDownloadButton button { min-height: 64px !important; font-size: 24px !important; font-weight: 800 !important; }
.stRadio label { font-size: 24px !important; }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("# 🚆 KolejGO")
st.sidebar.caption("Bilety kolejowe z QR i PDF")
st.sidebar.markdown("### Ten dashboard pokazuje")
if mode == "Normalny":
    sidebar_items = ["pełne połączenia", "cenę, czas i przesiadki", "peron oraz tor", "udogodnienia"]
elif mode == "Student":
    sidebar_items = ["najtańsze bilety", "zniżkę studencką", "BLIK", "alert opóźnienia"]
elif mode == "Emeryt":
    sidebar_items = ["duże litery", "tylko najważniejsze dane", "mało kliknięć", "pomoc/asystę"]
elif mode == "Rodzinny":
    sidebar_items = ["miejsca razem", "wózek i bagaż", "przedział rodzinny", "dłuższe przesiadki"]
else:
    sidebar_items = ["windy i rampy", "miejsce dla wózka", "asystę", "dostępną toaletę"]
for item in sidebar_items:
    st.sidebar.write("✅ " + item)

st.markdown(f"""
<div class="app-shell">
    <div class="header">
        <div class="header-row">
            <div>
                <h1>{cfg['emoji']} {cfg['title']}</h1>
                <p>{cfg['subtitle']}</p>
            </div>
            <span class="mode-pill">{mode}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown("### 🔎 Szukaj pociągu")
if mode == "Emeryt":
    c1, c2 = st.columns(2)
    with c1:
        from_city = st.selectbox("Skąd jadę", CITIES)
    with c2:
        to_city = st.selectbox("Dokąd jadę", CITIES, index=1)
    c3, c4 = st.columns(2)
    with c3:
        travel_date = st.date_input("Kiedy jadę")
    with c4:
        passenger_name = st.text_input("Imię i nazwisko")
    simple_only = st.checkbox("Pokaż tylko proste połączenia bez przesiadek", value=True)
    assistance = st.checkbox("Chcę pomoc przy wejściu do pociągu", value=False)
    passengers = 1
    train_class = "2 klasa"
    payment = "Karta"
else:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        from_city = st.selectbox("Skąd", CITIES)
    with c2:
        to_city = st.selectbox("Dokąd", CITIES, index=1)
    with c3:
        travel_date = st.date_input("Data podróży")
    with c4:
        passenger_name = st.text_input("Pasażer")
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        passengers = st.number_input("Liczba pasażerów", 1, 8, 1)
    with c6:
        train_class = st.selectbox("Klasa", ["2 klasa", "1 klasa"])
    with c7:
        payment = st.selectbox("Płatność", ["BLIK", "Karta", "Google Pay", "Przelew"])
    with c8:
        direct = st.checkbox("Bez przesiadek", value=(mode in ["Rodzinny", "Niepełnosprawny"]))
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown("### Funkcje dashboardu")
filters = {}
if mode == "Normalny":
    a, b, c, d, e = st.columns(5)
    with a: filters["wifi"] = st.checkbox("Wi‑Fi", value=False)
    with b: filters["quiet"] = st.checkbox("Strefa ciszy", value=False)
    with c: filters["bike"] = st.checkbox("Rower", value=False)
    with d: filters["pets"] = st.checkbox("Zwierzę", value=False)
    with e: filters["direct"] = st.checkbox("Tylko bezpośrednie", value=False)
elif mode == "Student":
    a, b, c, d = st.columns(4)
    with a: filters["cheapest"] = st.checkbox("Najtańsze najpierw", value=True)
    with b: filters["student_discount"] = st.checkbox("Zniżka studencka 49%", value=True)
    with c: filters["blik"] = st.checkbox("Pokaż BLIK", value=True)
    with d: filters["delays"] = st.checkbox("Alert opóźnień", value=True)
    st.markdown('<div class="ticket-ready">🎓 Cena w wynikach ma już naliczoną zniżkę studencką.</div>', unsafe_allow_html=True)
elif mode == "Emeryt":
    st.markdown('<div class="senior-box"><h2>Prosty tryb</h2>Pokazuję tylko 2 najłatwiejsze połączenia: bez przesiadek, z peronem, torem i dużym przyciskiem.</div>', unsafe_allow_html=True)
    filters["direct"] = simple_only
    filters["low_steps"] = True
    filters["assistance"] = assistance
elif mode == "Rodzinny":
    a, b, c, d = st.columns(4)
    with a: filters["seats_together"] = st.checkbox("Miejsca obok siebie", value=True)
    with b: filters["family_zone"] = st.checkbox("Przedział rodzinny", value=True)
    with c: filters["stroller"] = st.checkbox("Wózek dziecięcy", value=True)
    with d: filters["long_change"] = st.checkbox("Bez krótkich przesiadek", value=True)
    child_count = st.number_input("Liczba dzieci", 0, 6, 2)
else:
    a, b, c, d = st.columns(4)
    with a: filters["wheelchair"] = st.checkbox("Miejsce dla wózka", value=True)
    with b: filters["lift"] = st.checkbox("Winda/rampa na stacji", value=True)
    with c: filters["assistance"] = st.checkbox("Zamów asystę", value=True)
    with d: filters["accessible_toilet"] = st.checkbox("Dostępna toaleta", value=False)
    st.markdown('<div class="info-blue">♿ Wyniki ukrywają pociągi bez wymaganej dostępności.</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

def price(train):
    multiplier = 1.35 if train_class == "1 klasa" else 1.0
    family_multiplier = 0.85 if mode == "Rodzinny" else 1.0
    return round(train["base"] * cfg["discount"] * multiplier * passengers * family_multiplier, 2)

def matches(train):
    if mode != "Emeryt" and "direct" in globals() and direct and train["changes"] != 0:
        return False
    for key, val in filters.items():
        if not val:
            continue
        if key in ["cheapest", "student_discount", "blik", "delays", "assistance", "long_change"]:
            continue
        if key == "direct" and train["changes"] != 0:
            return False
        if key in train and not train[key]:
            return False
    return True

results = [t for t in TRAINS if matches(t)]
if mode == "Student":
    results = sorted(results, key=price)
elif mode == "Emeryt":
    results = [t for t in results if t["changes"] == 0 and t["low_steps"]][:2]
elif mode == "Rodzinny":
    results = sorted(results, key=lambda t: (not t["family_zone"], price(t)))
elif mode == "Niepełnosprawny":
    results = sorted(results, key=lambda t: (not t["wheelchair"], not t["lift"], price(t)))

st.markdown("### 🚄 Dostępne połączenia")
chosen_train = None
if not results:
    st.markdown(
        """
<div class="empty-state">
    <h3>😕 Brak połączeń</h3>
    <p>Nie znaleziono pociągów spełniających wymagania. Zmień filtry, wybierz inną trasę albo spróbuj później.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    a1, a2, a3 = st.columns(3)
    with a1:
        st.button("🔄 Wyszukaj ponownie", use_container_width=True)
    with a2:
        st.button("🧹 Wyczyść filtry", use_container_width=True)
    with a3:
        st.button("🔔 Powiadom mnie", use_container_width=True)
else:
    route_labels = []
    for train in results:
        p = price(train)
        if mode == "Emeryt":
            st.markdown(f'<div class="senior-box"><h2>{train["depart"]} → {train["arrive"]}</h2><b>{train["id"]} {train["name"]}</b><br>Peron {train["platform"]}, tor {train["track"]}<br>Cena: <b>{p:.2f} zł</b><br>Opóźnienie: {train["delay"]}</div>', unsafe_allow_html=True)
        else:
            badges = []
            if train["changes"] == 0: badges.append("bez przesiadek")
            if train["wifi"]: badges.append("Wi‑Fi")
            if train["bike"]: badges.append("rower")
            if train["family_zone"]: badges.append("rodzinny")
            if train["wheelchair"]: badges.append("dostępny")
            badge_html = "".join([f'<span class="badge">{b}</span>' for b in badges])
            st.markdown(f'<div class="route"><h3>{train["depart"]} → {train["arrive"]} • {train["id"]} {train["name"]}</h3><p>{from_city} → {to_city} | {train["duration"]} | Peron {train["platform"]}, tor {train["track"]} | Opóźnienie: {train["delay"]}</p><p>{badge_html}</p><div class="price">{p:.2f} zł</div></div>', unsafe_allow_html=True)
        route_labels.append(f"{train['depart']} {train['id']} — {p:.2f} zł")
    selected_label = st.radio("Wybierz bilet", route_labels, horizontal=(mode != "Emeryt"))
    chosen_train = results[route_labels.index(selected_label)]

def safe(txt):
    txt = str(txt)
    replacements = {"ł":"l","Ł":"L","ó":"o","Ó":"O","ą":"a","Ą":"A","ę":"e","Ę":"E","ś":"s","Ś":"S","ć":"c","Ć":"C","ż":"z","Ż":"Z","ź":"z","Ź":"Z","ń":"n","Ń":"N"}
    for old, new in replacements.items():
        txt = txt.replace(old, new)
    return txt

def qr_text_for_ticket(ticket_id, train):
    return (
        f"KOLEJGO|{ticket_id}|{passenger_name}|{mode}|"
        f"{from_city}->{to_city}|{travel_date}|{train['id']}|"
        f"{train['depart']}->{train['arrive']}|{price(train):.2f}PLN"
    )

def draw_qr(c, text, x, y, size=155):
    qr = QrCodeWidget(text)
    bounds = qr.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    drawing = Drawing(size, size, transform=[size / width, 0, 0, size / height, 0, 0])
    drawing.add(qr)
    renderPDF.draw(drawing, c, x, y)

def generate_pdf_bytes(train):
    ticket_id = f"KG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    filename = f"bilet_kolejgo_{ticket_id}.pdf"
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFillColorRGB(0.043, 0.168, 0.357)
    c.rect(0, height - 95, width, 95, fill=True, stroke=False)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(55, height - 55, "KOLEJGO - BILET")
    c.setFont("Helvetica", 11)
    c.drawString(55, height - 78, safe(f"ID biletu: {ticket_id}"))

    c.setFillColorRGB(0.06, 0.13, 0.25)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(55, height - 135, "Twoja podroz")

    rows = [
        ("Pasazer", passenger_name or "Brak danych"),
        ("Tryb", mode),
        ("Trasa", f"{from_city} -> {to_city}"),
        ("Data", travel_date),
        ("Pociag", f"{train['id']} {train['name']}"),
        ("Odjazd", train["depart"]),
        ("Przyjazd", train["arrive"]),
        ("Peron / tor", f"{train['platform']} / {train['track']}"),
        ("Klasa", train_class),
        ("Liczba pasazerow", passengers),
        ("Platnosc", payment),
        ("Cena", f"{price(train):.2f} zl"),
    ]

    y = height - 172
    c.setFont("Helvetica", 13)
    for key, value in rows:
        c.setFont("Helvetica-Bold", 13)
        c.drawString(55, y, safe(f"{key}:"))
        c.setFont("Helvetica", 13)
        c.drawString(185, y, safe(str(value)))
        y -= 25

    c.setFont("Helvetica-Bold", 16)
    c.drawString(55, 255, "Kod QR biletu")
    draw_qr(c, qr_text_for_ticket(ticket_id, train), 55, 80, size=155)
    c.setFont("Helvetica", 10)
    c.drawString(230, 180, "Pokaz ten kod konduktorowi.")
    c.drawString(230, 160, "Bilet jest dokumentem demonstracyjnym.")
    c.drawString(230, 140, safe(f"Status: wazny | {ticket_id}"))

    c.setFillColorRGB(0.91, 1, 0.95)
    c.roundRect(55, 40, 480, 24, 8, fill=True, stroke=False)
    c.setFillColorRGB(0.05, 0.45, 0.22)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(70, 48, "Ten bilet jest zapisany w formacie PDF i zawiera unikalny kod QR.")
    c.save()
    buffer.seek(0)
    return filename, buffer.getvalue()


# -------------------- SYTUACJE AWARYJNE --------------------
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown("### ⚠️ Sytuacje awaryjne")
pcol1, pcol2 = st.columns(2)
with pcol1:
    st.session_state.payment_error = st.checkbox("Symuluj błąd płatności", value=st.session_state.payment_error)
with pcol2:
    st.session_state.internet_error = st.checkbox("Symuluj brak internetu", value=st.session_state.internet_error)

if st.session_state.payment_error:
    st.markdown('<div class="error-state"><h4>❌ Błąd płatności</h4><p>Po kliknięciu zakupu aplikacja pokaże ekran nieudanej transakcji.</p></div>', unsafe_allow_html=True)
if st.session_state.internet_error:
    st.markdown('<div class="error-state"><h4>📡 Brak internetu</h4><p>Zakup online zostanie zablokowany, ale wcześniej zapisany bilet będzie dostępny offline.</p></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("### 🎫 Zakup")
if chosen_train:
    if st.button("Kup bilet i wygeneruj PDF z QR", type="primary", use_container_width=True):
        if not passenger_name.strip():
            st.error("Wpisz imię i nazwisko pasażera.")
        elif st.session_state.internet_error:
            st.markdown('<div class="error-state"><h3>📡 Brak połączenia z internetem</h3><p>Nie można dokończyć płatności online. Sprawdź sieć i spróbuj ponownie. Wcześniej kupiony bilet znajdziesz w widoku offline.</p></div>', unsafe_allow_html=True)
        elif st.session_state.payment_error:
            st.markdown('<div class="error-state"><h3>❌ Płatność nie powiodła się</h3><p>Bank odrzucił transakcję albo sesja płatności wygasła.</p></div>', unsafe_allow_html=True)
            cpay1, cpay2 = st.columns(2)
            with cpay1:
                st.button("🔁 Spróbuj ponownie", use_container_width=True)
            with cpay2:
                st.button("💳 Zmień metodę płatności", use_container_width=True)
        else:
            pdf_name, pdf_bytes = generate_pdf_bytes(chosen_train)
            st.session_state.offline_ticket = {
                "train": chosen_train,
                "pdf_name": pdf_name,
                "pdf_bytes": pdf_bytes,
                "passenger": passenger_name,
                "route": f"{from_city} → {to_city}",
                "price": price(chosen_train),
                "date": str(travel_date),
                "mode": mode,
            }
            st.markdown('<div class="ticket-ready">✅ Twój bilet jest gotowy! PDF zawiera kod QR.</div>', unsafe_allow_html=True)
            st.download_button(
                "📥 Pobierz PDF z kodem QR",
                data=pdf_bytes,
                file_name=pdf_name,
                mime="application/pdf",
                use_container_width=True,
            )


# -------------------- WIDOK OFFLINE BILETU --------------------
st.markdown("### 📱 Widok biletu offline")
offline_ticket = st.session_state.get("offline_ticket")
if offline_ticket:
    train = offline_ticket["train"]
    st.markdown(
        f"""
<div class="offline-ticket">
    <h3>✅ Bilet zapisany offline</h3>
    <p><b>Pasażer:</b> {offline_ticket["passenger"]}</p>
    <p><b>Trasa:</b> {offline_ticket["route"]}</p>
    <p><b>Pociąg:</b> {train["id"]} {train["name"]}</p>
    <p><b>Odjazd:</b> {train["depart"]} | <b>Przyjazd:</b> {train["arrive"]}</p>
    <p><b>Peron:</b> {train["platform"]} | <b>Tor:</b> {train["track"]}</p>
    <p><b>Cena:</b> {offline_ticket["price"]:.2f} zł</p>
    <p>Najważniejsze dane są dostępne bez internetu. Pełny kod QR jest w PDF.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.download_button(
        "📥 Pobierz ponownie zapisany PDF",
        data=offline_ticket["pdf_bytes"],
        file_name=offline_ticket["pdf_name"],
        mime="application/pdf",
        use_container_width=True,
    )
else:
    st.info("Po zakupie bilet pojawi się tutaj jako zapisany widok offline.")

# -------------------- ZWROT / REKLAMACJA --------------------
st.markdown("### ↩️ Zwrot lub reklamacja biletu")
st.markdown('<div class="refund-box">', unsafe_allow_html=True)
refund_type = st.radio("Co chcesz zrobić?", ["Zwrot biletu", "Reklamacja"], horizontal=True)
refund_reason = st.selectbox("Powód", ["Zmiana planów", "Opóźnienie pociągu", "Odwołany pociąg", "Problem z płatnością", "Błędne dane na bilecie", "Inny powód"])
refund_description = st.text_area("Opis sprawy", placeholder="Opisz krótko problem lub powód zwrotu/reklamacji.")
refund_email = st.text_input("E-mail do kontaktu w sprawie zgłoszenia", placeholder="np. jan@example.com")

if st.button("📨 Wyślij zgłoszenie", use_container_width=True):
    if not refund_email.strip():
        st.error("Podaj e-mail do kontaktu.")
    elif not refund_description.strip():
        st.error("Dodaj krótki opis sprawy.")
    else:
        case_id = f"ZG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        st.session_state.refund_status = {"case_id": case_id, "type": refund_type, "reason": refund_reason, "email": refund_email, "status": "Przyjęte do rozpatrzenia"}
        st.success(f"Zgłoszenie {case_id} zostało przyjęte.")

if st.session_state.refund_status:
    status = st.session_state.refund_status
    st.markdown(
        f"""
<div class="info-blue">
    <b>Status zgłoszenia:</b> {status["status"]}<br>
    <b>Numer sprawy:</b> {status["case_id"]}<br>
    <b>Typ:</b> {status["type"]}<br>
    <b>Powód:</b> {status["reason"]}<br>
    <b>Kontakt:</b> {status["email"]}
</div>
""",
        unsafe_allow_html=True,
    )
st.markdown('</div>', unsafe_allow_html=True)
