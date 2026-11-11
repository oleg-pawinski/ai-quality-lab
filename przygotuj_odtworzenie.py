"""Przygotowuje testy do ponownej oceny ZAPISANYCH odpowiedzi bota.

Bierze zapisany przebieg promptfoo (odpowiedzi bota) i aktualne sondy
(kryteria). Każda zapisana odpowiedź staje się osobnym testem z aktualnymi
kryteriami. Bot nie jest wywoływany ponownie, więc różnica między sędziami
nie miesza się z szumem bota.

Użycie:
  uv run python przygotuj_odtworzenie.py WYNIKI.json TESTY.json sondy/a.json [sondy/b.json ...]

UWAGA: TESTY.json zawiera odpowiedzi bota. Jeśli to kopia produkcji,
plik jest poufny i musi być w .gitignore.
"""

import json
import sys
from collections import Counter


def wczytaj_sondy(pliki):
    """Zwraca {opis sondy: sonda} z aktualnych plików sond."""
    sondy = {}
    for plik in pliki:
        with open(plik, encoding="utf-8") as f:
            for sonda in json.load(f):
                opis = sonda["description"]
                if opis in sondy:
                    print(f"UWAGA: opis „{opis}” powtarza się w sondach – biorę ostatni")
                sondy[opis] = sonda
    return sondy


def main():
    if len(sys.argv) < 4:
        print("Użycie: uv run python przygotuj_odtworzenie.py WYNIKI.json TESTY.json sondy/a.json [...]")
        sys.exit(2)
    plik_wynikow, plik_testow, pliki_sond = sys.argv[1], sys.argv[2], sys.argv[3:]

    sondy = wczytaj_sondy(pliki_sond)
    with open(plik_wynikow, encoding="utf-8") as f:
        wiersze = json.load(f)["results"]["results"]

    testy, pominiete, licznik = [], [], Counter()
    for w in wiersze:
        opis = (w.get("testCase") or {}).get("description", "")
        odpowiedz = (w.get("response") or {}).get("output")
        if w.get("failureReason") == 2 or not isinstance(odpowiedz, str) or not odpowiedz.strip():
            pominiete.append(f"{opis} – błąd techniczny albo brak odpowiedzi")
            continue
        if opis not in sondy:
            pominiete.append(f"{opis} – brak takiej sondy w podanych plikach")
            continue
        licznik[opis] += 1
        sonda = sondy[opis]
        zmienne = dict(sonda.get("vars", {}))
        zmienne["odpowiedz"] = odpowiedz
        testy.append({
            "description": f"{opis} #{licznik[opis]}",
            "vars": zmienne,
            "assert": sonda["assert"],
        })

    with open(plik_testow, "w", encoding="utf-8") as f:
        json.dump(testy, f, ensure_ascii=False, indent=2)

    print(f"Zapisane odpowiedzi w {plik_wynikow}: {len(wiersze)}")
    print(f"Testów do ponownej oceny: {len(testy)} (sond: {len(licznik)})")
    for opis, n in sorted(licznik.items()):
        print(f"  {opis}: {n} odp.")
    if pominiete:
        print(f"Pominięte: {len(pominiete)}")
        for p in pominiete:
            print(f"  {p}")
    print(f"Zapisano: {plik_testow}")


if __name__ == "__main__":
    main()
