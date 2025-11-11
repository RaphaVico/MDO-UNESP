import numpy as np
from scipy.special import comb
from matplotlib import pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import axes3d
import os
import logging
class BezierAirfoil():
    def __init__(self, properties):
        self.properties = properties
        self.properties["te_x1"] = properties["semi_span"]/3
        self.properties["te_x2"] = 2 * properties["semi_span"]/3

        self.properties["te_y1"] = 0.1
        self.properties["te_y2"] = 0.15
        self.properties["te_y3"] = 0.3


        self.properties["le_x1"] = properties["semi_span"]/3
        self.properties["le_x2"] = 2 * properties["semi_span"]/3

        self.properties["le_y1"]  = 1.1
        self.properties["le_y2"] = 0.9
        self.properties["le_y3"] = self.properties["te_y3"] + properties["chord_tip"]

        self.properties["span"] = np.linspace(0., np.pi/2, properties['number_of_panels']) *self.properties["semi_span"]
        span_points = np.array((0, self.properties["semi_span"]/3, 2*self.properties["semi_span"]/3, self.properties["semi_span"]))
        lagrange_basis = self.lagrange_polynomials(span_points)

        leading_edge_points = np.array(((0., self.properties["chord_root"]), (self.properties["le_x1"], self.properties["le_y1"]), (self.properties["le_x2"], self.properties["le_y2"]), (self.properties["semi_span"], self.properties["le_y3"])))
        trailing_edge_points = np.array(((0., 0.), (self.properties["te_x1"], self.properties["te_y1"]), (self.properties["te_x2"], self.properties["te_y2"]), (self.properties["semi_span"], self.properties["te_y3"])))

        thickness_points = np.array(properties["thicks"])
        camber_points = np.array(properties["cambers"])
        camber_pos_points = np.array(properties["cambers_pos"])

        self.leading_edge = self.bezier_curve(leading_edge_points, self.properties["span"])
        trailing_edge = self.bezier_curve(trailing_edge_points, self.properties["span"])

        self.properties["chord"] = self.leading_edge[:,1] - trailing_edge[:,1]

        self.properties["thickness"] = self.lagrange_curve(lagrange_basis, self.properties["span"], thickness_points)
        self.properties["camber"]= self.lagrange_curve(lagrange_basis, self.properties["span"], camber_points)
        self.properties["camber_pos"] = self.lagrange_curve(lagrange_basis, self.properties["span"], camber_pos_points)


        self.ze_points = []
        self.ye_points = []
        self.xe_points = []

    
        for i in range(self.properties["number_of_panels"]):
            # Certifique-se de que naca_4digits retorna coordenadas normalizadas (x/c, y/c)
            
            xu, yu = self.naca_4digits(self.properties["camber"][i], self.properties["camber_pos"][i], self.properties["thickness"][i])
            self.properties[f"xu_{i}"] = xu
            self.properties[f"yu_{i}"] = yu
            z = np.ones(xu.shape) * self.properties["span"][i]
            self.properties[f"z_{i}"] = z

            #Isso aqui é pra pegar os pontos do bordo de ataque
            idx_min = np.argmin(xu)
            # Coordenadas dos pontos mínimos
            z_min = z[idx_min]
            xu_min = xu[idx_min]
            yu_min = yu[idx_min]
            self.ze_points.append(z_min)
            self.ye_points.append(yu_min)
            self.xe_points.append(xu_min)
            logging.info(f"--- Seção {i} ---")
            logging.info(f"Corda: {self.properties['chord'][i]:.4f}")
            logging.info(f"Espessura: {self.properties['thickness'][i]:.4f}")
            logging.info(f"Cambra: {self.properties['camber'][i]:.4f}")
            logging.info(f"Pos. Cambra: {self.properties['camber_pos'][i]:.4f}")


        # self.properties["xe_points"] = [np.mean(self.properties[])]
        self.properties["ze_points"] = [np.mean(self.properties[f"z_{i}"]) for i in range(self.properties["number_of_panels"])]

    def write_airfoil_files(self, output_dir='airfoils'):
            """
            Escreve os arquivos de coordenadas .dat para cada seção da asa.
            """
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            airfoil_files = []
            for i in range(self.properties["number_of_panels"]):
                airfoil_name = f'bezier_section_{i}'
                file_path = os.path.join(output_dir, f'{airfoil_name}.dat')

                # Pega as coordenadas normalizadas
                x_coords = self.properties[f"xu_{i}"]
                y_coords = self.properties[f"yu_{i}"]

                with open(file_path, 'w') as f:
                    f.write(f'{airfoil_name}\n')
                    for x, y in zip(x_coords, y_coords):
                        f.write(f'{x:.6f} {y:.6f}\n')
                
                airfoil_files.append(file_path)
                
            return airfoil_files
    def lagrange_polynomials(self,xj):
        n = len(xj)
        polynomials = []

        for i in range(n):

            def lagrange_basis(x, i=i):
                li = 1
                for j in range(n):
                    if i != j:
                        li *= (x - xj[j]) / (xj[i] - xj[j])
                return li

            polynomials.append(lagrange_basis)

        return polynomials

    def bezier_curve(self, control_points, coords):
        control_points = np.array(control_points)
        n = len(control_points) - 1
        d = control_points.shape[1]
        num_points = len(coords)

        # --- CORREÇÃO FUNDAMENTAL AQUI ---
        # O parâmetro 't' de uma curva de Bezier DEVE estar no intervalo [0, 1].
        # Estamos normalizando as coordenadas da envergadura para esse intervalo.
        # Se coords[-1] for 0, evitamos divisão por zero, embora seja um caso de borda.
        max_coord = coords[-1] if coords[-1] > 0 else 1.0
        t = coords / max_coord  # Normaliza o vetor (ex: [0,..,3.0] -> [0,..,1.0])

        curve = np.zeros((num_points, d))

        for i in range(n + 1):
            binomial = comb(n, i)
            bernstein = binomial * (t ** i) * ((1 - t) ** (n - i))
            curve += np.outer(bernstein, control_points[i])

        return curve
    
    def lagrange_curve(self,lagrange_basis, x, y):
        curve = np.zeros(x.shape)

        for i in range(len(y)):
            curve += y[i] * lagrange_basis[i](x)

        return curve
    
    # def naca_4digits(self, camber, camber_pos, thickness): # Removido 'chord'
    #         x = np.linspace(0, 1., 100)
    #         x_start = x[x <= camber_pos]
    #         x_finish = x[x > camber_pos]

    #         yt = 5 * thickness * ( 0.2969 * np.sqrt(x) - 0.1260*x - 0.3516*x**2 + 0.2843*x**3 - 0.1015*x**4)

    #         # ... (resto da função como antes) ...
    #         mid_start = camber / camber_pos**2 * (2 * camber_pos * x_start - x_start**2.)
    #         mid_finish = camber / (1 - camber_pos)**2 * ( (1 - 2*camber_pos) + 2 * camber_pos * x_finish - x_finish**2.)

    #         dmid_start = 2 * camber / camber_pos**2 * (camber_pos - x_start)
    #         dmid_finish = 2 * camber / (1 - camber_pos)**2 * (camber_pos - x_finish)

    #         mid = np.array((*mid_start, *mid_finish)).flatten()
    #         dmid = np.array((*dmid_start, *dmid_finish)).flatten()

    #         theta = np.atan(dmid)
    #         sin = np.sin(theta)
    #         cos = np.cos(theta)

    #         xu = x - yt * sin
    #         xl = x + yt * sin
    #         yu = mid + yt * cos
    #         yl = mid - yt * cos
            
    #         # Não multiplique por 'chord' aqui!
    #         return np.array((*xu[::-1], *xl)).flatten(), np.array((*yu[::-1], *yl)).flatten()
    def naca_4digits(self, camber, camber_pos, thickness):
        x = np.linspace(0, 1., 100)
        
        # Garantir que o bordo de ataque (x=0) esteja presente
        if x[0] != 0:
            x = np.concatenate([[0], x])
        
        x_start = x[x <= camber_pos]
        x_finish = x[x > camber_pos]

        yt = 5 * thickness * (0.2969 * np.sqrt(x) - 0.1260*x - 0.3516*x**2 + 0.2843*x**3 - 0.1015*x**4)

        mid_start = camber / camber_pos**2 * (2 * camber_pos * x_start - x_start**2.)
        mid_finish = camber / (1 - camber_pos)**2 * ((1 - 2*camber_pos) + 2 * camber_pos * x_finish - x_finish**2.)

        dmid_start = 2 * camber / camber_pos**2 * (camber_pos - x_start)
        dmid_finish = 2 * camber / (1 - camber_pos)**2 * (camber_pos - x_finish)

        mid = np.concatenate([mid_start, mid_finish])
        dmid = np.concatenate([dmid_start, dmid_finish])

        theta = np.arctan(dmid)
        
        xu = x - yt * np.sin(theta)
        yu = mid + yt * np.cos(theta)
        xl = x + yt * np.sin(theta)
        yl = mid - yt * np.cos(theta)
        
        # Garantir ordenação correta: do bordo de fuga superior para o inferior
        # Primeiro: pontos superiores do TE ao LE
        x_upper = xu[::-1]
        y_upper = yu[::-1]
        
        # Depois: pontos inferiores do LE ao TE (excluindo o LE para não duplicar)
        x_lower = xl[1:]
        y_lower = yl[1:]
        
        # Combinar todos os pontos
        x_total = np.concatenate([x_upper, x_lower])
        y_total = np.concatenate([y_upper, y_lower])
        
        return x_total, y_total
    def plot(self):
            fig = plt.figure()
            ax = fig.add_subplot(projection='3d')

            # Listas para armazenar os mínimos
            z_min_list = []
            xu_min_list = []
            yu_min_list = []

            for i in range(self.properties["number_of_panels"]):
                xu = self.properties[f"xu_{i}"]
                xu += self.leading_edge[i,1] #isso precisa ser somado antes ou só no plot?
                yu = self.properties[f"yu_{i}"]
                z = self.properties[f"z_{i}"]

                ax.plot(z, xu, yu, label=f'Curva {i}')

                # Índices dos máximos e mínimos
                idx_max = np.argmax(xu)
                idx_min = np.argmin(xu)

                # Coordenadas dos pontos máximos
                z_max = z[idx_max]
                xu_max = xu[idx_max]
                yu_max = yu[idx_max]

                # Coordenadas dos pontos mínimos
                z_min = z[idx_min]
                xu_min = xu[idx_min]
                yu_min = yu[idx_min]

                # Salvar mínimos para depois ligar
                z_min_list.append(z_min)
                xu_min_list.append(xu_min)
                yu_min_list.append(yu_min)
            ax.set_xlabel('Z')
            ax.set_ylabel('X')
            ax.set_zlabel('Y')
            ax.set_aspect('equal')
            ax.set_title('Curvas de Aerofólio')
            plt.show()
