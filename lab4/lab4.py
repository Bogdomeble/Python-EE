import numpy as np

# Bus data
# Voltage [kV], Angle [degrees]

bus_data = {
    1: {'V': 116.6, 'angle': 0.0},
    2: {'V': 114.4, 'angle': -4.98},
    3: {'V': 112.2, 'angle': -12.72},
    4: {'V': 111.1, 'angle': -10.33},
    5: {'V': 113.3, 'angle': -8.78}
}

# Line data
# From, To, R [Ohm], X[Ohm]

line_data =[
    (1, 2, 2.42, 7.26),
    (1, 3, 9.68, 29.04),
    (2, 3, 7.26, 21.78),
    (2, 4, 7.26, 21.78),
    (2, 5, 4.84, 14.52),
    (3, 4, 1.21, 3.63),
    (4, 5, 9.68, 29.04)
]

num_buses = len(bus_data)

# Conversion to complex
# Bus 1 is index 0.

V = np.zeros(num_buses, dtype=complex)
for i in range(1, num_buses + 1):
    V_mag = bus_data[i]['V']
    V_rad = np.radians(bus_data[i]['angle']) # to radians
    V[i-1] = V_mag * np.exp(1j * V_rad) # Exponential form re^(i * theta)

# print(f"\nV-bus: {np.round(V,3)} KV\n")

# Network Modeling (Ybus)

Ybus = np.zeros((num_buses, num_buses), dtype=complex) # nxn square matrix for every node in the system
y_lines = {} # to store the admittance of each line

for f, t, R, X in line_data:
    Z = R + 1j * X       # Line impedance (Z = R + j(Xc-Xl))
    y = 1 / Z            # Line admittance (y = 1/Z)

    # admittance for later calculations (indices from 0)
    y_lines[(f-1, t-1)] = y
    y_lines[(t-1, f-1)] = y

    # Y_ij = -y_ij
    Ybus[f-1, t-1] -= y
    Ybus[t-1, f-1] -= y

    # Diagonal elements Y_ii = sum of admittances connected to the node
    Ybus[f-1, f-1] += y
    Ybus[t-1, t-1] += y

print("--- PART A: Ybus Matrix ---")
print(np.round(Ybus, 3))
print("\n")


# PART B - Current Calculation

# (Bus current injections): I_bus = Ybus * V

I_bus = Ybus @ V

print("--- PART B: nodes (I_bus) [kA] ---")
for i in range(num_buses):
    print(f"Bus {i+1}: {np.round(I_bus[i], 3)} kA")

# I_ij = y_ij * (V_i - V_j)
I_line = {}
print("\n--- PART B: lines (I_ij) [kA] ---")
for (f, t), y in y_lines.items():
    if f < t: # calculate in one direction here
        I_ij = y * (V[f] - V[t])
        I_line[(f, t)] = I_ij
        print(f" Bus {f + 1} -> Bus {t + 1}: {np.round(I_ij, 3)} kA")

# PART C - Power Calculation

# S = V * I* (np.conj(I))
# S is in MW because we have kilovolts times kiloamperes.

print("\n--- PART C:(S_ij) [MVA] ---")
S_line = {}
for (f, t), I in I_line.items():
    S_ij = V[f] * np.conj(I) # conjugate:  S = V * I*
    S_line[(f, t)] = S_ij
    print(f" Bus {f+1} -> Bus {t+1}: P = {S_ij.real:.2f} MW, Q = {S_ij.imag:.2f} Mvar, S = {np.sqrt(S_ij.real ** 2 + S_ij.imag ** 2):.2f} MVA")

# Power injected into each node for Part D
S_bus = V * np.conj(I_bus)

# PART D - Analysis

P_bus = np.real(S_bus) # Active power
Q_bus = np.imag(S_bus) # Reactive power

print(f"\nP_bus: {np.round(P_bus,3)} MW\n")
print(f"\nQ_bus: {np.round(Q_bus,3)} Mvar\n")

# Generators are at Bus 1 and Bus 2.
# "Injected power" - positive power injected into the network.

gen_buses = [0, 1] #  (Bus 1, Bus 2)
max_gen_P = -float('inf')
max_gen_bus = -1

for b in gen_buses:
    if P_bus[b] > max_gen_P:
        max_gen_P = P_bus[b]
        max_gen_bus = b + 1

# Loads are at 3, 4, 5.
# Consumed power is the value with a minus sign relative to injected

load_buses = [2, 3, 4] # (Bus 3, Bus 4, Bus 5)
max_load_Q = -float('inf')
max_load_bus = -1

for b in load_buses:
    consumed_Q = -Q_bus[b] # Reverse the sign - how much the node "consumes"
    if consumed_Q > max_load_Q:
        max_load_Q = consumed_Q
        max_load_bus = b + 1

print("\n--- PART D: Analysis ---")
print(f" Node with max active power (Generator): Bus {max_gen_bus} ({max_gen_P:.2f} MW)")
print(f" Node with maximum consumed reactive power (Load): Bus {max_load_bus} ({max_load_Q:.2f} Mvar)")
