# avl_generator.py
import numpy as np
def create_avl_config_from_bezier(file_name, bezier_wing, surface_name="wing"):
    """
    Cria um arquivo de configuração .avl completo a partir de um objeto BezierAirfoil.
    """
    # Extrair propriedades do objeto bezier_wing
    chords = bezier_wing.properties["chord"]
    span_positions = bezier_wing.properties["span"]
    leading_edge_xyz = bezier_wing.leading_edge
    airfoil_files = bezier_wing.properties["airfoil_files"] # Assumindo que você salvou isso

    # Calcular valores de referência
    half_wing_area = np.trapezoid(chords, span_positions)
    Sref = 2 * half_wing_area
    Bref = 2 * span_positions[-1]
    Cref = (2 / Sref) * np.trapezoid(chords**2, span_positions) # C M A
    
    with open(file_name, 'w') as f:
        # --- Cabeçalho do Arquivo ---
        f.write(f'{surface_name} from Bezier\n') # Título do caso [cite: 45]
        f.write('#Mach\n')
        f.write('0.0\n') # Mach [cite: 47]
        f.write('#iYsym  iZsym  Zsym\n')
        f.write('1  0  0.0\n') # Simetria no plano Y=0 [cite: 48]
        f.write('#Sref   Cref   Bref\n')
        f.write(f'{Sref:.4f}  {Cref:.4f}  {Bref:.4f}\n') # Dimensões de referência [cite: 49]
        f.write('#Xref   Yref   Zref\n')
        f.write(f'{0.25*Cref:.4f}  0.0  0.0\n') # Ponto de referência (CG, aprox. 25% da CMA) [cite: 50]
        f.write('\n')

        # --- Definição da Superfície ---
        f.write('#====================================================================\n')
        f.write('SURFACE\n') # Palavra-chave SURFACE [cite: 69]
        f.write(f'{surface_name}\n') # Nome da superfície [cite: 70]
        f.write('#Nchord  Cspace   Nspan  Sspace\n')
        f.write('12  1.0  40  -2.0\n') # Discretização (ajuste conforme necessário) [cite: 71, 265]
        f.write('\n')

        # --- Seções da Asa ---
        for i in range(len(span_positions)):
            f.write('#-----------------------------------------------------------------\n')
            f.write('SECTION\n') # Palavra-chave SECTION [cite: 124]
            f.write(f'#Xle Yle Zle   Chord   Ainc\n')
            Xle = leading_edge_xyz[i, 1] - chords[i] # Posição x do bordo de ataque
            Yle = span_positions[i] # Posição y
            Zle = 0.0 # Posição z
            chord = chords[i]
            ainc = 0.0 # Ângulo de incidência/torção, pode ser parametrizado
            f.write(f'{Xle:.4f}  {Yle:.4f}  {Zle:.4f}  {chord:.4f}  {ainc:.2f}\n') # [cite: 125]
            
            f.write('AFILE\n') # Palavra-chave AFILE [cite: 163]
            f.write(f'{airfoil_files[i]}\n') # Caminho para o arquivo do aerofólio [cite: 164]
            f.write('\n')