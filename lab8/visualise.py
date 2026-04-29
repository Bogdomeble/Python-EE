
import pandapower as pp
import pandapower.plotting.plotly as plotly
import pandapower.plotting as plot
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import copy

# ============================================================
# CREATE NETWORK
# ============================================================

net = pp.create_empty_network()

v_nom = 110.0  # kV

# Buses
b1 = pp.create_bus(net, vn_kv=v_nom, name="Bus 1")
b2 = pp.create_bus(net, vn_kv=v_nom, name="Bus 2")
b3 = pp.create_bus(net, vn_kv=v_nom, name="Bus 3")
b4 = pp.create_bus(net, vn_kv=v_nom, name="Bus 4")
b5 = pp.create_bus(net, vn_kv=v_nom, name="Bus 5")

# Slack
pp.create_ext_grid(net, bus=b1, vm_pu=1.06, name="Slack")

# Generator + loads
pp.create_gen(net, bus=b2, p_mw=40, vm_pu=1.01, name="Gen 2")

pp.create_load(net, bus=b2, p_mw=20, q_mvar=10, name="Load 2")
pp.create_load(net, bus=b3, p_mw=45, q_mvar=15, name="Load 3")
pp.create_load(net, bus=b4, p_mw=40, q_mvar=5, name="Load 4")
pp.create_load(net, bus=b5, p_mw=60, q_mvar=10, name="Load 5")

# Lines
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
    pp.create_line_from_parameters(
        net,
        from_bus=from_b,
        to_bus=to_b,
        length_km=length,
        r_ohm_per_km=r,
        x_ohm_per_km=x,
        c_nf_per_km=0,
        max_i_ka=i_max
    )

# ============================================================
# RUN BASE CASE POWER FLOW
# ============================================================

pp.runpp(net)

print("\n=== BASE CASE BUS RESULTS ===")
print(net.res_bus[['vm_pu', 'va_degree']])

print("\n=== BASE CASE LINE RESULTS ===")
print(net.res_line[['loading_percent']])

# ============================================================
# CREATE BUS COORDINATES
# ============================================================

pp.plotting.create_generic_coordinates(net)

# ============================================================
# 1. INTERACTIVE NETWORK VISUALIZATION (PLOTLY)
# ============================================================

fig = plotly.pf_res_plotly(
    net,
    line_width=3,
    bus_size=14
)

fig.update_layout(
    title="Base Case Power Flow Results",
    title_x=0.5
)

fig.show()

# ============================================================
# 2. VOLTAGE PROFILE PLOT
# ============================================================

plt.figure(figsize=(8, 5))

plt.plot(
    net.bus.name.values,
    net.res_bus.vm_pu.values,
    marker='o',
    linewidth=2
)

plt.axhline(1.0, linestyle='--', label='Nominal Voltage')
plt.axhline(0.95, color='red', linestyle='--', label='Voltage Limit')

plt.ylabel("Voltage (p.u.)")
plt.xlabel("Bus")
plt.title("Bus Voltage Profile")

plt.grid(True)
plt.legend()

plt.show()

# ============================================================
# 3. LINE LOADING PLOT
# ============================================================

plt.figure(figsize=(10, 5))

plt.bar(
    net.line.index.astype(str),
    net.res_line.loading_percent.values
)

plt.axhline(
    100,
    color='red',
    linestyle='--',
    label='Thermal Limit'
)

plt.xlabel("Line")
plt.ylabel("Loading (%)")
plt.title("Line Loading")

plt.grid(True)
plt.legend()

plt.show()

# ============================================================
# 4. NETWORK TOPOLOGY COLORED BY RESULTS
# ============================================================

line_collection = plot.create_line_collection(
    net,
    lines=net.line.index,
    z=net.res_line.loading_percent.values,
    cmap="jet",
    linewidths=4
)

bus_collection = plot.create_bus_collection(
    net,
    buses=net.bus.index,
    z=net.res_bus.vm_pu.values,
    cmap="coolwarm",
    size=120
)

plt.figure(figsize=(8, 6))

plot.draw_collections(
    [line_collection, bus_collection]
)

plt.title("Network Topology with Power Flow Results")

plt.show()

# ============================================================
# 5. N-1 CONTINGENCY ANALYSIS + VISUALIZATION
# ============================================================

contingency_results = []

for idx in net.line.index:

    print(f"\nRunning contingency: remove line {idx}")

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

        contingency_results.append({
            'line': idx,
            'v_min': v_min,
            'load_max': load_max
        })

        # ----------------------------------------------------
        # INTERACTIVE CONTINGENCY VISUALIZATION
        # ----------------------------------------------------

        fig = plotly.pf_res_plotly(
            net,
            line_width=3,
            bus_size=14
        )

        fig.update_layout(
            title=f"N-1 Contingency: Line {idx} Out",
            title_x=0.5
        )

        fig.show()

    else:

        contingency_results.append({
            'line': idx,
            'v_min': np.nan,
            'load_max': np.nan
        })

        print(f"Contingency {idx} did NOT converge")

    # Restore line
    net.line.at[idx, 'in_service'] = True

# ============================================================
# 6. CONTINGENCY SUMMARY PLOTS
# ============================================================

df_cont = pd.DataFrame(contingency_results)

# ------------------------------------------------------------
# MAX LOADING UNDER CONTINGENCIES
# ------------------------------------------------------------

plt.figure(figsize=(10, 5))

plt.bar(
    df_cont['line'].astype(str),
    df_cont['load_max']
)

plt.axhline(
    100,
    color='red',
    linestyle='--',
    label='Thermal Limit'
)

plt.xlabel("Outaged Line")
plt.ylabel("Maximum Loading (%)")

plt.title("N-1 Contingency Thermal Analysis")

plt.grid(True)
plt.legend()

plt.show()

# ------------------------------------------------------------
# MINIMUM VOLTAGE UNDER CONTINGENCIES
# ------------------------------------------------------------

plt.figure(figsize=(10, 5))

plt.bar(
    df_cont['line'].astype(str),
    df_cont['v_min']
)

plt.axhline(
    0.95,
    color='red',
    linestyle='--',
    label='Voltage Limit'
)

plt.xlabel("Outaged Line")
plt.ylabel("Minimum Voltage (p.u.)")

plt.title("N-1 Contingency Voltage Analysis")

plt.grid(True)
plt.legend()

plt.show()

# ============================================================
# 7. PRINT SUMMARY TABLE
# ============================================================

print("\n=== CONTINGENCY SUMMARY ===")
print(df_cont)