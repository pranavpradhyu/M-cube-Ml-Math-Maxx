"""Question generator for the timed Number Game (mental arithmetic)."""
import random


def number_game_question(level="easy"):
    level = (level or "easy").lower()
    if level == "easy":
        a, b = random.randint(1, 20), random.randint(1, 20)
        op = random.choice(["+", "-"])
    elif level == "medium":
        a, b = random.randint(10, 50), random.randint(2, 12)
        op = random.choice(["+", "-", "×"])
    else:  # hard
        a, b = random.randint(12, 99), random.randint(3, 20)
        op = random.choice(["+", "-", "×"])
    if op == "-" and b > a:
        a, b = b, a
    if op == "+":
        ans = a + b
    elif op == "-":
        ans = a - b
    else:
        ans = a * b
    return {"text": f"{a} {op} {b}", "answer": ans}
