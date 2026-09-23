with open("paper2_heat_irregular_domain/estilo.sty") as f:
    text = f.read()

# Let's check how biblatex handles doi
print("Has hyperref:", "hyperref" in text)
