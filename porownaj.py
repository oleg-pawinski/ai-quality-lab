import json

with open("oceny.txt", encoding="utf-8") as plik:
    moje = [linia.strip().lower() == "tak" for linia in plik if linia.strip()]

with open("klucz_sedziego.json", encoding="utf-8") as plik:
    sedzia = json.load(plik)

if len(moje) != len(sedzia):
    raise SystemExit(f"Masz {len(moje)} ocen, a powinno być {len(sedzia)}")

zgodne = sum(a == b for a, b in zip(moje, sedzia))
print(f"Zgodność: {zgodne}/{len(sedzia)} ({100 * zgodne // len(sedzia)}%)")
for numer, (a, b) in enumerate(zip(moje, sedzia), start=1):
    if a != b:
        print(f"Rozbieżność w odpowiedzi {numer}: ja={'tak' if a else 'nie'}, sędzia={'tak' if b else 'nie'}")