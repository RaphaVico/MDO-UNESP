from MDO_UNESP.bezier_airfoil import BezierAirfoil
from MDO_UNESP.plot_airfoils import plot_airfoils
from MDO_UNESP.avl_generator import create_avl_config_from_bezier
from MDO_UNESP.avl_runner import get_aero_coef
import logging
import numpy as np
import matplotlib.pyplot as plt
#Naca 2414
properties = {
    "semi_span": 1,
    "number_of_panels": 25,
    "chord_root": 1,
    "chord_tip": 0.8,
    "thicks": [0.14, 0.14, 0.14, 0.14],
    "cambers": [0.02, 0.02, 0.02, 0.02],
    "cambers_pos": [0.40, 0.40, 0.40, 0.40],
    "Cl_max": 1.2
}
camber = 0.02
thickness = 0.14
camber_pos = 0.40
def gerar_naca_code(camber, camber_pos, thickness):
    """
    Gera o número NACA (4 dígitos) a partir de camber, posição e espessura.
    Entradas devem ser frações da corda (ex: 0.02 = 2%).
    """
    # Converter para porcentagem
    camber_pct = camber * 100
    camber_pos_pct = camber_pos * 10   # cuidado: segundo dígito é em décimos da corda
    thickness_pct = thickness * 100

    # Arredondar valores para inteiros
    camber_digit = round(camber_pct)
    camber_pos_digit = round(camber_pos_pct)
    thickness_digits = round(thickness_pct)

    # Garantir que os dígitos caibam no formato NACA
    camber_digit = min(max(camber_digit, 0), 9)
    camber_pos_digit = min(max(camber_pos_digit, 0), 9)
    thickness_digits = min(max(thickness_digits, 0), 99)

    # Montar o código NACA
    naca_code = f"{camber_digit}{camber_pos_digit}{thickness_digits:02d}"
    return naca_code

logging.info(f'Generating NACA number for camber={camber}, camber_pos={camber_pos}, thickness={thickness}')
naca_number = gerar_naca_code(camber, camber_pos, thickness)
logging.info(f'Generated NACA number: {naca_number}')
teste = BezierAirfoil(properties)


airfoil_files = teste.write_airfoil_files(output_dir='airfoils')


teste.properties["airfoil_files"] = airfoil_files
create_avl_config_from_bezier('bezier_wing.avl', teste, surface_name="bezier_wing")
teste.plot()

naca = teste.naca_4digits(camber, camber_pos, thickness)
logging.info(f'NACA 4 digits coordinates: {naca}')
plot_airfoils(coords=naca, airfoil_name=f'NACA {naca_number}')
cl_max, cd_max, cm_max = get_aero_coef('bezier_wing.avl', properties["Cl_max"], alpha_start=-9, alpha_end=12.5, alpha_step=0.250)


alphas = cl_max.keys()
cl_max = list(cl_max.values())
logging.info(f'Cl vs Alpha data: {cl_max}')

plt.plot(alphas, cl_max, marker='o')
plt.title('Cl vs Alpha for Bezier Airfoil')
plt.xlabel('Alpha (degrees)')
plt.ylabel('Cl')
plt.grid(True)

plt.show()
logging.info(f'Calculated Cl_max from BezierAirfoil: {cl_max}')