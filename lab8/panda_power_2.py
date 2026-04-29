import pandapower as pp
import pandas as pd
import numpy as np
import copy

# -------------------------------
# Create the power system model
# -------------------------------

net = pp.create_empty_network()
v_nom = 110.0  # kV
print(f"Nominal voltage of the system: {v_nom:.3f} kV\n")

# Buses (indices: 0..4)
b1 = pp.create_bus(net, vn_kv=v_nom, name="Bus 1")   # idx 0
b2 = pp.create_bus(net, vn_kv=v_nom, name="Bus 2")   # idx 1
b3 = pp.create_bus(net, vn_kv=v_nom, name="Bus 3")   # idx 2
b4 = pp.create_bus(net, vn_kv=v_nom, name="Bus 4")   # idx 3
b5 = pp.create_bus(net, vn_kv=v_nom, name="Bus 5")   # idx 4

# Slack at Bus 1
pp.create_ext_grid(net, bus=b1, vm_pu=1.06, name="Slack")

# Generator + load at Bus 2 (PV bus)
pp.create_gen(net, bus=b2, p_mw=40, vm_pu=1.01, name="Gen 2")
pp.create_load(net, bus=b2, p_mw=20, q_mvar=10, name="Load 2")

# Loads at other buses
pp.create_load(net, bus=b3, p_mw=45, q_mvar=15, name="Load 3")
pp.create_load(net, bus=b4, p_mw=40, q_mvar=5, name="Load 4")
pp.create_load(net, bus=b5, p_mw=60, q_mvar=10, name="Load 5")

# Lines: (from, to, r_ohm/km, x_ohm/km, length_km, max_i_ka)
line_data = [
    (b1, b2, 0.02, 0.06, 50, 1.5),
    (b1, b3, 0.08, 0.24, 60, 0.5),
    (b2, b3, 0.06, 0.25, 40, 0.5),
    (b2, b4, 0.06, 0.18, 30, 0.5),
    (b2, b5, 0.04, 0.12, 45, 0.5),
    (b3, b4, 0.01, 0.03, 55, 0.5),
    (b4, b5, 0.08, 0.24, 35, 0.5),
]

for from_b, to_b, r, x, length, i_max in line_data:
    pp.create_line_from_parameters(net, from_bus=from_b, to_bus=to_b, length_km=length,
                                   r_ohm_per_km=r, x_ohm_per_km=x, c_nf_per_km=0,
                                   max_i_ka=i_max)

# Initial power flow (base case)
pp.runpp(net)

print("--- BASE CASE BUS RESULTS ---")
print(net.res_bus[['vm_pu', 'va_degree']])

print("\n--- BASE CASE LINE RESULTS ---")
net.res_line['i_ka'] = (net.res_line.loading_percent / 100) * net.line.max_i_ka
print(net.res_line[['i_ka', 'loading_percent']])

# -------------------------------
# N-1 Contingency Analysis
# -------------------------------

print("\n=== N-1 CONTINGENCY ANALYSIS ===\n")

contingency_results = []   # store results

for idx in net.line.index:
    line_name = f"Line {idx} ({net.line.from_bus.at[idx]}->{net.line.to_bus.at[idx]})"

    # Take line out of service
    net.line.at[idx, 'in_service'] = False

    converged = True
    try:
        pp.runpp(net)
    except pp.LoadflowNotConverged:
        converged = False

    if converged:
        v_min = net.res_bus.vm_pu.min()
        load_max = net.res_line.loading_percent.max()
    else:
        v_min = None
        load_max = None

    contingency_results.append({
        'line': idx,
        'name': line_name,
        'converged': converged,
        'v_min': v_min,
        'load_max': load_max
    })

    # Restore the line before next iteration
    net.line.at[idx, 'in_service'] = True

# Print summary of all contingencies
for res in contingency_results:
    if res['converged']:
        print(f"Outage of {res['name']:30s} => Vmin = {res['v_min']:.4f} pu, "
              f"Max loading = {res['load_max']:.1f}%")
    else:
        print(f"Outage of {res['name']:30s} => DID NOT CONVERGE")

# Identify most critical contingency for thermal overload and for voltage violation
critical_thermal = None
critical_voltage = None
max_load = 0
min_voltage = 1.0

for res in contingency_results:
    if res['converged']:
        if res['load_max'] is not None and res['load_max'] > max_load:
            max_load = res['load_max']
            critical_thermal = res
        if res['v_min'] is not None and res['v_min'] < min_voltage:
            min_voltage = res['v_min']
            critical_voltage = res

if critical_thermal:
    print(f"\nMost critical for THERMAL OVERLOAD: {critical_thermal['name']}  "
          f"-> Max loading = {critical_thermal['load_max']:.1f}%")
