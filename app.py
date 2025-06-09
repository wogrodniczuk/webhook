from flask import Flask, request, jsonify
import re
import os
from openai import OpenAI

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

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

# Mapping for number words to digits
NUMBER_WORDS = {
    "jedno": 1,
    "jeden": 1,
    "dwa": 2,
    "trzy": 3,
    "cztery": 4,
    "pięć": 5,
    "sześć": 6,
    "siedem": 7,
    "osiem": 8,
    "dziewięć": 9,
    "dziesięć": 10,
}

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    instruction = data.get("instruction", "").lower()
    print(f"DEBUG: Raw instruction: '{instruction}'")

    # Use OpenAI to interpret the instruction
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful drone navigation assistant. Your task is to extract only the sequence of drone movements from a given natural language instruction. Output each movement on a new line. For example, if the instruction is 'poleciałem jedno pole w prawo, a później na sam dół', output 'prawo 1\ndół na sam'. For 'poleciałem dwa pola w lewo', output 'lewo 2'. For 'poleciałem w górę', output 'góra 1'. For 'na samą górę', output 'góra na sam'. For 'na sam dół', output 'dół na sam'. For 'poleciałem prawo ile tylko możemy', output 'prawo na sam'. If the instruction contains 'na maksa' or 'ile wlezie', interpret it as 'na sam'. Make sure to only output the movements."},
                {"role": "user", "content": instruction}
            ]
        )
        # Assuming the model returns movements in the format "direction steps" or "direction na sam"
        # e.g., "prawo 1\ndół na sam"
        openai_interpreted_instruction = completion.choices[0].message.content.strip()
        print(f"DEBUG: OpenAI interpreted instruction: '{openai_interpreted_instruction}'")
        # Normalize literal \n to actual newlines before splitting
        openai_interpreted_instruction = openai_interpreted_instruction.replace("\\n", "\n")
        
        # Split instructions by new line and process each movement
        movement_commands = [cmd.strip() for cmd in re.split(r'[\r\n]+', openai_interpreted_instruction) if cmd.strip()]

    except Exception as e:
        # Fallback to original parsing if OpenAI call fails
        print(f"OpenAI interpretation failed: {e}. Falling back to regex parsing.")
        
        # Pre-process the instruction for fallback to match OpenAI's expected output format
        fallback_processed_instruction = instruction
        # Handle "ile tylko możemy" by transforming it to "na sam"
        fallback_processed_instruction = re.sub(r"(\w+)\s*ile tylko możemy", r"\1 na sam", fallback_processed_instruction)
        # Handle "na sam X" cases by transforming them to "X na sam"
        fallback_processed_instruction = re.sub(r"na sam (góra|dół|prawo|lewo)", r"\1 na sam", fallback_processed_instruction)
        
        # If OpenAI fails, split the pre-processed instruction into commands
        movement_commands = [cmd.strip() for cmd in re.split(r'[\r\n]+', fallback_processed_instruction) if cmd.strip()]
        # If after splitting, it's still empty, then use the original instruction as a single command
        if not movement_commands:
            movement_commands = [instruction]
        print(f"DEBUG: Fallback movement commands: {movement_commands}")

    pos_y, pos_x = 0, 0

    # Parsowanie poleceń (adapted for OpenAI output or fallback)
    # The pattern will now look for "direction [steps]" or "direction na sam"
    pattern = r"(prawo|lewo|góra|dół|na prawo|na lewo|do góry|na dół|w górę)\s*(\d+|jedno|jeden|dwa|trzy|cztery|pięć|sześć|siedem|osiem|dziewięć|dziesięć|na sam)?"

    for command in movement_commands:
        print(f"DEBUG: Attempting to parse command: '{command}' (len: {len(command)}, repr: {repr(command)})")
        match = re.search(pattern, command)
        if match:
            direction = match.group(1).strip()
            number_or_phrase = match.group(2) if match.group(2) else "1" # Default to 1 step if no number/phrase

            steps = 1
            if number_or_phrase == "na sam":
                # Will be handled by the 'na sam' logic below
                pass
            elif number_or_phrase in NUMBER_WORDS:
                steps = NUMBER_WORDS[number_or_phrase]
            elif number_or_phrase.isdigit():
                steps = int(number_or_phrase)

            dy, dx = MOVES.get(direction, (0, 0))

            # Przesuwamy się krok po kroku
            if number_or_phrase == "na sam": # Check the number_or_phrase for 'na sam'
                # Move to the boundary
                if dy == 1: # Moving down
                    steps = MAX_Y - 1 - pos_y
                elif dy == -1: # Moving up
                    steps = pos_y
                elif dx == 1: # Moving right
                    steps = MAX_X - 1 - pos_x
                elif dx == -1: # Moving left
                    steps = pos_x
                else:
                    steps = 0 # No movement, or invalid direction for 'na sam'

            for _ in range(steps):
                new_y = pos_y + dy
                new_x = pos_x + dx
                if 0 <= new_y < MAX_Y and 0 <= new_x < MAX_X:
                    pos_y, pos_x = new_y, new_x
                else:
                    break # Stop if we hit a boundary
        else:
            print(f"ERROR: Could not parse movement from: '{command}' (len: {len(command)}, repr: {repr(command)})")

    # Opis aktualnego pola
    description = MAP_DESCRIPTION[pos_y][pos_x]

    # Odpowiedź
    response = {
        "description": description
    }
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
