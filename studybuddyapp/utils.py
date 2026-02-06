def generate_hints(content):
    sentences = content.split(".")
    hints = [s.strip()[:50] + "..." for s in sentences if len(s.strip()) > 20]
    return hints[:5]  # max 5 hints


