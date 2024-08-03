"""
Handles parsing the drawn circuit to a format that can be solved
"""

from simulator.connectable import Connection
from simulator.component import Component
from simulator.components import GateValve, Pump, Fitting, ThreewayValve
from simulator.pipe import Pipe
from simulator.circuit import Circuit

from itertools import chain


def assign_nodes(components) -> None:
    """
    Walks through all components and pipes to separate them into nodes.
    Assigns to pipes/fittings to which node they belong, and to components to which nodes they connect
    """
    pumps_valves = [comp for comp in components if type(comp) in [Pump, GateValve, ThreewayValve]]

    # ID's of visited Connection ID's as keys, node they belong to as value
    visited = {}
    node_id = -1

    # For each component, check their connections
    pv: Component
    for pv in pumps_valves:

        # For each connection, if not already handled, start a BFS from this connection
        conn: Connection
        for conn in pv.connections:

            # If not previously visited
            if conn not in visited:
                stack = [conn]

                # Next node ID
                node_id += 1

                # While the stack isn't empty
                while stack:
                    # Pop the first connection and mark it (and its connection) as visited
                    c: Connection = stack.pop(0)
                    visited[c] = str(node_id)
                    if c.connection is not None:
                        visited[c.connection] = str(node_id)

                    # If the connection is part of a pipe or fitting,
                    # add all unvisited connections on the other side to the stack
                    if type(c.other_comp()) in [Pipe, Fitting]:
                        stack += [_c for _c in c.other_comp().connections if _c not in visited]
                    # Otherwise add only the opposing connection if it exists
                    elif c.other_comp() is not None and c.connection not in visited:
                        stack.append(c.connection)

    for o, n in visited.items():
        # For the components, register the nodes they connect to
        if type(o.connectable) in (Pump, GateValve, ThreewayValve):
            o.connectable.nodes[o] = n
        # For the pipes, assign which node they are a part of
        elif type(o.connectable) in [Fitting, Pipe]:
            o.connectable.node = n


def separate_disjointed_circuits():
    pass


def parse(components) -> None:
    """
    Parse all components into a format suitable for the circuit solver, and solve the circuit
    """
    # Separate the pumps and the valves
    _pumps = [comp for comp in components if isinstance(comp, Pump)]
    _valves = [comp for comp in components if isinstance(comp, GateValve)]
    _threes = [comp for comp in components if isinstance(comp, ThreewayValve)]

    # Gather all the nodes
    pump_nodes = set(chain.from_iterable([pump.nodes.values() for pump in _pumps]))
    valve_nodes = set(chain.from_iterable([valve.nodes.values() for valve in _valves]))
    three_nodes = set(chain.from_iterable([three.nodes.values() for three in _threes]))
    nodes = pump_nodes | valve_nodes | three_nodes

    # Parse the pumps
    pumps = {}
    for p in _pumps:
        _from, _to = p.get_from_to()
        pumps[p.name] = (p.text_value, p.nodes[_from], p.nodes[_to])

    # Parse the valves
    valves = {v.name: (v.text_value, *v.nodes.values()) for v in _valves}

    # Parse the threeway valves
    for three in _threes:
        _open, blue, red = three.open_blue_red_connections()
        o_node, b_node, r_node = [three.nodes[s] for s in (_open, blue, red)]
        b_res, r_res = three.text_value * three.blue_part, three.text_value * (1 - three.blue_part)
        valves[three.name + ".b"] = (b_res, o_node, b_node)
        valves[three.name + ".r"] = (r_res, o_node, r_node)

    # Solve the circuit
    # TODO: Use flood fill to separate disjointed circuits
    circuit = Circuit(nodes, valves, pumps)
    circuit.solve()

    # Print it (unnecessary for later)
    for _r in circuit.resistors.values():
        print(_r.name, _r.resistance, _r.current, _r.voltage_drop, f"({' <-> '.join([n.name for n in _r.nodes])})")
    for _n in circuit.nodes.values():
        print(_n.name, _n.voltage)
