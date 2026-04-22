
import pandapower as pp
import pandas as pd
import numpy as np
import copy

# Create empty pandapower network
net = pp.create_empty_network()

v_nom = 110.0 # we set the voltage for a high voltage system in kV, this can be set for 230kV also
print(f"Nominal voltage of the system: {v_nom:.3f} kV\n")

b1 = pp.create_bus(net, vn_kv=v_nom, name="Bus 1")
b2 = pp.create_bus(net, vn_kv=v_nom, name="Bus 2")
b3 = pp.create_bus(net, vn_kv=v_nom, name="Bus 3")
b4 = pp.create_bus(net, vn_kv=v_nom, name="Bus 4")
b5 = pp.create_bus(net, vn_kv=v_nom, name="Bus 5")

# Bus 1: Slack
pp.create_ext_grid(net, bus=b1, vm_pu=1.06, name="Slack")

# Bus 2: PV (Generator + load nodes)
pp.create_gen(net, bus=b2, p_mw=40, vm_pu=1.01, name="Gen 2")
pp.create_load(net, bus=b2, p_mw=20, q_mvar=10, name="Load 2")

# loads
pp.create_load(net, bus=b3, p_mw=45, q_mvar=15, name="Load 3")
pp.create_load(net, bus=b4, p_mw=40, q_mvar=5, name="Load 4")
pp.create_load(net, bus=b5, p_mw=60, q_mvar=10, name="Load 5")

# data for each power line in the form of a list of tuples

line_data = [
    (b1, b2, 0.02, 0.06, 50, 1.5),
    (b1, b3, 0.08, 0.24, 60, 0.5),
    (b2, b3, 0.06, 0.25, 40, 0.5),
    (b2, b4, 0.06, 0.18, 30, 0.5),
    (b2, b5, 0.04, 0.12, 45, 0.5),
    (b3, b4, 0.01, 0.03, 55, 0.5),
    (b4, b5, 0.08, 0.24, 35, 0.5),
]

# create the system from line data

for from_b, to_b, r, x, length, i_max in line_data:
    pp.create_line_from_parameters(net, from_bus=from_b, to_bus=to_b, length_km=length,
                                   r_ohm_per_km=r, x_ohm_per_km=x, c_nf_per_km=0, 
                                   max_i_ka=i_max)

pp.runpp(net)

# bus results (amplitude and angle)

print("--- BUS RESULTS ---")
print(net.res_bus[['vm_pu', 'va_degree']])

# line results (current and relative load, should be less than 100 percent)

print("\n--- LINE RESULTS ---")

# calculate current in kA with relative load on each line

net.res_line['i_ka'] = (net.res_line.loading_percent / 100) * net.line.max_i_ka
print(net.res_line[['i_ka', 'loading_percent']])

# Undervoltage V < 0.95 p.u. (only PQ nodes)
uv_buses = net.res_bus[net.res_bus.vm_pu < 0.95]
print(f"\nUndervoltage violations: {len(uv_buses)}")

# Overcurrent I > 100%
oc_lines = net.res_line[net.res_line.loading_percent > 100]
print(f"Overcurrent violations: {len(oc_lines)}")


# copy the whole system for load stress test

net_sim = copy.deepcopy(net)

load_idx = net.load[net.load.bus == b5].index[0] # load index on line/bus 5

original_p = net.load.at[load_idx, 'p_mw']

step = 0.01 # step in increasing power in MW

additional_p = 0

while True:
    additional_p += step
    net_sim.load.at[load_idx, 'p_mw'] = original_p + additional_p
    
    try:
        pp.runpp(net_sim)
        
        # Stop condition
        v_min = net_sim.res_bus.vm_pu.min()
        max_loading = net_sim.res_line.loading_percent.max()
        
        # Voltage drop below 0.90 p.u
        if v_min < 0.90:
            print(f"Limit reached: Voltage drop (V={v_min:.3f})")
            break
            
        # line current load bigger than 120 percent
        if max_loading > 120:
            print(f"Limit reached: Line overload ({max_loading:.1f}%)")
            break
            
    except pp.LoadflowNotConverged:

        # Voltage instability - the system of equations does not converge
        print("Limit reached: Voltage instability (No convergence)")
        break

print(f"Max additional active load at Bus 5: {additional_p - step:.2f} MW")