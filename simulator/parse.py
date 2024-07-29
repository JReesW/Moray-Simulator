"""
Handles parsing the drawn circuit to a format that can be solved
"""

import pygame

from simulator.connectable import Connectable, Connection
# TODO: Threeway valves
from simulator.component import Component
from simulator.components import GateValve, Pump, Fitting, ThreewayValve
from simulator.pipe import Pipe

import ctypes


def assign_nodes(components):
    pumps = [comp for comp in components if isinstance(comp, Pump)]
    valves = [comp for comp in components if isinstance(comp, GateValve) or isinstance(comp, ThreewayValve)]
    pumps_valves = [*pumps, *valves]

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
                    visited[c] = node_id
                    if c.connection is not None:
                        visited[c.connection] = node_id

                    # If the connection is part of a pipe or fitting,
                    # add all unvisited connections on the other side to the stack
                    if type(c.other_comp()) in [Pipe, Fitting]:
                        stack += [_c for _c in c.other_comp().connections if _c not in visited]
                    # Otherwise add only the opposing connection if it exists
                    elif c.other_comp() is not None and c.connection not in visited:
                        stack.append(c.connection)

    for o, n in visited.items():
        # For the components, register the nodes they connect to
        if "Pump" in o.connectable.name or "Gate" in o.connectable.name or "Thre" in o.connectable.name:
            o.connectable.nodes[o] = n
        # For the pipes, assign which node they are a part of
        elif type(o.connectable) in [Fitting, Pipe]:
            o.connectable.node = n
