from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Mapa
MAP_DESCRIPTION = [
    ["punkt startowy", "trawa", "drzewo", "dom"],
    ["trawa", "wiatrak", "trawa", "trawa"],
    ["trawa", "trawa", "skały", "dwa drzewa"],
    ["góry", "góry", "samochód", "jaskinia"],
]

# Rozmiar mapy
MAX_Y = len(MAP_DESCRIPTION)
MAX_X = len(MAP_DESCRIPTION[0])

# Ruchy
MOVES = {
    "prawo": (0, 1),
    "lewo": (0, -1),
    "góra": (-1, 0),
    "dół": (1, 0),
    "do góry": (-1, 0),
    "w górę": (-1, 0),
    "na dół": (1, 0),
    "na lewo": (0, -1),
    "na prawo": (0, 1),
}

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    instruction = data.get("instruction", "").lower()

    # Zaczynamy od punktu startowego
    pos_y, pos_x = 0, 0

    # Parsowanie poleceń
    pattern = r"(\d+)?\s*(pole|pola)?\s*(w\s)?(prawo|lewo|góra|dół|na prawo|na lewo|do góry|na dół|w górę)"
    matches = re.findall(pattern, instruction)

    for match in matches:
        number_str, _, _, direction = match
        steps = int(number_str) if number_str else 1

        dy, dx = MOVES.get(direction.strip(), (0, 0))

        # Przesuwamy się krok po kroku
        for _ in range(steps):
            new_y = pos_y + dy
            new_x = pos_x + dx
            if 0 <= new_y < MAX_Y and 0 <= new_x < MAX_X:
                pos_y, pos_x = new_y, new_x

    # Opis aktualnego pola
    description = MAP_DESCRIPTION[pos_y][pos_x]

    # Odpowiedź
    response = {
        "description": description,
        "debug_position": [pos_y, pos_x],
        "instruction_parsed": matches
    }
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
