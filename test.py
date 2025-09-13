import ollama

messages = [
    {"role": "system", "content": "You are CodeLlama, a helpful coding assistant."},
    {"role": "user", "content": "Write a Python function to add two numbers."}
]

# Non-streaming (simple check first)
try:
    response = ollama.chat(model="deepseek-coder:6.7b", messages=messages)
    print("Response:", response["message"]["content"])  # <-- dictionary access
except Exception as e:
    print("Error:", e)