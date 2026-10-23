import json
import random

with open("kalibracja.json", encoding="utf-8") as plik:
    dane = json.load(plik)

wiersze = dane["results"]["results"]
if not wiersze:
    raise SystemExit("Brak wyników w pliku")

pozycje = []
for w in wiersze:
    try:
        pytanie = w["vars"]["pytanie"]
        kryterium = w["vars"]["kryterium"]
        odpowiedz = w["response"]["output"]
        werdykt = bool(w["success"])
    except KeyError:
        raise SystemExit(f"Inna struktura pliku. Klucze: {list(w.keys())}")
    if "klatce piersiowej" in pytanie:
        continue
    pozycje.append((pytanie, kryterium, odpowiedz, werdykt))

random.seed(7)
random.shuffle(pozycje)

with open("do_oceny.md", "w", encoding="utf-8") as plik:
    for numer, (pytanie, kryterium, odpowiedz, _) in enumerate(pozycje, start=1):
        plik.write(f"## {numer}\n\n")
        plik.write(f"**Pytanie:** {pytanie}\n\n")
        plik.write(f"**Kryterium:** {kryterium}\n\n")
        plik.write(f"**Odpowiedź:** {odpowiedz}\n\n---\n\n")

with open("klucz_sedziego.json", "w", encoding="utf-8") as plik:
    json.dump([p[3] for p in pozycje], plik)

print(f"Gotowe: {len(pozycje)} odpowiedzi do oceny w pliku do_oceny.md.")
print("NIE otwieraj klucz_sedziego.json przed ocenieniem.")