import schemdraw
import schemdraw.elements as elm

def draw_rc_circuit():
    """Circuit for task 2: RC Step Response"""
    print("Generating schematic: RC Step Response...")
    with schemdraw.Drawing(show=True) as d:
        d.config(fontsize=12)
        
        # Pulse source
        d += (V1 := elm.SourcePulse().up().label('V_input\n0→5V'))
        
        # Series resistor
        d += (R1 := elm.Resistor().right().label('R1\n1kΩ'))
        
        # Capacitor to ground
        d += (C1 := elm.Capacitor().down().label('C1\n1μF'))
        
        # Return to source and ground
        d += elm.Line().left().tox(V1.start)
        d += elm.Ground()

def draw_rl_circuit():
    """Circuit for task 2: RL Step Response"""
    print("Generating schematic: RL Step Response...")
    with schemdraw.Drawing(show=True) as d:
        d.config(fontsize=12)
        
        # Pulse source
        d += (V1 := elm.SourcePulse().up().label('V_input\n0→10V'))
        
        # Series resistor
        d += (R1 := elm.Resistor().right().label('R1\n10Ω'))
        
        # Inductor to ground
        d += (L1 := elm.Inductor().down().label('L1\n10mH'))
        
        # Return to source and ground
        d += elm.Line().left().tox(V1.start)
        d += elm.Ground()

def draw_rlc_series():
    """Circuit for task 3: Series RLC"""
    print("Generating schematic: Series RLC (Before compensation)...")
    with schemdraw.Drawing(show=True) as d:
        d.config(fontsize=12)
        
        # Sinusoidal source
        d += (V1 := elm.SourceSin().up().label('Source\n10V, 50Hz'))
        
        # Series R, L, C
        d += (R1 := elm.Resistor().right().label('R1\n50Ω'))
        d += (L1 := elm.Inductor().right().label('L1\n100mH'))
        d += (C1 := elm.Capacitor().down().label('C1\n10μF'))
        
        # Return to source and ground
        d += elm.Line().left().tox(V1.start)
        d += elm.Ground()

def draw_rlc_pfc():
    """Circuit for task 4: Series RLC with PFC (Parallel Compensation)"""
    print("Generating schematic: Series RLC with compensation (PFC)...")
    with schemdraw.Drawing(show=True) as d:
        d.config(fontsize=12)
        
        # Sinusoidal source
        d += (V1 := elm.SourceSin().up().label('Source\n10V, 50Hz'))
        
        # Top wire to the PFC branch
        d += elm.Line().right().length(2)
        d += elm.Dot() # Kropka węzła górnego
        d.push() 
        
        # --- COMPENSATION BRANCH (PFC) ---
        # Używamy .length(1.5), aby zmieścić dwa elementy w jednym pionie
        d += elm.Inductor().down().length(1.5).label('L_comp\n0.96H', loc='bottom')
        d += elm.Resistor().down().length(1.5).label('R_comp\n1mΩ', loc='bottom')
        d += elm.Dot() # Kropka węzła dolnego
        
        d.pop() 
        
        # --- ORIGINAL RLC BRANCH ---
        d += elm.Line().right().length(2)
        d += elm.Resistor().right().label('R1\n50Ω')
        d += elm.Inductor().right().label('L1\n100mH')
        # Kondensator zrównuje się z dołem źródła
        d += elm.Capacitor().down().toy(V1.start).label('C1\n10μF')
        
        # --- RETURN WIRE AND GROUND ---
        # Zamykamy obwód jednym dolnym przewodem i uziemiamy całość
        d += elm.Line().left().tox(V1.start)
        d += elm.Ground()
        
# Start drawing
if __name__ == "__main__":
    draw_rc_circuit()
    draw_rl_circuit()
    draw_rlc_series()
    draw_rlc_pfc()