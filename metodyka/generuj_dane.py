"""Generuje przykładowe, celowo zabrudzone dane sprzedaży detalicznej do demo Osmos.

Dane są w pełni syntetyczne (stały seed), nie pochodzą od żadnego klienta.
Uruchomienie: python generuj_dane.py  -> pliki w ..\\dane\\raw
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(2026)
OUT = Path(__file__).resolve().parent.parent / "dane" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

MIASTA = ["Warszawa", "Kraków", "Wrocław", "Poznań", "Gdańsk", "Łódź", "Katowice", "Lublin"]
SEGMENTY = ["Standard", "Premium", "Business"]
KATEGORIE = {
    "Elektronika": (199, 4999),
    "AGD": (149, 3499),
    "Odzież": (29, 499),
    "Dom i ogród": (19, 899),
    "Sport": (39, 1299),
}
IMIONA = ["Anna", "Piotr", "Katarzyna", "Tomasz", "Magdalena", "Michał", "Agnieszka", "Paweł", "Ewa", "Marcin"]
NAZWISKA = ["Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kamiński", "Lewandowski", "Zieliński", "Szymański"]

N_KLIENCI, N_PRODUKTY, N_SKLEPY, N_ZAMOWIENIA = 2000, 300, 12, 50000
problemy = {}


def licz(nazwa):
    problemy[nazwa] = problemy.get(nazwa, 0) + 1


# sklepy
sklepy = []
for i in range(1, N_SKLEPY + 1):
    sklepy.append({"store_id": f"S{i:03d}", "store_name": f"Sklep {MIASTA[(i - 1) % len(MIASTA)]} {i}",
                   "city": MIASTA[(i - 1) % len(MIASTA)], "channel": "online" if i == N_SKLEPY else "stationary"})

# klienci
klienci = []
for i in range(1, N_KLIENCI + 1):
    email = f"klient{i}@example.com"
    if random.random() < 0.02:
        email = email.upper()
        licz("customers: e-mail wielkimi literami")
    seg = random.choices(SEGMENTY, weights=[70, 20, 10])[0]
    if random.random() < 0.03:
        seg = seg.lower() + " "
        licz("customers: segment małymi literami / ze spacją")
    city = random.choice(MIASTA)
    if random.random() < 0.02:
        city = ""
        licz("customers: puste miasto")
    klienci.append({"customer_id": f"C{i:05d}", "first_name": random.choice(IMIONA), "last_name": random.choice(NAZWISKA),
                    "email": email, "city": city, "segment": seg,
                    "signup_date": (date(2022, 1, 1) + timedelta(days=random.randint(0, 1200))).isoformat()})
for k in random.sample(klienci, 40):
    klienci.append(dict(k))
    licz("customers: zduplikowany wiersz")

# produkty
produkty = []
for i in range(1, N_PRODUKTY + 1):
    kat = random.choice(list(KATEGORIE))
    lo, hi = KATEGORIE[kat]
    price = round(random.uniform(lo, hi), 2)
    price_txt = f"{price:.2f}"
    if random.random() < 0.05:
        price_txt = price_txt.replace(".", ",")
        licz("products: cena z przecinkiem dziesiętnym")
    produkty.append({"product_id": f"P{i:04d}", "product_name": f"{kat} model {i}", "category": kat,
                     "list_price": price_txt, "active": random.choice(["true", "true", "true", "false"])})

# zamówienia (ok. 2 lata)
start = date(2024, 11, 1)
zamowienia = []
for i in range(1, N_ZAMOWIENIA + 1):
    d = start + timedelta(days=random.randint(0, 729))
    prod = random.choice(produkty)
    price = float(prod["list_price"].replace(",", "."))
    qty = random.choices([1, 2, 3, 4, 5], weights=[60, 20, 10, 6, 4])[0]
    discount = random.choice([0, 0, 0, 0.05, 0.1, 0.2])
    order_date = d.isoformat()
    if random.random() < 0.04:
        order_date = d.strftime("%d.%m.%Y")
        licz("orders: data w formacie DD.MM.RRRR")
    cust = random.choice(klienci)["customer_id"]
    if random.random() < 0.01:
        cust = ""
        licz("orders: brak customer_id")
    elif random.random() < 0.005:
        cust = f"C{random.randint(90000, 99999)}"
        licz("orders: customer_id spoza słownika klientów")
    status = random.choices(["completed", "returned", "cancelled"], weights=[90, 7, 3])[0]
    if random.random() < 0.01:
        qty = -qty
        licz("orders: ujemna ilość")
    zamowienia.append({"order_id": f"O{i:07d}", "order_date": order_date, "customer_id": cust,
                       "product_id": prod["product_id"], "store_id": random.choice(sklepy)["store_id"],
                       "quantity": qty, "unit_price": f"{price:.2f}", "discount": discount, "status": status})
for z in random.sample(zamowienia, 250):
    zamowienia.append(dict(z))
    licz("orders: zduplikowane zamówienie")
random.shuffle(zamowienia)


def zapisz(nazwa, wiersze, sep=","):
    with open(OUT / nazwa, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(wiersze[0]), delimiter=sep)
        w.writeheader()
        w.writerows(wiersze)
    print(f"{nazwa}: {len(wiersze)} wierszy")


zapisz("stores.csv", sklepy)
zapisz("customers.csv", klienci)
zapisz("products.csv", produkty, sep=";")
# zamówienia w dwóch plikach, jak z dwóch eksportów miesięcznych
pol = len(zamowienia) // 2
(OUT / "orders").mkdir(exist_ok=True)
for idx, czesc in enumerate([zamowienia[:pol], zamowienia[pol:]], 1):
    zapisz(f"orders/orders_part{idx}.csv", czesc)

with open(OUT.parent / "wstrzykniete_problemy.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["problem", "liczba"])
    for k, v in sorted(problemy.items()):
        w.writerow([k, v])
print("Zapisano wstrzykniete_problemy.csv")
