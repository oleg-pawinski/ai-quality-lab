# Buduje wiadomosci dla Gemini w tej samej kolejnosci co serwer Herbatnika:
# prompt systemowy -> imie i nazwisko -> dzisiejsza data -> fakty o uzytkowniku.
# Prawdziwy prompt jest w herbatnik-prompt.txt (tylko lokalnie, w .gitignore).
# Uzytkownik i fakty sa ZMYSLONE.

import json
from datetime import date
from pathlib import Path

IMIE_I_NAZWISKO = "Tadeusz Nowicki"

FAKTY = [
    "- wnuczka: odwiedza w niedziele (kategoria: person)",
    "- ulubione_zajecie: praca w ogrodku (kategoria: preference)",
    "- spacer: codziennie rano z psem (kategoria: routine)",
    "- pies: ma psa (kategoria: other)",
    "- relacja: spacer -> pies (DOES)",
]

DNI = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
MIESIACE = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca",
            "sierpnia", "września", "października", "listopada", "grudnia"]


def data_po_polsku(d):
    return f"Dzisiaj jest {DNI[d.weekday()]}, {d.day} {MIESIACE[d.month - 1]} {d.year}"


def zbuduj(context):
    pytanie = context["vars"]["pytanie"]
    # Sonda moze podac wlasne imie w zmiennej "imie"; domyslnie Tadeusz Nowicki.
    imie = context["vars"].get("imie", IMIE_I_NAZWISKO)
    sciezka = Path(__file__).parent / "herbatnik-prompt.txt"
    prompt = sciezka.read_text(encoding="utf-8")

    dzis = data_po_polsku(date.today())
    fakty = "\n".join(FAKTY)

    # Brzmienie zdania o imieniu jest nasze, nie produkcyjne.
    system = "\n\n".join([
        prompt,
        f"Rozmawiasz z osobą o imieniu i nazwisku: {imie}. "
        "Zwracaj się do niej po imieniu. Nigdy nie używaj znaczników takich jak [IMIĘ].",
        dzis,
        "Fakty o użytkowniku:\n" + fakty,
    ])

    return json.dumps([
        {"role": "system", "content": system},
        {"role": "user", "content": pytanie},
    ], ensure_ascii=False)
