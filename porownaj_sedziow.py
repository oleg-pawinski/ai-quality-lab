"""Porównanie dwóch sędziów na TYCH SAMYCH zapisanych odpowiedziach bota.

Wejście: dwa przebiegi promptfoo z odtworzenia (odtworzenie-stary.yaml
i odtworzenie-nowy.yaml). Porównuje werdykt po werdykcie (odpowiedź + metryka).
Liczą się tylko oceny sędziego (llm-rubric); reguły (np. not-regex) dają
zawsze ten sam wynik, więc są pokazane osobno tylko dla kontroli.

Użycie:
  uv run python porownaj_sedziow.py STARY.json NOWY.json
"""

import json
import sys
from collections import defaultdict


def wczytaj(plik):
    """Zwraca {(odpowiedź, metryka): (zaliczone, typ, powód)} i liczbę błędów."""
    with open(plik, encoding="utf-8") as f:
        wiersze = json.load(f)["results"]["results"]
    werdykty, bledy = {}, 0
    for w in wiersze:
        opis = (w.get("testCase") or {}).get("description", "?")
        czastkowe = (w.get("gradingResult") or {}).get("componentResults")
        if w.get("failureReason") == 2 or not czastkowe:
            bledy += 1
            continue
        for c in czastkowe:
            asercja = c.get("assertion") or {}
            metryka = asercja.get("metric")
            if not metryka:
                continue
            powod = " ".join((c.get("reason") or "").split())
            werdykty[(opis, metryka)] = (bool(c.get("pass")), asercja.get("type", "?"), powod)
    return werdykty, len(wiersze), bledy


def main():
    if len(sys.argv) != 3:
        print("Użycie: uv run python porownaj_sedziow.py STARY.json NOWY.json")
        sys.exit(2)
    stary, n_s, b_s = wczytaj(sys.argv[1])
    nowy, n_n, b_n = wczytaj(sys.argv[2])
    print(f"STARY: {n_s} odpowiedzi, błędy techniczne: {b_s}")
    print(f"NOWY:  {n_n} odpowiedzi, błędy techniczne: {b_n}")

    wspolne = sorted(set(stary) & set(nowy))
    brakujace = len(set(stary) ^ set(nowy))
    if brakujace:
        print(f"UWAGA: {brakujace} werdyktów jest tylko w jednym pliku – pomijam je")

    zgodne = wszystkie = reguly_zgodne = reguly = 0
    per_metryka = defaultdict(lambda: [0, 0, 0])  # stary zal., nowy zal., liczba
    roznice = []
    for klucz in wspolne:
        p_s, typ, powod_s = stary[klucz]
        p_n, _, powod_n = nowy[klucz]
        if typ != "llm-rubric":
            reguly += 1
            reguly_zgodne += p_s == p_n
            continue
        wszystkie += 1
        zgodne += p_s == p_n
        m = per_metryka[klucz[1]]
        m[0] += p_s
        m[1] += p_n
        m[2] += 1
        if p_s != p_n:
            roznice.append((klucz, p_s, p_n, powod_s, powod_n))

    print(f"\nOceny sędziego: zgodne {zgodne}/{wszystkie}")
    print(f"Reguły (kontrola, powinno być 100%): zgodne {reguly_zgodne}/{reguly}")

    print(f"\n{'metryka':28} {'stary':>7} {'nowy':>7}")
    for metryka, (z_s, z_n, n) in sorted(per_metryka.items()):
        znak = "" if z_s == z_n else "  <- różnica"
        print(f"{metryka:28} {z_s:>3}/{n:<3} {z_n:>3}/{n:<3}{znak}")

    if roznice:
        print(f"\nRóżnice ({len(roznice)}):")
        for (opis, metryka), p_s, p_n, powod_s, powod_n in roznice:
            tak = lambda p: "zalicza" if p else "NIE zalicza"
            print(f"\n- {opis} | {metryka}: stary {tak(p_s)}, nowy {tak(p_n)}")
            print(f"  stary: {powod_s[:220]}")
            print(f"  nowy:  {powod_n[:220]}")


if __name__ == "__main__":
    main()
