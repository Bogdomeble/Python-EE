import schemdraw
import schemdraw.elements as elm

with schemdraw.Drawing() as d:
    # 1. Źródło napięcia V1 (w górę)
    V1 = d.add(elm.SourceSin().up().label('V1\n1V AC'))
    
    # 2. Rezystor R1 połączony szeregowo od źródła w prawo
    R1 = d.add(elm.Resistor().right().at(V1.end).label('R1\n10Ω'))
    
    # Zapamiętujemy punkt 'node1' - to tutaj obwód się rozdziela
    node1 = R1.end
    
    # 3. Pierwsza gałąź równoległa: Cewka L1 (w dół do poziomu masy)
    L1 = d.add(elm.Inductor().down().at(node1).label('L1\n1mH'))
    
    # 4. Druga gałąź równoległa: Przesuwamy się w prawo i dodajemy Kondensator C1
    d.add(elm.Line().right().at(node1).length(1.5))
    C1 = d.add(elm.Capacitor().down().label('C1\n1μF'))
    
    # 5. Zamknięcie obwodu (powrót do masy)
    # Łączymy dół kondensatora z dołem cewki i dalej do źródła
    d.add(elm.Line().left().at(C1.end).tox(L1.end))
    d.add(elm.Line().left().tox(V1.start))
    
    # Dodajemy kropkę w miejscu rozgałęzienia (opcjonalnie, dla estetyki)
    d.add(elm.Dot().at(node1))
    
    # Dodajemy symbol masy
    d.add(elm.Ground().at(V1.start))