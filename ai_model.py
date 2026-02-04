from llama_cpp import Llama
import json
import os
import random

# Singleton instance of the model
_llm = None

def get_llm():
    """Initialize and return the LLM instance (singleton)."""
    global _llm
    if _llm is None:
        model_path = os.getenv(
            "AI_MODEL_PATH",
            r"C:\BinaryGame\BinaryGameBackEnd\model\gemma-2-2b-it-Q4_K_M.gguf",
        )
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at {model_path}. "
                f"Download it from: https://huggingface.co/bartowski/gemma-2-2b-it-GGUF"
            )
        
        _llm = Llama(
            model_path=model_path,
            n_ctx=2048,  # Context window
            n_threads=4,  # CPU threads
            n_gpu_layers=0,  # Set to 0 for CPU only, increase for GPU
            verbose=False
        )
    return _llm


def generate_hint_text(grid: str, hints: list[dict]) -> str:
    """
    Generate natural language hint using local AI model.
    
    Args:
        grid: JSON string of the current puzzle state
        hints: List of possible moves from get_possible_moves()
    
    Returns:
        Natural language hint text
    """
    
    # Format hints for the prompt
    hints_text = "\n".join([
        f"- Row {h['row']+1}, Column {h['col']}: Put {h['value']} ({h['reason']})"
        for h in hints  # Use top 3 hints
    ])

    print("Formatted hints for prompt:")
    print(hints_text)
    
    prompt = f"""You are a helpful assistant for a binary puzzle game. You are a raccoon named Bystrzacha Brightpaw, but your reply must be plain text only (no markdown, no asterisks, no quotes, no bullets).
    

Rules of the game:

1. Each cell must contain 0 or 1
2. No more than two consecutive 0s or 1s in any row or column
3. Each row and column must have equal numbers of 0s and 1s
4. All rows and all columns must be unique

The rows are labeled 1 2 3...
The columns are labeled A B C...

Current puzzle state (JSON):
{grid}

Possible next moves:
{hints_text}

Be warm and a little playful, but still simple and clear. No emojis, no extra styling.

Always tell the user exactly one move and why it is valid. Include a short cute phrase in every hint, like:
- "my tail tells me"
- "I feel it in my whiskers"
- "my paws are sure"
Keep the cute phrase short (3-6 words) and include it once.
If possible next moves is empty, still provide one concrete suggestion based on the rules (pick a random empty cell and propose a value).

Give ONE short hint (1-2 sentences). Focus on ONLY ONE move."""

    llm = get_llm()
    response = llm.create_chat_completion(
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=100,
        stop=["\n\n"]  # Stop at double newline
    )
    
    hint = response["choices"][0]["message"]["content"].strip()
    # Enforce plain text output: strip common markdown noise
    hint = hint.replace("*", "").replace("`", "").replace("_", "").replace("#", "").strip()
    return hint


def generate_error_feedback(grid: str, errors: list) -> str:
    """
    Generate friendly error feedback using local AI model.
    
    Args:
        grid: JSON string of the current puzzle state
        errors: List of error objects (flexible format)
    
    Returns:
        Natural language feedback about the errors
    """
    if not errors:
        return "Great! No errors detected in this move."
    
    # Format errors for the prompt - handle flexible error format
    errors_text_list = []
    for error in errors:
        if isinstance(error, dict):
            # Try to build readable error description from whatever fields exist
            if 'row' in error and 'col' in error:
                error_desc = f"Row {error.get('row', '?')}, Column {error.get('col', '?')}"
                if 'error_type' in error:
                    error_desc += f": {error['error_type']}"
            else:
                # Fallback: just stringify the error
                error_desc = str(error)
            errors_text_list.append(f"- {error_desc}")
        else:
            errors_text_list.append(f"- {str(error)}")
    
    random.shuffle(errors_text_list)

    errors_text = "\n".join(errors_text_list)  # Limit to 5 errors

    print("Formatted errors for prompt:")
    print(errors_text)
    
    prompt = f"""You are a friendly assistant for a binary puzzle game. You are a raccoon named Bystrzacha Brightpaw, but your reply must be plain text only (no markdown, no asterisks, no quotes, no bullets).

Rules of the game:

1. Each cell must contain 0 or 1
2. No more than two consecutive 0s or 1s in any row or column
3. Each row and column must have equal numbers of 0s and 1s
4. All rows and all columns must be unique

The rows are labeled 1 2 3...
The columns are labeled A B C...

Current puzzle state (JSON):
{grid}

Errors found in user's move:
{errors_text}

Keep it simple and calm. No jokes, no emojis, no extra styling.

Always state at least one concrete mistake and which rule it breaks. Do not leave the answer blank.
Give a SHORT explanation (1-2 sentences max). Don't give solutions, just explain the problem."""

    llm = get_llm()
    response = llm.create_chat_completion(
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=500,
        stop=["\n\n"]
    )
    
    feedback = response["choices"][0]["message"]["content"].strip()

    # Enforce plain text output: strip common markdown noise
    feedback = feedback.replace("*", "").replace("`", "").replace("_", "").replace("#", "").strip()
    return feedback
