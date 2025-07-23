from openai import OpenAI

try:
    client = OpenAI()
    print("OpenAI client instantiated successfully:", client)
except Exception as e:
    print("OpenAI client instantiation failed:", e)
