import re

with open("recovered_paper.tex", "r") as f:
    text = f.read()

# Try to find the exact file content if it has markers
if "[FILE_CONTENT_START]" in text and "[FILE_CONTENT_END]" in text:
    content = text.split("[FILE_CONTENT_START]")[1].split("[FILE_CONTENT_END]")[0]
    # Remove leading newline if present
    if content.startswith("\n"):
        content = content[1:]
    with open("recovered_paper.tex", "w") as out:
        out.write(content)
    print("Cleaned using markers!")
else:
    print("Markers not found, maybe it's already clean or in a different format.")
    print("First 200 chars:")
    print(text[:200])

