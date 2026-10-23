import json
import sys
from collections import defaultdict

plik = sys.argv[1] if len(sys.argv) > 1 else "wyniki_metryki.json"
szukaj = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None
metryka_powody = sys.argv[3] if len(sys.argv) > 3 else None

with open(plik, encoding="utf-8") as f:
    dane = json.load(f)

wiersze = dane["results"]["results"]


def czy_blad(w):
    if w.get("failureReason") == 2:
        return True
    czastkowe = (w.get("gradingResult") or {}).get("componentResults")
    return not czastkowe


bledy = [w for w in wiersze if czy_blad(w)]
poprawne = [w for w in wiersze if not czy_blad(w)]

suma = defaultdict(float)
ile = defaultdict(int)
powody = []

for w in poprawne:
    for c in w["gradingResult"]["componentResults"]:
        metryka = (c.get("assertion") or {}).get("metric")
        if not metryka:
            continue
        wynik = c.get("score")
        if wynik is None:
            wynik = 1.0 if c.get("pass") else 0.0
        suma[metryka] += float(wynik)
        ile[metryka] += 1
        if metryka == metryka_powody and not c.get("pass"):
            powody.append(c.get("reason", "(brak uzasadnienia)"))

zaliczone = sum(1 for w in poprawne if w.get("success"))
print(f"Odpowiedzi: {len(wiersze)}, w tym błędy techniczne: {len(bledy)}")
print(f"Zaliczone (spośród ocenionych): {zaliczone} z {len(poprawne)}\n")

if bledy:
    print("Błędy techniczne (nie liczone w metrykach):")
    for w in bledy:
        pytanie = w.get("vars", {}).get("pytanie", "")[:60]
        print(f"- {pytanie}...: {str(w.get('error'))[:120]}")
    print()

print(f"{'metryka':32} wynik")
for m in sorted(suma):
    print(f"{m:32} {suma[m]:.2f} / {ile[m]}")

if szukaj:
    print(f"\nOdpowiedzi na sondy z pytaniem zawierającym '{szukaj}':")
    for w in poprawne:
        if szukaj.lower() in w.get("vars", {}).get("pytanie", "").lower():
            print("-", w["response"]["output"].replace("\n", " "))

if metryka_powody:
    print(f"\nUzasadnienia porażek dla '{metryka_powody}':")
    for p in powody:
        print("-", p.replace("\n", " "))