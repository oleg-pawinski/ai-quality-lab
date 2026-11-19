# Lancuch Herbatnika lokalnie - to, co zobaczylby senior:
#   guardrail1 (wiadomosc seniora) -> glowny model -> guardrail2 (odpowiedz modelu) -> odpowiedz albo fallback
# Kolejnosc jak na serwerze (opis od Jedrka). Anonimizacje pomijamy - dane w sondach sa zmyslone.
#
# Prompty guardraili i fallbacki sa POUFNE: guardrail1.txt, guardrail2.txt, fallbacki.json
# (tylko lokalnie, w .gitignore). Ten plik ich nie zawiera, tylko je wczytuje.
#
# Uzycie: provider "file://lancuch.py" w herbatnik-lancuch.yaml.
# Wynik: output = tekst dla seniora; metadata = werdykty guardraili i surowa odpowiedz modelu;
#        tokenUsage = suma tokenow Gemini (promptfoo pokazuje ja na koncu przebiegu).
#
# Oszczednosc: werdykt guardrail1 zalezy tylko od wiadomosci seniora i promptu guardrail1,
# wiec jest zapamietywany w folderze cache_guardrail1/ (lokalnie, .gitignore).
# Zmiana promptu guardrail1 = nowy klucz = automatycznie nowe pytanie.
# UWAGA: z pamiecia powtorzenia (--repeat 3) nie pokaza, czy guardrail1 jest stabilny.
# Do pomiaru samego guardrail1 wylacz pamiec:  $env:LANCUCH_G1_CACHE="0"

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

FOLDER = Path(__file__).parent
MODEL = "gemini-3.5-flash"  # jak na produkcji (po stronie Google kierowany do 3.6)
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
CACHE_G1 = FOLDER / "cache_guardrail1"


def klucz():
    k = os.environ.get("GOOGLE_API_KEY")
    if k:
        return k
    # promptfoo zwykle przekazuje .env; gdyby nie - czytamy go sami (klucz zostaje na komputerze)
    for linia in (FOLDER / ".env").read_text(encoding="utf-8").splitlines():
        if linia.strip().startswith("GOOGLE_API_KEY="):
            return linia.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("Brak GOOGLE_API_KEY")


