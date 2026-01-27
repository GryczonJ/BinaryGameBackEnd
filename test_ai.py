import os
import json
import sys

# Ensure local imports work when running as a script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from routers.ai import get_possible_moves
from ai_model import generate_hint_text


def main():
    # Set your model path here or via AI_MODEL_PATH env var
    model_path = os.getenv("AI_MODEL_PATH", "./model/gemma-2-2b-it-Q4_K_M.gguf")
    print(f"Using model path: {model_path}")

    # Example 6x6 puzzle grid (None means empty)
    grid = [
        [0,     1,      None,   1,      0,      None],
        [1,     0,      None,   None,   None,   None],
        [None,  None,   0,      0,      1,      None],
        [0,     1,      None,   1,      None,   0],
        [0,     None,   1,      None,   None,   None],
        [None,  None,   1,      1,      0,      1],
    ]
    grid2 = [
        [0,     None,   None,   None,   0,      None],
        [None,  None,   None,   None,   None,   None],
        [None,  None,   None,   0,      None,   None],
        [None,  None,   None,   None,   None,   0],
        [None,  None,   None,   None,   None,   None],
        [None,  None,   None,   1,      0,      1],
    ]
    size = len(grid)

    grid_json = json.dumps(grid)
    hints = get_possible_moves(grid_json, size)

    print("Possible hints (rule-based):")
    for h in hints:
        print(f" - Row {h['row']+1}, Col {h['col']}: put {h['value']} ({h['reason']})")

    print("\nAI response:")
    try:
        hint_text = generate_hint_text(grid=grid_json, hints=hints)
        print(hint_text)
    except FileNotFoundError as e:
        print("Model not found. Download the GGUF first:")
        print("  huggingface-cli download bartowski/gemma-2-2b-it-GGUF gemma-2-2b-it-Q4_K_M.gguf --local-dir ./models")
        print(f"Details: {e}")


if __name__ == "__main__":
    main()
