"""
Handles parsing the drawn circuit to a format that can be solved
"""

from simulator.connectable import Connection, Connectable
from simulator.component import Component
from simulator.components import GateValve, Pump, Fitting, ThreewayValve
from simulator.pipe import Pipe
from simulator.circuit import Circuit, Node, Current

from itertools import chain
from collections import defaultdict


class PipeCurrent:
    def __init__(self, current: float, max_current: float, direction, voltage):
        self.current = current
        self.max_current = max_current
        self.direction = direction
        self.voltage = voltage

    def __repr__(self):
        return f"[{self.current}A / {self.max_current}A -> {self.direction}]"


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


def separate_disjointed_circuits(nodes: [str], valves: {str: (float, str, str)}, pumps: {str: (float, str, str)}):
    """
    Split up the list of nodes and components into disjointed lists of nodes and components
    """
    nodes_left = set(nodes)
    circuits = []

    while nodes_left:
        nodes_to_check = [nodes_left.pop()]
        new_valves = {}
        new_pumps = {}

        for node in nodes_to_check:
            for _, a, b in (valves | pumps).values():
                if a == node and b in nodes_left:
                    nodes_to_check.append(b)
                    nodes_left.remove(b)
                elif b == node and a in nodes_left:
                    nodes_to_check.append(a)
                    nodes_left.remove(a)

        for node in nodes_to_check:
            for name, (v, a, b) in valves.items():
                if a == node or b == node:
                    new_valves[name] = (v, a, b)
            for name, (v, a, b) in pumps.items():
                if a == node or b == node:
                    new_pumps[name] = (v, a, b)

        circuits.append((nodes_to_check, new_valves, new_pumps))

    # Remove circuits without pumps or without valves
    circuits = [c for c in circuits if len(c[1]) > 0]
    circuits = [c for c in circuits if len(c[2]) > 0]

    return circuits


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

    # Split the nodes and components into disjointed circuits
    split_circuits = separate_disjointed_circuits(nodes, valves, pumps)
    circuits = []

    # Solve each disjointed circuit
    for n, v, p in split_circuits:
        circuit = Circuit(n, v, p)
        circuit.solve()
        circuits.append(circuit)

    # Print it (unnecessary for later)
    for circuit in circuits:
        print("")
        __valves = {v.name: v for v in _valves}
        __threes = {t.name: t for t in _threes}
        for _r in circuit.resistors.values():
            if ".r" in _r.name:
                __threes[_r.name[:-2]].circuit_red_valve = _r
            elif ".b" in _r.name:
                __threes[_r.name[:-2]].circuit_blue_valve = _r
            else:
                __valves[_r.name].circuit_valve = _r
            print(f"{_r.name}, which has a resistance of {_r.resistance} Ohms and connects nodes {' and '.join([n.name for n in _r.nodes])} "
                  f"with current {_r.current}")
        print("")
        for _n in circuit.nodes.values():
            color_names = ["red", "blue", "orange", "green", "yellow", "cyan", "purple", "pink", "sienna", "rosy brown", "orchid", "olive"]
            print(f"Node {_n.name} (colored {color_names[int(_n.name) % len(color_names)]}) has a voltage of {_n.voltage} Volts")
        print("")
        __pumps = {p.name: p for p in _pumps}
        for _v in circuit.voltage_sources.values():
            __pumps[_v.name].circuit_pump = _v
            print(f"Voltage source {_v.name} (with voltage {_v.voltage}) has a current of {_v.current}")
        print("\n" + ("-" * 30))


def assign_pipe_current_in_node(node: Node, io: {str: [(Connectable, Current)]}):
    """
    Assign current to individual pipes within a single node
    """
    ins_outs = defaultdict(lambda: {"in": [], "out": [], "dir": None})

    for (comp_in, curr_in) in io["in"]:
        conn: Connection = [c for c, n in comp_in.nodes.items() if n == node.name][0]  # pycharm tripping

        stack = [conn.other_comp()]
        dist = 1
        distances = {stack[0]: dist}

        # While the stack isn't empty
        while stack:
            # Pop the first connectable from the stack
            c: Connectable = stack.pop(0)

            # Get all neighboring components that are pipes/fittings and aren't
            neighbors = [_c.other_comp() for _c in c.connections if isinstance(_c.other_comp(), (Pipe, Fitting))]
            unassigned = [_c for _c in neighbors if _c not in distances]

            # Assign the distance to the component
            for u in unassigned:
                distances[u] = distances[c] + 1
                stack.append(u)

        # For each out
        for (comp_out, curr_out) in io["out"]:
            # TODO: decide if this threeway valve anomaly is worth it
            # if isinstance(comp_out, ThreewayValve):
            #     conns =
            conn: Connection = [c for c, n in comp_out.nodes.items() if n == node.name][0]  # pycharm tripping once more

            # Trace back through the distances to get the shortest path
            while distances[conn.other_comp()] > 1:
                comp, _dir = conn.other_comp(), conn.opposite()
                ins_outs[comp]["in"].append(curr_in)
                ins_outs[comp]["out"].append(curr_out)
                ins_outs[comp]["dir"] = _dir

                conns = [c for c in comp.connections if c is not None and isinstance(c.other_comp(), (Pipe, Fitting))]
                conn = min(
                    conns,
                    key=lambda c: distances[c.other_comp()]
                )
            comp, _dir = conn.other_comp(), conn.opposite()
            ins_outs[comp]["in"].append(curr_in)
            ins_outs[comp]["out"].append(curr_out)
            ins_outs[comp]["dir"] = _dir

    # Separate pipes from fittings
    pipes = []
    fittings = []
    for comp, io in ins_outs.items():
        if isinstance(comp, Pipe):
            pipes.append((comp, io))
        else:
            fittings.append((comp, io))

    # Assign the smaller current of the combined ins and combined outs as the pipe's current
    # largest = 0
    for pipe, io in pipes:
        total_in = sum([cur.amps for cur in io["in"]])
        total_out = sum([cur.amps for cur in io["out"]])

        pipe.current = PipeCurrent(min(total_in, total_out), 0, io["dir"], node.voltage)
        # if pipe.current.current > largest:
        #     largest = pipe.current.current

    # for pipe, _ in pipes:
    #     pipe.current.max_current = largest


def assign_pipe_current(_components, _pipes):
    """
    Assign currents to individual pipes
    """
    nodes = defaultdict(lambda: {"in": [], "out": []})
    components = [c for c in _components if isinstance(c, (Pump, GateValve, ThreewayValve))]

    # Pair all components with the current going through them
    component_current = []
    for component in components:
        if isinstance(component, Pump):
            component_current.append((component, component.circuit_pump.current))
        elif isinstance(component, GateValve):
            component_current.append((component, component.circuit_valve.current))
        elif isinstance(component, ThreewayValve):
            component_current.append((component, component.circuit_red_valve.current))
            component_current.append((component, component.circuit_blue_valve.current))

    # Filter out the components with a current of 0, and determine the strongest current
    component_current = [(co, cu) for co, cu in component_current if cu.amps > 0]

    # Divide the components into the inputs and outputs of nodes
    for co, cu in component_current:
        nodes[cu.source]["out"].append((co, cu))
        nodes[cu.target]["in"].append((co, cu))

    # For each node, pathfind each input to each output
    node: Node
    for node, io in nodes.items():
        assign_pipe_current_in_node(node, io)

    # Assign the largest current to each pipe
    largest = 0
    for pipe in _pipes:
        if pipe.current is not None and pipe.current.current > largest:
            largest = pipe.current.current

    for pipe in _pipes:
        if pipe.current is not None:
            pipe.current.max_current = largest
