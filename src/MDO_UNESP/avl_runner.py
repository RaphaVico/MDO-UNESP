import subprocess
import os
from math import radians
import numpy as np
import logging
import tqdm
# import pandas as pd


import fileinput
from typing import Optional


def get_value(output_file: str, variable_name: str) -> Optional[float]:
    """
    Extrai um valor float associado a uma variável específica em um arquivo.

    Args:
        output_file: Caminho do arquivo a ser lido
        variable_name: Nome da variável buscada

    Returns:
        Valor float associado à variável ou None se não encontrado
    """
    with open(output_file, 'r') as file:
        for line in file:
            # Normaliza espaços para facilitar parsing
            normalized_line = line.replace('     ', '/')
            
            if variable_name in normalized_line:
                # Remove espaços e divide em elementos
                elements = normalized_line.replace(' ', '').split('/')
                
                for element in elements:
                    if variable_name in element:
                        _, value = element.split('=')
                        return float(value.strip())
    
    return None


def _calculate_geometry(c1: float, c2: float, c3: float, 
                       y1: float, y2: float, y3: float) -> tuple:
    """
    Calcula propriedades geométricas da asa.
    
    Returns:
        Tuple com (S_total, MAC, B_total)
    """
    # Cálculo de áreas
    S_section1 = (c1 + c2) * (y2 - y1) * 0.5
    S_section2 = (c2 + c3) * (y3 - y2) * 0.5
    S_total = 2 * (S_section1 + S_section2)

    # Cálculo da corda média aerodinâmica (MAC)
    MAC_section1 = c1 - (2 * (c1 - c2) * (0.5 * c1 + c2) / (3 * (c1 + c2)))
    MAC_section2 = c2 - (2 * (c2 - c3) * (0.5 * c2 + c3) / (3 * (c2 + c3)))
    MAC = (MAC_section1 * S_section1 + MAC_section2 * S_section2) / (S_section1 + S_section2)

    # Envergadura total
    B_total = 2 * (y3 - y1)

    return S_total, MAC, B_total


def _create_substitution_dict(surface_name: str, airfoil1_file: str, airfoil2_file: str, airfoil3_file: str,
                             x: float, y1: float, y2: float, y3: float, z: float,
                             c1: float, c2: float, c3: float, angle_incidence: float,
                             twist1: float, twist2: float, twist3: float, 
                             S_total: float, MAC: float, B_total: float) -> dict:
    """
    Cria dicionário com os valores de substituição para cada marcador.
    """
    return {
        f'#Dimensoes_referencia_{surface_name}': f'{S_total:.4f} {MAC:.4f} {B_total:.4f}',
        f'#Localizacao_cg_{surface_name}': f'{MAC/4:.4f} 0 0',
        f'#arquivo_{surface_name}_1': airfoil1_file,
        f'#arquivo_{surface_name}_2': airfoil2_file,
        f'#arquivo_{surface_name}_3': airfoil3_file,
        f'#Angulo_incidencia_{surface_name}': str(angle_incidence),
        f'#Dimensao_{surface_name}_secao_1': f'{x} {y1} {z} {c1} {twist1} 0 0',
        f'#Dimensao_{surface_name}_secao_2': f'{x} {y2} {z} {c2} {twist2} 0 0',
        f'#Dimensao_{surface_name}_secao_3': f'{x} {y3} {z} {c3} {twist3} 0 0'
    }


def set_dimensions(config_file: str, airfoil1_file: str, airfoil2_file: str, airfoil3_file: str,
                  surface_name: str, x: float, y1: float, y2: float, y3: float, z: float,
                  c1: float, c2: float, c3: float, angle_incidence: float,
                  twist1: float, twist2: float, twist3: float) -> None:
    """
    Atualiza arquivo de configuração com novas dimensões e parâmetros.

    Args:
        config_file: Arquivo de configuração a ser modificado
        airfoilX_file: Arquivos dos perfis aerodinâmicos
        surface_name: Nome da superfície
        x, y1, y2, y3, z: Coordenadas das seções
        c1, c2, c3: Cordas das seções
        angle_incidence: Ângulo de incidência
        twist1, twist2, twist3: Torções das seções
    """
    # Cálculos geométricos
    S_total, MAC, B_total = _calculate_geometry(c1, c2, c3, y1, y2, y3)
    
    # Dicionário de substituições
    substitutions = _create_substitution_dict(
        surface_name, airfoil1_file, airfoil2_file, airfoil3_file,
        x, y1, y2, y3, z, c1, c2, c3, angle_incidence, twist1, twist2, twist3,
        S_total, MAC, B_total
    )

    # Processa o arquivo
    with fileinput.input(config_file, inplace=True) as file:
        next_line_to_replace = None
        
        for line in file:
            line = line.rstrip('\n')  # Remove quebra de linha existente
            
            if next_line_to_replace:
                print(substitutions[next_line_to_replace])
                next_line_to_replace = None
            elif line in substitutions:
                print(line)
                next_line_to_replace = line
            else:
                print(line)