else:
    print("\nNo thermal critical contingency found (all converged with loading <= 100%).")

if critical_voltage:
    print(f"Most critical for VOLTAGE VIOLATION: {critical_voltage['name']}  "
          f"-> Vmin = {critical_voltage['v_min']:.4f} pu")
else:
    print("No voltage critical contingency found (all converged with Vmin >= 0.95 pu).")

# -------------------------------
# Helper functions for corrective device search
# -------------------------------

def check_violations(network):
    """Return True if no violations (voltage >= 0.90 pu, line loading <= 120 %) and power flow converges."""
    try:
        pp.runpp(network)
    except pp.LoadflowNotConverged:
        return False
    v_ok = (network.res_bus.vm_pu >= 0.90).all()
    load_ok = (network.res_line.loading_percent <= 120.0).all()
    return v_ok and load_ok

def find_minimal_device(net_base, out_line_idx, device_type, candidate_buses,
                        start=0.0, step=0.5, max_size=200):
    """
    For a given contingency (line out_line_idx out of service), find the smallest size of a device
    ('cap' for shunt capacitor [Mvar] or 'gen' for generator [MW]) at each candidate bus
    that removes all violations.
    Returns list of dicts with bus, min_size, device.
    """
    results = []
    for bus in candidate_buses:
        # First test with size=0 (no device) – maybe no violation exists
        net_test = copy.deepcopy(net_base)
        net_test.line.at[out_line_idx, 'in_service'] = False
        if check_violations(net_test):
            results.append({'bus': bus, 'min_size': 0.0, 'device': device_type})
            continue

        # Otherwise increase size until violations disappear or max_size reached
        size = start + step   # start searching from first positive step
        found = False
        while size <= max_size:
            net_test = copy.deepcopy(net_base)
            net_test.line.at[out_line_idx, 'in_service'] = False

            if device_type == 'cap':
                # Shunt capacitor modelled as static generator (p=0, q=size)
                pp.create_sgen(net_test, bus, p_mw=0, q_mvar=size, name=f"Cap_{size}Mvar")
            elif device_type == 'gen':
                # Additional generator with voltage setpoint 1.0 pu
                pp.create_gen(net_test, bus, p_mw=size, vm_pu=1.0, name=f"Gen_{size}MW")
            else:
                raise ValueError("device_type must be 'cap' or 'gen'")

            if check_violations(net_test):
                results.append({'bus': bus, 'min_size': size, 'device': device_type})
                found = True
                break
            size += step

        if not found:
            results.append({'bus': bus, 'min_size': None, 'device': device_type,
                            'comment': f'No solution up to {max_size}'})
    return results

# -------------------------------
# Find minimal corrective device for the most critical contingencies
# -------------------------------

# Use a clean copy of the original network (all lines in service)
net_original = copy.deepcopy(net)

# bus numbers from the assignment: Bus 3 => index 2, Bus 4 => index 3, Bus 5 => index 4
candidate_buses = [2, 3, 4]   # corresponding to Buses 3, 4, 5

# --- Voltage‑critical contingency → shunt capacitor ---
if critical_voltage:
    print("\n=== CORRECTIVE DEVICE FOR VOLTAGE CRITICAL CONTINGENCY ===")
    print(f"Outage: {critical_voltage['name']}, Vmin = {critical_voltage['v_min']:.4f} pu")
    out_idx_v = critical_voltage['line']

    cap_results = find_minimal_device(net_original, out_idx_v, device_type='cap',
                                      candidate_buses=candidate_buses)
    for r in cap_results:
        if r['min_size'] is not None:
            print(f"Bus {r['bus']} (name Bus {r['bus']+1}): minimal shunt capacitor = {r['min_size']:.4f} Mvar")
        else:
            print(f"Bus {r['bus']}: no solution found within tested range.")
else:
    print("\nNo voltage critical contingency to correct.")

# --- Thermal‑critical contingency → generator ---
if critical_thermal:
    print("\n=== CORRECTIVE DEVICE FOR THERMAL CRITICAL CONTINGENCY ===")
    print(f"Outage: {critical_thermal['name']}, Max load = {critical_thermal['load_max']:.1f}%")
    out_idx_t = critical_thermal['line']

    gen_results = find_minimal_device(net_original, out_idx_t, device_type='gen',
                                      candidate_buses=candidate_buses)
    for r in gen_results:
        if r['min_size'] is not None:
            print(f"Bus {r['bus']} (name Bus {r['bus']+1}): minimal additional generator = {r['min_size']:.1f} MW")
        else:
            print(f"Bus {r['bus']}: no solution found within tested range.")
else:
    print("\nNo thermal critical contingency to correct.")