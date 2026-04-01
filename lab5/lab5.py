import numpy as np
import matplotlib.pyplot as plt
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
from PySpice.Spice.NgSpice.Shared import NgSpiceShared

# =======================================================
#  NGSPICE 42 PATCH
# =======================================================
original_send_char = NgSpiceShared._send_char

def patched_send_char(self, message, message_id):
    msg_str = message.decode('utf-8', errors='ignore') if isinstance(message, bytes) else str(message)
    
    if "Using SPARSE" in msg_str or "compatibility mode" in msg_str:
        return 0 
        
    return original_send_char(self, message, message_id)

# REPLACE THE STDERR DATA
NgSpiceShared._send_char = patched_send_char
# =======================================================

# --- RC circuit ---
circuit_rc = Circuit('RC Step Response')
circuit_rc.PulseVoltageSource('input', 'vin', circuit_rc.gnd,
                              initial_value=0@u_V, pulsed_value=5@u_V,
                              delay_time=0@u_s, rise_time=1@u_us, fall_time=1@u_us,
                              pulse_width=5@u_ms, period=10@u_ms)
circuit_rc.R(1, 'vin', 'out', 1@u_kOhm)
circuit_rc.C(1, 'out', circuit_rc.gnd, 1@u_uF)

# WRACAMY DO 'ngspice-shared'
simulator_rc = circuit_rc.simulator(simulator='ngspice-shared')
analysis_rc = simulator_rc.transient(step_time=10@u_us, end_time=5@u_ms)

# --- RL circuit ---
circuit_rl = Circuit('RL Step Response')
circuit_rl.PulseVoltageSource('input', 'vin', circuit_rl.gnd,
                              initial_value=0@u_V, pulsed_value=10@u_V,
                              delay_time=0@u_s, rise_time=1@u_us, fall_time=1@u_us,
                              pulse_width=5@u_ms, period=10@u_ms)
circuit_rl.R(1, 'vin', 'out', 10@u_Ohm)
circuit_rl.L(1, 'out', circuit_rl.gnd, 10@u_mH)

# WRACAMY DO 'ngspice-shared'
simulator_rl = circuit_rl.simulator(simulator='ngspice-shared')
analysis_rl = simulator_rl.transient(step_time=10@u_us, end_time=5@u_ms)

# --- plots ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# RC circuit plot
time_rc = np.array(analysis_rc.time) * 1000 # miliseconds
ax1.plot(time_rc, np.array(analysis_rc['vin']), label='V_input (5V)')
ax1.plot(time_rc, np.array(analysis_rc['out']), label='V_C (capacitor voltage)')
ax1.set_title('RC step response')
ax1.set_xlabel('time [ms]')
ax1.set_ylabel('Voltage [V]')
ax1.grid()
ax1.legend()

# RL circuit plot 
time_rl = np.array(analysis_rl.time) * 1000
ax2.plot(time_rl, np.array(analysis_rl['vin']), label='V_input (10V)')
ax2.plot(time_rl, np.array(analysis_rl['vin']) - np.array(analysis_rl['out']), label='V_L (coil voltage)')
ax2.set_title('RL step response')
ax2.set_xlabel('Time [ms]')
ax2.set_ylabel('Voltage [V]')
ax2.grid()
ax2.legend()

plt.tight_layout()
plt.show()