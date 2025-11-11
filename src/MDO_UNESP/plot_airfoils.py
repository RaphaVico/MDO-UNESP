import logging
import matplotlib.pyplot as plt
def plot_airfoils(file=None, coords=None, airfoil_name=None, figsize=(10, 5)):
    if file:
        with open(file, 'r') as f:
            lines = f.readlines()
            airfoil_name = lines[0].strip()
            airfoil_data = [list(map(float, line.split())) for line in lines[1:] if line.strip()]
            x, y = zip(*airfoil_data)
    else:
        if coords is None or airfoil_name is None:
            raise ValueError("If 'file' is not provided, both 'coords' and 'airfoil_name' must be specified.")
        logging.info(f'Plotting airfoil: {airfoil_name}')
        logging.info(f'Coordinates provided: {coords}')
        x = coords[0]
        y = coords[1]
    plt.figure(figsize=figsize)
    plt.plot(x, y, label=airfoil_name)
    plt.title(f'Airfoil: {airfoil_name}')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.axis('equal')
    plt.grid(True)
    plt.legend()
    plt.show()

