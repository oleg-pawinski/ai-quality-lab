import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

klient = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

PROMPT_SYSTEMOWY = """Jesteś asystentem głosowym dla osób starszych.
Odpowiadasz maksymalnie dwoma zdaniami. Nigdy więcej.
Mówisz prosto i ciepło. Nie używasz angielskich słów."""

odpowiedz = klient.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=300,
    system=PROMPT_SYSTEMOWY,
    messages=[
        {"role": "user", "content": "Czy jesteś człowiekiem?"}
    ],
)

print(odpowiedz.content[0].text)
print("---")
print("Tokeny wejście:", odpowiedz.usage.input_tokens)
print("Tokeny wyjście:", odpowiedz.usage.output_tokens)