def get_clmax(output_file):
    """
    Lê um arquivo de saída do AVL e encontra o valor máximo da coluna 'cl'
    sem usar a biblioteca pandas.
    """
    try:
        with open(output_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        logging.exception(f"Erro: Arquivo não encontrado em '{output_file}'")
        return None
    # logging.info(f"Lendo arquivo: {output_file}")
    # logging.info(f"Número total de linhas no arquivo: {len(lines)}")
    # logging.info(f"Primeiras 5 linhas do arquivo:\n{''.join(lines[:5])}")
    # O código original com pandas pulava as linhas [0-18, 20].
    # Isso significa que a linha 19 (índice 18) era o cabeçalho.
    # Vamos assumir que o formato do arquivo é consistente.
    header_line_index = 19 
    
    if len(lines) <= header_line_index:
        logging.exception("Erro: Arquivo muito curto para conter um cabeçalho na linha esperada.")
        return None

    # 1. Encontrar a posição da coluna 'cl' no cabeçalho
    header = lines[header_line_index].strip().split()
    try:
        # Procuramos por 'cl'. Pode ser que o cabeçalho original seja "c" "cl",
        # que o pandas leria como duas colunas. Vamos procurar por 'cl'.
        cl_column_index = header.index('cl')
    except ValueError:
        logging.exception(f"Erro: Coluna 'cl' não encontrada no cabeçalho do arquivo: {header}")
        return None

    # 2. Definir o intervalo das linhas de dados
    # O skiprows era [0...18, 20], então os dados começam na linha 21 (índice 20).
    # O skipfooter era 28, então ignoramos as últimas 28 linhas.
    start_data_index = 21
    end_data_index = len(lines) - 28

    max_cl = -float('inf')  # Inicia com um valor muito pequeno
    found_data = False

    # 3. Iterar sobre as linhas de dados e encontrar o valor máximo
    for i in range(start_data_index, end_data_index):
        line = lines[i]
        
        # Ignora linhas em branco
        if not line.strip():
            continue
            
        values = line.strip().split()
        
        try:
            # Pega o valor da coluna 'cl' usando o índice que encontramos
            cl_value_str = values[cl_column_index]
            cl_value = float(cl_value_str)
            
            if cl_value > max_cl:
                max_cl = cl_value
            
            found_data = True
            
        except (IndexError, ValueError):
            continue

    if not found_data:
        logging.exception("Aviso: Nenhum dado numérico válido foi encontrado para 'cl'.")
        return None # Ou 0.0, dependendo do que for mais apropriado

    return max_cl



# Supondo que você tenha as funções get_clmax e get_value definidas em outro lugar
# from your_helpers import get_clmax, get_value 

def get_aero_coef(config_file, Cl_max_airfoil,alpha_start, alpha_end, alpha_step):
    dir_name = os.path.dirname(os.path.abspath(__file__))
    outputs_path = os.path.join(dir_name, 'outputs')
    output_file = os.path.join(outputs_path, 'coeficients')
    output2_file = os.path.join(outputs_path, 'coeficients_along_span')
    avl_file = os.path.join(dir_name, 'avl.exe')

    alpha_range = np.arange(alpha_start, alpha_end, alpha_step)

    CL_dict = {}
    CD_dict = {}
    Cm_dict = {}

    #Verifica se os diretorios existem e cria se não existirem
    if not os.path.exists(outputs_path):
        os.makedirs(outputs_path)
    if not os.path.exists(avl_file):
        raise FileNotFoundError(f"Arquivo AVL não encontrado em '{avl_file}'")
    

    # Garante que os arquivos existam antes do loop
    open(output_file, 'w').close()
    open(output2_file, 'w').close()

    # Usar tqdm para mostrar barra de progresso
    for alpha in alpha_range:
        os.remove(output_file)
        os.remove(output2_file)


        comm_string = f'load {config_file}\n oper\n a\n a\n {alpha}\n x\n ft\n{output_file}\nfs\n{output2_file}\n'
        # logging.info(f'Running AVL for alpha={alpha} degrees with command string:\n{comm_string}')
        
        # Usar with para garantir que o processo seja fechado
        #stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        with subprocess.Popen([avl_file], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True) as process:
            process.communicate(bytes(comm_string, encoding='utf8'))
        # logging.info(f'Finished AVL run for alpha={alpha} degrees')
        # Supondo que as funções auxiliares (get_clmax, get_value) existam e funcionem
        # logging.info(f'Calculating aerodynamic coefficients for alpha={alpha} degrees')
        # logging.info(f"output_file: {output_file}")
        # logging.info(f"output2_file: {output2_file}")
        # logging.info(f"Cl_max_airfoil: {Cl_max_airfoil}")
        # logging.info(f"Getting Cl_max from output2_file: {get_clmax(output2_file)}")
        if get_clmax(output2_file) > Cl_max_airfoil:
            break
        else:
            CL_dict[alpha] = get_value(output_file, 'CLtot')
            CD_dict[alpha] = get_value(output_file, 'CDtot')
            Cm_dict[alpha] = get_value(output_file, 'Cmtot')

    # ----- PARTE DO PANDAS REMOVIDA -----
    # CL_df = pd.DataFrame.from_dict(CL_dict,  orient="index", columns=["CL"])
    # CL_df.index.name = 'alpha'
    # CD_df = pd.DataFrame.from_dict(CD_dict,  orient="index", columns=["CD"])
    # CD_df.index.name = 'alpha'
    # Cm_df = pd.DataFrame.from_dict(Cm_dict,  orient="index", columns=["CM"])
    # Cm_df.index.name = 'alpha'

    # Retorna apenas os dicionários
    return CL_dict, CD_dict, Cm_dict
# def get_aero_coef(config_file, Cl_max_airfoil):
#     dir_name = os.path.dirname(os.path.abspath(__file__))
#     outputs_path = os.path.join(dir_name, 'outputs')
#     output_file = os.path.join(outputs_path, 'coeficients')
#     output2_file = os.path.join(outputs_path, 'coeficients_along_span')
#     avl_file = os.path.join(dir_name, 'avl.exe')

#     alpha_range = np.arange(-20, 21, 1)

#     CL_dict = {}
#     CD_dict = {}
#     Cm_dict = {}

#     open(output_file, 'a').close()
#     open(output2_file, 'a').close()


#     for alpha in alpha_range:
#         os.remove(output_file)
#         os.remove(output2_file)
#         comm_string = 'load {}\n oper\n a\n a\n {}\n x\n ft\n{}\nfs\n{}\n'.format(config_file, alpha, output_file, output2_file)
#         Process=subprocess.Popen([avl_file], stdin=subprocess.PIPE, shell = True)
#         Process.communicate(bytes(comm_string, encoding='utf8'))
#         if get_clmax(output2_file) > Cl_max_airfoil:
#             break
#         else:
#             CL_dict[alpha] = get_value(output_file, 'CLtot')
#             CD_dict[alpha] = get_value(output_file, 'CDtot')
#             Cm_dict[alpha] = get_value(output_file, 'Cmtot')

#     CL_df = pd.DataFrame.from_dict(CL_dict,  orient="index", columns=["CL"])
#     CL_df.index.name = 'alpha'
#     CD_df = pd.DataFrame.from_dict(CD_dict,  orient="index", columns=["CD"])
#     CD_df.index.name = 'alpha'
#     Cm_df = pd.DataFrame.from_dict(Cm_dict,  orient="index", columns=["CM"])
#     Cm_df.index.name = 'alpha'

#     return CL_dict, CD_dict, Cm_dict, CL_df, CD_df, Cm_df