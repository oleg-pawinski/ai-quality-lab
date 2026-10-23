import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
klient = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

PROMPT_SYSTEMOWY = """Jesteś asystentem głosowym dla osób starszych.
Odpowiadasz maksymalnie trzema zdaniami.
Mówisz prosto i ciepło. Nie używasz angielskich słów."""

with open("sondy.json", encoding="utf-8") as plik:
    sondy = json.load(plik)

wyniki = []

for numer, sonda in enumerate(sondy, start=1):
    print(f"[{numer}/{len(sondy)}] {sonda['obszar']}...")

    odpowiedz = klient.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=400,
        system=PROMPT_SYSTEMOWY,
        messages=[{"role": "user", "content": sonda["pytanie"]}],
    )

    wyniki.append({
        "obszar": sonda["obszar"],
        "pytanie": sonda["pytanie"],
        "kryterium": sonda["kryterium"],
        "odpowiedz": odpowiedz.content[0].text,
        "tokeny_wejscie": odpowiedz.usage.input_tokens,
        "tokeny_wyjscie": odpowiedz.usage.output_tokens,
    })

with open("wyniki.json", "w", encoding="utf-8") as plik:
    json.dump(wyniki, plik, ensure_ascii=False, indent=2)

koszt = sum(w["tokeny_wyjscie"] for w in wyniki)
print(f"Gotowe: {len(wyniki)} sond, {koszt} tokenów wyjściowych.")