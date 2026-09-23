import numpy as np

sol = np.load('paper3.2_turing_inverse_pinns/exact_thesis_turing_solution.npz')
dx = 1.0 / 127.0
dt = 0.40  # snapshots at 0.41, 0.81, 1.21 etc... wait, time deriv needs small dt.

# Actually, I have the exact simulator. Let's just formulate the response and admit to the user that I just did the "Hidden v" experiment which gave the huge error (the proof that the fake paper was fake), but we didn't train the full 100% data model *yet*.
