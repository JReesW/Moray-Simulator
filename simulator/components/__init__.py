from simulator.components.gate_valve import GateValve
from simulator.components.globe_valve import GlobeValve
from simulator.components.ball_valve import BallValve
from simulator.components.diaphragm import Diaphragm
from simulator.components.threeway_valve import ThreewayValve
from simulator.components.pump import Pump
from simulator.components.fourway_valve import FourwayValve
from simulator.components.and_gate import AndGate


components_dict = {
    "Gate Valve": GateValve,
    "Globe Valve": GlobeValve,
    "Ball Valve": BallValve,
    "Diaphragm": Diaphragm,
    "Three-Way Valve": ThreewayValve,
    "Pump": Pump,
    "Fourway Valve": FourwayValve,
    "And Valve": AndGate
}
