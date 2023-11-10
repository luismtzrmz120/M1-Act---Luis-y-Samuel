from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
import random

class Coche(Agent):
    def __init__(self, unique_id, model, initial_position):
        super().__init__(unique_id, model)
        self.probabilidad_fallo = 0.1
        self.pos = initial_position
        self.movimiento_permitido = True

    def move(self):
        if self.pos[1] < self.model.longitud_camino - 1 and self.movimiento_permitido:
            new_position = (self.pos[0], self.pos[1] + 1)
            if self.model.grid.is_cell_empty(new_position):
                self.model.grid.move_agent(self, new_position)
            elif random.random() > self.probabilidad_fallo:
                new_position = random.choice([(self.pos[0] + 1, self.pos[1] + 1),
                                              (self.pos[0] - 1, self.pos[1] + 1)])
                if self.model.grid.is_cell_empty(new_position):
                    self.model.grid.move_agent(self, new_position)
                else:
                    choque_agent = Choque(new_position, self.model)
                    self.model.grid.place_agent(choque_agent, new_position)
                    self.movimiento_permitido = False

class CocheContrario(Agent):
    def __init__(self, unique_id, model, initial_position):
        super().__init__(unique_id, model)
        self.probabilidad_fallo = 0.1
        self.pos = initial_position

    def move(self):
        if self.pos[1] > 0:
            new_position = (self.pos[0], self.pos[1] - 1)
            if self.model.grid.is_cell_empty(new_position):
                self.model.grid.move_agent(self, new_position)
            elif random.random() > self.probabilidad_fallo:
                new_position = random.choice([(self.pos[0] + 1, self.pos[1] - 1),
                                              (self.pos[0] - 1, self.pos[1] - 1)])
                if self.model.grid.is_cell_empty(new_position):
                    self.model.grid.move_agent(self, new_position)
                else:
                    self.model.grid.place_agent(Choque(new_position, self.model), new_position)

class CocheIzquierdaDerecha(Agent):
    def __init__(self, unique_id, model, initial_position):
        super().__init__(unique_id, model)
        self.probabilidad_fallo = 0.1
        self.pos = initial_position
        self.movimiento_permitido = True

    def move(self):
        if self.pos[0] < self.model.longitud_camino - 1 and self.movimiento_permitido:
            new_position = (self.pos[0] + 1, self.pos[1])
            if self.model.grid.is_cell_empty(new_position):
                self.model.grid.move_agent(self, new_position)
            elif random.random() > self.probabilidad_fallo:
                new_position = random.choice([(self.pos[0] + 1, self.pos[1] + 1),
                                              (self.pos[0] + 1, self.pos[1] - 1)])
                if self.model.grid.is_cell_empty(new_position):
                    self.model.grid.move_agent(self, new_position)
                else:
                    choque_agent = Choque(new_position, self.model)
                    self.model.grid.place_agent(choque_agent, new_position)
                    self.movimiento_permitido = False

class SimulacionCoches(Model):
    def __init__(self, num_coches, num_coches_contrarios, num_obstaculos, num_coches_izquierda_derecha, longitud_camino, probabilidad_fallo):
        self.num_coches = num_coches
        self.num_coches_contrarios = num_coches_contrarios
        self.num_obstaculos = num_obstaculos
        self.num_coches_izquierda_derecha = num_coches_izquierda_derecha
        self.longitud_camino = longitud_camino
        self.probabilidad_fallo = probabilidad_fallo
        self.grid = MultiGrid(longitud_camino, longitud_camino, True)
        self.schedule = RandomActivation(self)

        obstaculos_positions = [
            (2, 5), (4, 7), (6, 3), (8, 9), (10, 4), (12, 8),
            (1, 2), (3, 5), (5, 8), (7, 11), (9, 6), (11, 9),
            (2, 10), (4, 4), (6, 12), (8, 2), (10, 8), (12, 5)
        ]

        for obstaculo_pos in obstaculos_positions:
            self.grid.place_agent(Obstaculo(obstaculo_pos, self), obstaculo_pos)

        coches_iniciales = [(random.randint(0, longitud_camino-1), 0) for _ in range(num_coches)]
        for i in range(num_coches):
            coche = Coche(i, self, coches_iniciales[i])
            self.schedule.add(coche)
            self.grid.place_agent(coche, coches_iniciales[i])

        coches_contrarios_iniciales = [(random.randint(0, longitud_camino-1), longitud_camino-1) for _ in range(2)]
        for i in range(2):
            coche_contrario = CocheContrario(i + num_coches, self, coches_contrarios_iniciales[i])
            self.schedule.add(coche_contrario)
            self.grid.place_agent(coche_contrario, coches_contrarios_iniciales[i])

        coches_izquierda_derecha_iniciales = [(0, random.randint(1, longitud_camino-1)) for _ in range(num_coches_izquierda_derecha)]
        for i in range(num_coches_izquierda_derecha):
            coche_izquierda_derecha = CocheIzquierdaDerecha(i + num_coches + num_coches_contrarios, self, coches_izquierda_derecha_iniciales[i])
            self.schedule.add(coche_izquierda_derecha)
            self.grid.place_agent(coche_izquierda_derecha, coches_izquierda_derecha_iniciales[i])

        self.datacollector = DataCollector(
            agent_reporters={"Posicion": "pos"},
            model_reporters={"Espacio Libre": lambda m: sum(1 for x in range(m.grid.width) for y in range(m.grid.height) if m.grid.is_cell_empty((x, y)))}
        )

    def step(self):
        self.datacollector.collect(self)
        agentes_a_mover = list(self.schedule.agents)
        for agente in agentes_a_mover:
            if isinstance(agente, Coche) or isinstance(agente, CocheContrario) or isinstance(agente, CocheIzquierdaDerecha):
                agente.move()

class Obstaculo(Agent):
    def __init__(self, pos, model):
        super().__init__(pos, model)

class Choque(Agent):
    def __init__(self, pos, model):
        super().__init__(pos, model)

def agent_portrayal(agent):
    portrayal = {"Shape": "circle",
                 "Filled": "true",
                 "Layer": 0,
                 "Color": "red" if isinstance(agent, Coche) else "black",
                 "r": 0.5}
    if isinstance(agent, CocheContrario):
        portrayal["Color"] = "green"
    elif isinstance(agent, CocheIzquierdaDerecha):
        portrayal["Color"] = "blue"
    elif isinstance(agent, Obstaculo):
        portrayal["Color"] = "black"
    elif isinstance(agent, Choque):
        portrayal["Color"] = "cyan"
    return portrayal

model_params = {
    "num_coches": 8,
    "num_coches_contrarios": 2,
    "num_obstaculos": 18,
    "num_coches_izquierda_derecha": 2,
    "longitud_camino": 15,
    "probabilidad_fallo": 0.1,
}

grid = CanvasGrid(agent_portrayal, model_params["longitud_camino"], model_params["longitud_camino"], 500, 500)
server = ModularServer(SimulacionCoches, [grid], "Simulacion Coches", model_params)
server.port = 8521
server.launch()
