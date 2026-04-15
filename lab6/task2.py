import math
import numpy as np
import matplotlib.pyplot as plt
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

# calculating theoretical values

R_val = 10@u_Ohm    #  10 ohms
L_val = 1@u_mH      # 1 mH
C_val = 1@u_uF      # 1 uF

# f_r = 1 / (2 * pi * sqrt(L * C))
# convert from pyspice units to regular numbers
L_float = 1e-3
C_float = 1e-6

f_res_theoretical = 1 / (2 * math.pi * math.sqrt(L_float * C_float))
print(f"\nTheoretical resonance frequency {f_res_theoretical:.2f} Hz\n")

# new circuit with the same voltage source
circuit = Circuit('Parallel RLC Circuit')
circuit.SinusoidalVoltageSource('V1', 'input', circuit.gnd, amplitude=1@u_V)

# R in series, then we do L anc C in parallel
circuit.R(1, 'input', 'node1', R_val)
circuit.L(1, 'node1', circuit.gnd, L_val)
circuit.C(1, 'node1', circuit.gnd, C_val)

# ac frequency analysis

simulator = circuit.simulator(temperature=25, nominal_temperature=25)

# 100Hz -> 100kHz with 100 points

analysis = simulator.ac(start_frequency=100@u_Hz, stop_frequency=100@u_kHz, number_of_points=1000, variation='dec')

# extract the necessary data

frequencies = analysis.frequency

# the current only goes through the resistor when counting power
# convert complex values to real nums using np.abs()

current_magnitude = np.abs(analysis.vv1)

# look for the resonance frequency

max_current_index = np.argmin(current_magnitude)
f_res_simulated = frequencies[max_current_index]

print(f"\nSimulated resonance frequncy: {float(f_res_simulated):.2f} Hz\n")
print(f"\nRelative error: {np.abs(f_res_simulated - f_res_theoretical) / f_res_theoretical * 100:.2f} %")

# Plots

plt.figure(figsize=(10, 6))
plt.semilogx(frequencies, current_magnitude * 1000) # x in log scale, current in mA.

plt.axvline(x=float(f_res_simulated), color='r', linestyle='--', label=f'Resonance ({float(f_res_simulated):.2f} Hz)')
plt.title('Parallel RLC circuit - frequency response')

plt.xlabel('frequency [Hz]')
plt.ylabel('current [mA]')

plt.grid(True, which="both", ls="-")
plt.legend()
plt.show()