import schemdraw
import schemdraw.elements as elm

# Tworzymy obiekt rysunku
with schemdraw.Drawing() as d:
    # Dodajemy źródło napięcia sinusoidalnego (V1)
    # Kierunek 'up' (w górę) od punktu (0,0)
    V1 = d.add(elm.SourceSin().label('V1\n1V AC'))
    
    # Rysujemy linię (kabel) do wejścia rezystora
    d.add(elm.Line().right().at(V1.end))
    
    # Dodajemy Rezystor (R1)
    R1 = d.add(elm.Resistor().right().label('R1\n100Ω'))
    
    # Dodajemy Cewkę (L1)
    L1 = d.add(elm.Inductor().right().label('L1\n1mH'))
    
    # Dodajemy Kondensator (C1) - skierowany w dół do masy
    C1 = d.add(elm.Capacitor().down().label('C1\n1μF'))
    
    # Zamykamy obwód do masy
    d.add(elm.Line().left().at(C1.end).tox(V1.start))
    d.add(elm.Ground().at(V1.start))

    # Opcjonalnie: zapis do pliku
    # d.save('schemat_rlc.png')