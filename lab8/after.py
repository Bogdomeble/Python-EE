import pandapower as pp
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# ==============================================================================
# 1. NETWORK CREATION AND PARAMETERS
# ==============================================================================
net = pp.create_empty_network()
v_nom = 110.0

b1 = pp.create_bus(net, vn_kv=v_nom, name="Bus 1")
b2 = pp.create_bus(net, vn_kv=v_nom, name="Bus 2")
b3 = pp.create_bus(net, vn_kv=v_nom, name="Bus 3")
b4 = pp.create_bus(net, vn_kv=v_nom, name="Bus 4")
b5 = pp.create_bus(net, vn_kv=v_nom, name="Bus 5")

pos_dict = {
    b1: (0, 5),   b2: (5, 10),
    b3: (5, 0),   b4: (10, 5),
    b5: (15, 10)
}

# --- NETWORK ELEMENTS ---
pp.create_ext_grid(net, bus=b1, vm_pu=1.06, name="Slack")
pp.create_gen(net, bus=b2, p_mw=40, vm_pu=1.01, name="Gen 2")

# CORRECTIVE ACTION: Generator added based on N-1 analysis
pp.create_sgen(net, bus=b5, p_mw=10.474, name="Gen 5")

# --- LOADS ---
pp.create_load(net, bus=b2, p_mw=20, q_mvar=10, name="Load 2")
pp.create_load(net, bus=b3, p_mw=45, q_mvar=15, name="Load 3")
pp.create_load(net, bus=b4, p_mw=40, q_mvar=5, name="Load 4")
pp.create_load(net, bus=b5, p_mw=60, q_mvar=10, name="Load 5")

# --- TRANSMISSION LINES ---
line_data = [
    (b1, b2, 0.02, 0.06, 50, 1.5), # Index 0 (Critical Line)
    (b1, b3, 0.08, 0.24, 60, 0.5), # Index 1
    (b2, b3, 0.06, 0.25, 40, 0.5), # Index 2
    (b2, b4, 0.06, 0.18, 30, 0.5), # Index 3
    (b2, b5, 0.04, 0.12, 45, 0.5), # Index 4
    (b3, b4, 0.01, 0.03, 55, 0.5), # Index 5
    (b4, b5, 0.08, 0.24, 35, 0.5), # Index 6
]

for from_b, to_b, r, x, length, i_max in line_data:
    pp.create_line_from_parameters(
        net, from_bus=from_b, to_bus=to_b, length_km=length,
        r_ohm_per_km=r, x_ohm_per_km=x, c_nf_per_km=0, max_i_ka=i_max
    )

# ==============================================================================
# 2. CONTINGENCY SIMULATION (N-1)
# ==============================================================================
# Disconnecting the critical line
LINE_OUTAGE = 0 

if LINE_OUTAGE is not None:
    net.line.at[LINE_OUTAGE, 'in_service'] = False
    print(f"Warning: Line {LINE_OUTAGE} has been DISCONNECTED for the N-1 contingency test.")

pp.runpp(net)

# ==============================================================================
# 3. VISUALIZATION
# ==============================================================================
fig = go.Figure()

# Max value set to 130 to comfortably fit the 120% loading on the color scale
cmap_lines = plt.colormaps.get_cmap('turbo')
norm_lines = mcolors.Normalize(vmin=0, vmax=140)

# A. DRAWING LINES
for idx in net.line.index:
    b_from = net.line.at[idx, 'from_bus']
    b_to = net.line.at[idx, 'to_bus']
    x0, y0 = pos_dict[b_from]
    x1, y1 = pos_dict[b_to]
    
    if net.line.at[idx, 'in_service']:
        load = net.res_line.at[idx, 'loading_percent']
        color_hex = mcolors.to_hex(cmap_lines(norm_lines(load)))
        
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1], mode='lines',
            line=dict(width=5, color=color_hex), showlegend=False,
            hoverinfo='text', text=f"Line {idx} ({b_from}-{b_to})<br>Loading: {load:.1f}%"
        ))
        
        fig.add_annotation(
            x=(x0 + x1)/2, y=(y0 + y1)/2, text=f"<b>{load:.1f}%</b>",
            showarrow=False, font=dict(color="black", size=11),
            bgcolor="rgba(255, 255, 255, 0.9)", bordercolor=color_hex, borderwidth=2
        )
    else:
        # Disconnected contingency line
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1], mode='lines',
            line=dict(width=4, color='grey', dash='dash'), showlegend=False,
            hoverinfo='text', text=f"Line {idx} ({b_from}-{b_to})<br><b>OUT OF SERVICE</b>"
        ))
        
        fig.add_annotation(
            x=(x0 + x1)/2, y=(y0 + y1)/2, text="<b>X</b>",
            showarrow=False, font=dict(color="red", size=16),
            bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="red", borderwidth=2
        )

# B. DRAWING BUSES
bus_x = [pos_dict[b][0] for b in net.bus.index]
bus_y = [pos_dict[b][1] for b in net.bus.index]
bus_v = net.res_bus['vm_pu'].tolist()
bus_names = net.bus['name'].tolist()

label_text_buses = [f"<b>{name}</b><br>{v:.3f} pu" for name, v in zip(bus_names, bus_v)]

fig.add_trace(go.Scatter(
    x=bus_x, y=bus_y, mode='markers+text',
    marker=dict(
        size=24, color=bus_v, colorscale='RdBu', cmin=0.85, cmax=1.05,
        colorbar=dict(title="Bus Voltage [p.u.]", x=1.02, thickness=20),
        line=dict(width=2, color='Black')
    ),
    text=label_text_buses, textposition="top center",
    textfont=dict(size=14, color='black'), hoverinfo='none', showlegend=False
))

# C. ANNOTATIONS
fig.add_annotation(
    x=pos_dict[b5][0] + 1.2, y=pos_dict[b5][1] + 0.3,
    text="⚡ <b>Gen: 10.5 MW</b>", showarrow=True, arrowhead=2,
    ax=40, ay=-30, font=dict(color="#2ca02c", size=13)
)

# D. SECOND LEGEND (Line loading)
fig.add_trace(go.Scatter(
    x=[None], y=[None], mode='markers',
    marker=dict(
        size=0, color=[0, 130], colorscale='turbo', cmin=0, cmax=130,
        colorbar=dict(title="Line Loading [%]", x=1.18, thickness=20)
    ), showlegend=False
))

# E. FIGURE LAYOUT
fig.update_layout(
    title=dict(
        text=f"<b>Power Flow Analysis - After adding generator (Disconnected line number {LINE_OUTAGE})</b>",
        font=dict(size=24)
    ),
    width=1500, height=850, plot_bgcolor='white', paper_bgcolor='white',
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    margin=dict(l=40, r=150, t=90, b=40)
)

fig.show()