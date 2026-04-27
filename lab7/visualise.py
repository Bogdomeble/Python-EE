import pandapower as pp
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# ==============================================================================
# 1. NETWORK CREATION & PARAMETERS
# ==============================================================================
net = pp.create_empty_network()
v_nom = 110.0

# Create buses
b1 = pp.create_bus(net, vn_kv=v_nom, name="Bus 1")
b2 = pp.create_bus(net, vn_kv=v_nom, name="Bus 2")
b3 = pp.create_bus(net, vn_kv=v_nom, name="Bus 3")
b4 = pp.create_bus(net, vn_kv=v_nom, name="Bus 4")
b5 = pp.create_bus(net, vn_kv=v_nom, name="Bus 5")

# PLANAR LAYOUT: Custom dictionary of coordinates (X, Y) to avoid intersections
pos_dict = {
    b1: (0, 5),   # Left
    b2: (5, 10),  # Top Center
    b3: (5, 0),   # Bottom Center
    b4: (10, 5),  # Middle Right
    b5: (15, 10)  # Top Far Right
}

# Network elements
pp.create_ext_grid(net, bus=b1, vm_pu=1.06, name="Slack")
pp.create_gen(net, bus=b2, p_mw=40, vm_pu=1.01, name="Gen 2")
pp.create_load(net, bus=b2, p_mw=20, q_mvar=10, name="Load 2")
pp.create_load(net, bus=b3, p_mw=45, q_mvar=15, name="Load 3")
pp.create_load(net, bus=b4, p_mw=40, q_mvar=5, name="Load 4")
pp.create_load(net, bus=b5, p_mw=60, q_mvar=10, name="Load 5")

line_data = [
    (b1, b2, 0.02, 0.06, 50, 1.5), (b1, b3, 0.08, 0.24, 60, 0.5),
    (b2, b3, 0.06, 0.25, 40, 0.5), (b2, b4, 0.06, 0.18, 30, 0.5),
    (b2, b5, 0.04, 0.12, 45, 0.5), (b3, b4, 0.01, 0.03, 55, 0.5),
    (b4, b5, 0.08, 0.24, 35, 0.5),
]

for from_b, to_b, r, x, length, i_max in line_data:
    pp.create_line_from_parameters(net, from_bus=from_b, to_bus=to_b, length_km=length,
                                   r_ohm_per_km=r, x_ohm_per_km=x, c_nf_per_km=0, max_i_ka=i_max)

# ==============================================================================
# 2. CALCULATION (POWER FLOW)
# ==============================================================================
pp.runpp(net, numba=False)

# ==============================================================================
# 3. PROFESSIONAL VISUALIZATION (Plotly Graph Objects)
# ==============================================================================
fig = go.Figure()

# Line color generator ('turbo' scale from 0 to 120%)
cmap_lines = plt.colormaps.get_cmap('turbo')
norm_lines = mcolors.Normalize(vmin=0, vmax=120)

# A. DRAWING LINES
for idx in net.line.index:
    b_from = net.line.at[idx, 'from_bus']
    b_to = net.line.at[idx, 'to_bus']
    
    x0, y0 = pos_dict[b_from]
    x1, y1 = pos_dict[b_to]
    
    load = net.res_line.at[idx, 'loading_percent']
    color_hex = mcolors.to_hex(cmap_lines(norm_lines(load)))
    
    # Draw the line
    fig.add_trace(go.Scatter(
        x=[x0, x1], y=[y0, y1], mode='lines',
        line=dict(width=5, color=color_hex),
        hoverinfo='text',
        text=f"Line {b_from}-{b_to}<br>Loading: {load:.1f}%",
        showlegend=False
    ))
    
    # Percentage label in the middle of the line
    fig.add_annotation(
        x=(x0 + x1)/2, y=(y0 + y1)/2,
        text=f"<b>{load:.1f}%</b>",
        showarrow=False, font=dict(color="black", size=11),
        bgcolor="rgba(255, 255, 255, 0.9)", bordercolor=color_hex,
        borderwidth=2, borderpad=3
    )

# B. DRAWING BUSES (NODES)
bus_indices = net.bus.index.tolist()
bus_x = [pos_dict[b][0] for b in bus_indices]
bus_y = [pos_dict[b][1] for b in bus_indices]
bus_v = net.res_bus['vm_pu'].tolist()
bus_names = net.bus['name'].tolist()

# Labels above nodes
label_text_buses = [f"<b>{name}</b><br>{v:.3f} pu" for name, v in zip(bus_names, bus_v)]

fig.add_trace(go.Scatter(
    x=bus_x, y=bus_y, mode='markers+text',
    marker=dict(
        size=24, color=bus_v,
        colorscale='RdBu', cmin=0.90, cmax=1.10,
        colorbar=dict(title="Bus Voltage [p.u.]", x=1.02, thickness=20), # First legend
        line=dict(width=2, color='Black')
    ),
    text=label_text_buses, textposition="top center",
    textfont=dict(size=14, color='black'),
    hoverinfo='none', showlegend=False
))

# C. ADDING HIDDEN TRACE (To force the Line Loading legend to appear)
fig.add_trace(go.Scatter(
    x=[None], y=[None], mode='markers',
    marker=dict(
        size=0, color=[0, 120], colorscale='turbo', cmin=0, cmax=120,
        colorbar=dict(title="Line Loading [%]", x=1.18, thickness=20) # Second legend
    ), showlegend=False
))

# D. WINDOW & LAYOUT SETTINGS
fig.update_layout(
    title=dict(text="<b>Power Flow Analysis - 110kV System Status</b>", font=dict(size=24)),
    width=1500, height=850,
    plot_bgcolor='white', paper_bgcolor='white',
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    margin=dict(l=40, r=150, t=90, b=40)
)

fig.show()