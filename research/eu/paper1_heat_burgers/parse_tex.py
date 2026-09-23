import re

with open("recovered_paper.tex", "r") as f:
    lines = f.readlines()

output_lines = []
start_parsing = False
for line in lines:
    if line.startswith("1: "):
        start_parsing = True
    if start_parsing:
        # Match 'number: ' prefix
        match = re.match(r'^\d+:\s(.*)', line)
        if match:
            output_lines.append(match.group(1) + "\n")
        elif re.match(r'^\d+:$', line.strip()):
            output_lines.append("\n")

with open("paper_pinns_heat_burgers.tex", "w") as out:
    out.writelines(output_lines)

print("Recovered tex written to paper_pinns_heat_burgers.tex!")
