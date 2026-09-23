import json

log_file = "/home/warley/.gemini/antigravity-ide/brain/f1f663a6-f5ac-4b70-a841-aec049891964/.system_generated/logs/transcript_full.jsonl"

with open(log_file, "r") as f:
    for line in f:
        data = json.loads(line)
        if data.get("type") == "VIEW_FILE" and "paper_pinns_heat_burgers.tex" in data.get("content", ""):
            print("Found VIEW_FILE with tex content!")
            with open("recovered_paper.tex", "w") as out:
                out.write(data["content"])
            break
        elif data.get("type") == "RUN_COMMAND" and "cat paper_pinns_heat_burgers.tex" in data.get("content", ""):
            print("Found RUN_COMMAND cat with tex content!")
            with open("recovered_paper.tex", "w") as out:
                out.write(data["content"])
            break
