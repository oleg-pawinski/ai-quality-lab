import json

with open("sondy.json", encoding="utf-8") as plik:
    sondy = json.load(plik)

przypadki = []
for sonda in sondy:
    przypadki.append({
        "description": sonda["obszar"],
        "vars": {
            "pytanie": sonda["pytanie"],
            "kryterium": sonda["kryterium"],
        },
    })

with open("przypadki.json", "w", encoding="utf-8") as plik:
    json.dump(przypadki, plik, ensure_ascii=False, indent=2)

print(f"Zapisano {len(przypadki)} przypadków.")