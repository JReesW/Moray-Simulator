from engine.core import Game
from simulator import SimulationScene


if __name__ == "__main__":
    app = Game(
        starting_scene=SimulationScene,
        caption="Moray - Hydraulic Circuit Simulator"
    )

    while True:
        app.frame()
