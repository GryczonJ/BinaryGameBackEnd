from llama_cpp import Llama
import json
import os

# Singleton instance of the model
_llm = None


def get_llm():
    """Initialize and return the LLM instance (singleton)."""
    global _llm
    if _llm is None:
        model_path = os.getenv("AI_MODEL_PATH", "./model/gemma-2-2b-it-Q4_K_M.gguf")
        
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
    if not hints:
        return "I don't see any obvious moves right now. Double-check the puzzle rules!"
    
    # Format hints for the prompt
    hints_text = "\n".join([
        f"- Row {h['row']+1}, Column {h['col']}: Put {h['value']} ({h['reason']})"
        for h in hints[:3]  # Use top 3 hints
    ])
    
    prompt = f"""You are a helpful assistant for a binary puzzle game. You are a raccoon named Bystrzacha Brightpaw, user sees a 3d render of you in the app, and your response in chat styled bubbles. 
    

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

You can sometimes throw in a little joke, be silly, friendly, but smart. Dont be cheesy, dont use emojis.

Always tell user where he can put a value, and why.
If the possibele next moves is empty, come up with something yourself, suggest putting random values in random spots just to get puzzle moving.

Give ONE friendly, encouraging hint to the player. Be concise (1-2 sentences). Focus on ONLY ONE move, choose randomly."""

    llm = get_llm()
    response = llm.create_chat_completion(
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=1000,
        stop=["\n\n"]  # Stop at double newline
    )
    
    hint = response["choices"][0]["message"]["content"].strip()
    return hint