def gemini(tekst, system=None, wyszukiwarka=False):
    """Jedno wywolanie Gemini. Zwraca (tekst, tokeny). Ponawia przy 429/5xx i timeoucie, max 3 proby."""
    body = {"contents": [{"role": "user", "parts": [{"text": tekst}]}]}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if wyszukiwarka:
        body["tools"] = [{"google_search": {}}]
    dane = json.dumps(body).encode("utf-8")

    for proba in range(3):
        req = urllib.request.Request(
            URL.format(MODEL),
            data=dane,
            headers={"Content-Type": "application/json", "x-goog-api-key": klucz()},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                odp = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and proba < 2:
                time.sleep(5 * (proba + 1))
                continue
            raise RuntimeError(f"Gemini HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
        except (urllib.error.URLError, TimeoutError) as e:
            if proba < 2:
                time.sleep(5 * (proba + 1))
                continue
            raise RuntimeError(f"Gemini - brak polaczenia: {e}")

        kandydat = (odp.get("candidates") or [{}])[0]
        czesci = kandydat.get("content", {}).get("parts", [])
        tekst_odp = "".join(c.get("text", "") for c in czesci if not c.get("thought")).strip()
        if not tekst_odp:
            raise RuntimeError(f"Gemini - pusta odpowiedz (finishReason: {kandydat.get('finishReason')})")
        u = odp.get("usageMetadata", {})
        tokeny = {
            "wejscie": u.get("promptTokenCount", 0),
            "wyjscie": u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0),
            "z_cache_google": u.get("cachedContentTokenCount", 0),
        }
        return tekst_odp, tokeny


def guardrail1(g1_prompt, pytanie):
    """Werdykt guardrail1 z pamieci albo z Gemini. Zwraca (tekst, tokeny, z_pamieci)."""
    wlaczona = os.environ.get("LANCUCH_G1_CACHE", "1") != "0"
    klucz_pamieci = hashlib.sha256((g1_prompt + "\n---\n" + pytanie).encode("utf-8")).hexdigest()[:24]
    plik = CACHE_G1 / f"{klucz_pamieci}.txt"
    if wlaczona and plik.exists():
        return plik.read_text(encoding="utf-8"), {"wejscie": 0, "wyjscie": 0, "z_cache_google": 0}, True
    tekst, tokeny = gemini(g1_prompt.replace("{{user_message}}", pytanie))
    if wlaczona and werdykt(tekst)[0] != "NIEZNANY":  # nieczytelnego werdyktu nie zapamietujemy
        CACHE_G1.mkdir(exist_ok=True)
        plik.write_text(tekst, encoding="utf-8")
    return tekst, tokeny, False


def werdykt(tekst):
    """Zamienia odpowiedz guardraila na (werdykt, szczegol). Nieczytelny werdykt -> NIEZNANY."""
    linia = tekst.strip().strip("`").strip().splitlines()[0].strip().strip("`").strip()
    if linia == "PASS":
        return "PASS", ""
    if linia == "SOS":
        return "SOS", ""
    if linia.startswith("BLOCKED:"):
        return "BLOCKED", linia[len("BLOCKED:"):].strip()
    return "NIEZNANY", linia


def call_api(prompt, options, context):
    meta = {"tokeny": {}}

    def wynik(slownik):
        # suma tokenow wszystkich krokow -> promptfoo pokazuje ja w podsumowaniu
        we = sum(t["wejscie"] for t in meta["tokeny"].values())
        wy = sum(t["wyjscie"] for t in meta["tokeny"].values())
        slownik["tokenUsage"] = {"prompt": we, "completion": wy, "total": we + wy}
        slownik["metadata"] = meta
        return slownik

    try:
        wiadomosci = json.loads(prompt)  # z herbatnik_prompt.py: [system, user]
        system = next(w["content"] for w in wiadomosci if w["role"] == "system")
        pytanie = next(w["content"] for w in wiadomosci if w["role"] == "user")

        # 1. guardrail1 - ocenia wiadomosc seniora
        g1 = (FOLDER / "guardrail1.txt").read_text(encoding="utf-8")
        meta["guardrail1"], meta["tokeny"]["guardrail1"], meta["g1_z_pamieci"] = guardrail1(g1, pytanie)
        w1, powod1 = werdykt(meta["guardrail1"])
        if w1 == "NIEZNANY":
            return wynik({"error": f"guardrail1 - nieczytelny werdykt: {meta['guardrail1'][:200]}"})
        if w1 == "SOS":
            meta["etap"] = "SOS"
            return wynik({"output": "[OKNO SOS] Guardrail1 zatrzymal lancuch. Senior widzi okno 'Zadzwon na SOS'."})
        if w1 == "BLOCKED":
            meta["etap"] = "BLOKADA_WEJSCIA"
            return wynik({"output": f"[BLOKADA WEJSCIA] {powod1}"})

        # 2. glowny model - jak w herbatnik.yaml, z wyszukiwarka Google
        meta["odpowiedz_modelu"], meta["tokeny"]["model"] = gemini(pytanie, system=system, wyszukiwarka=True)

        # 3. guardrail2 - widzi TYLKO odpowiedz modelu, bez pytania seniora
        g2 = (FOLDER / "guardrail2.txt").read_text(encoding="utf-8")
        meta["guardrail2"], meta["tokeny"]["guardrail2"] = gemini(g2.replace("{{assistant_response}}", meta["odpowiedz_modelu"]))
        w2, kategoria = werdykt(meta["guardrail2"])
        if w2 not in ("PASS", "BLOCKED"):
            return wynik({"error": f"guardrail2 - nieczytelny werdykt: {meta['guardrail2'][:200]}"})
        if w2 == "BLOCKED":
            fallbacki = json.loads((FOLDER / "fallbacki.json").read_text(encoding="utf-8"))
            tekst = fallbacki.get(f"fallback_{kategoria}")
            if tekst is None:
                return wynik({"error": f"guardrail2 - nieznana kategoria: {kategoria}"})
            meta["etap"] = f"FALLBACK_{kategoria}"
            return wynik({"output": tekst})

        meta["etap"] = "ODPOWIEDZ_MODELU"
        return wynik({"output": meta["odpowiedz_modelu"]})

    except Exception as e:
        return wynik({"error": f"{type(e).__name__}: {e}"})
