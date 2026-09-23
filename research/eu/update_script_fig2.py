with open("paper2_heat_irregular_domain/src/generate_all_figures_compact.py") as f:
    text = f.read()

# Replace \textbf in annotation with clean bold text or mathtext \mathbf
old_str = r"""ax1.annotate(r'\textbf{Rigidez Numérica}' + '\n' + r'($\sim 26\mathrm{k}$ épocas)', 
             xy=(26000, 2.2e-3), xytext=(28000, 6e-2),
             arrowprops=dict(arrowstyle="->", color="crimson", lw=1.0),
             fontsize=6.8, color='darkred',
             bbox=dict(boxstyle="round,pad=0.25", fc="#fff5f5", ec="crimson", lw=0.6))"""

new_str = r"""ax1.annotate('Rigidez Numérica\n' + r'($\sim 26\mathrm{k}$ épocas)', 
             xy=(26000, 2.2e-3), xytext=(27500, 5e-2),
             arrowprops=dict(arrowstyle="->", color="crimson", lw=1.0),
             fontsize=7.0, fontweight='bold', color='darkred',
             bbox=dict(boxstyle="round,pad=0.3", fc="#fff5f5", ec="crimson", lw=0.7))"""

assert old_str in text, "old_str not found"
text = text.replace(old_str, new_str)
with open("paper2_heat_irregular_domain/src/generate_all_figures_compact.py", "w") as f:
    f.write(text)
print("[OK] Replaced annotation successfully")
