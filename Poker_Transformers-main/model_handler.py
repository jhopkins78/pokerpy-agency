from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch

# Load model and tokenizer once at module level for efficiency
MODEL_NAME = "SoelMgd/Poker_SmolLM"
TOKENIZER_NAME = "HuggingFaceTB/SmolLM2-135M"

device = 0 if torch.cuda.is_available() else -1

tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
tokenizer.pad_token = tokenizer.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

text_gen = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    return_full_text=False,
    device=device
)

def analyze_hand(hand_text: str, max_new_tokens: int = 32) -> str:
    """
    Analyze a poker hand history and return a natural-language interpretation.

    Args:
        hand_text (str): Raw hand history string.
        max_new_tokens (int): Maximum number of tokens to generate.

    Returns:
        str: Model's natural-language interpretation.
    """
    result = text_gen(hand_text, max_new_tokens=max_new_tokens, do_sample=False)
    return result[0]["generated_text"] if result and "generated_text" in result[0] else ""
