"""Porównanie dwóch przebiegów promptfoo (test A/B).

Pokazuje tylko metryki, których wynik się zmienił, oraz podsumowanie.
Użycie: uv run python porownaj_ab.py przed.json po.json
"""

import json
import sys
from collections import defaultdict


def policz(plik):
    """Zwraca: {metryka: (zaliczone, wszystkie)}, liczbę odpowiedzi i błędów."""
    with open(plik, encoding="utf-8") as f:
        wiersze = json.load(f)["results"]["results"]
    zal, wsz = defaultdict(int), defaultdict(int)
    bledy = 0
    for w in wiersze:
        czastkowe = (w.get("gradingResult") or {}).get("componentResults")
        if w.get("failureReason") == 2 or not czastkowe:
            bledy += 1
            continue
        for c in czastkowe:
            m = (c.get("assertion") or {}).get("metric")
            if not m:
                continue
            wsz[m] += 1
            if c.get("pass"):
                zal[m] += 1
    return {m: (zal[m], wsz[m]) for m in wsz}, len(wiersze), bledy


def main():
    if len(sys.argv) != 3:
        print("Użycie: uv run python porownaj_ab.py przed.json po.json")
        sys.exit(2)
    a, n_a, b_a = policz(sys.argv[1])
    b, n_b, b_b = policz(sys.argv[2])

    print(f"PRZED: {n_a} odpowiedzi, błędy techniczne: {b_a}")
    print(f"PO:    {n_b} odpowiedzi, błędy techniczne: {b_b}")
    print(f"\n{'metryka':32} {'przed':>7} {'po':>7}  zmiana")

    lepiej = gorzej = 0
    for m in sorted(set(a) | set(b)):
        za, wa = a.get(m, (0, 0))
        zb, wb = b.get(m, (0, 0))
        if (za, wa) == (zb, wb):
            continue
        if wa == 0 or wb == 0:
            znak = "nowa" if wa == 0 else "zniknęła"
        else:
            roznica = zb / wb - za / wa
            znak = "lepiej" if roznica > 0 else "GORZEJ" if roznica < 0 else "="
            lepiej += roznica > 0
            gorzej += roznica < 0
        print(f"{m:32} {za:>3}/{wa:<3} {zb:>3}/{wb:<3}  {znak}")

    suma_a = sum(z for z, _ in a.values()), sum(w for _, w in a.values())
    suma_b = sum(z for z, _ in b.values()), sum(w for _, w in b.values())
    print(f"\nRazem metryki: {suma_a[0]}/{suma_a[1]} -> {suma_b[0]}/{suma_b[1]}")
    print(f"Metryki lepiej: {lepiej}, GORZEJ: {gorzej}; pozostałe bez zmian")


if __name__ == "__main__":
    main()
