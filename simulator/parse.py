"""
Handles parsing the drawn circuit to a format that can be solved
"""

from simulator.connectable import Connection
from simulator.component import Component
from simulator.components import GateValve, Pump, Fitting, ThreewayValve
from simulator.pipe import Pipe
from simulator.circuit import Circuit

from itertools import chain


def assign_nodes(components):
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


def parse(components):
    _pumps = [comp for comp in components if isinstance(comp, Pump)]
    _valves = [comp for comp in components if isinstance(comp, GateValve)]

    pump_nodes = set(chain.from_iterable([pump.nodes.values() for pump in _pumps]))
    valve_nodes = set(chain.from_iterable([valve.nodes.values() for valve in _valves]))
    nodes = pump_nodes | valve_nodes

    pumps = {}
    for p in _pumps:
        _from, _to = p.get_from_to()
        pumps[p.name] = (p.text_value, p.nodes[_from], p.nodes[_to])

    valves = {v.name: (v.text_value, *v.nodes.values()) for v in _valves}

    circuit = Circuit(nodes, valves, pumps)
    circuit.solve()

    # Print it (unnecessary for later)
    for _r in circuit.resistors.values():
        print(_r.name, _r.resistance, _r.current, _r.voltage_drop, f"({' <-> '.join([n.name for n in _r.nodes])})")
    for _n in circuit.nodes.values():
        print(_n.name, _n.voltage)
