from collections import Counter


Blueprint = {str: tuple}


class Current:
    def __init__(self, amps: float, source: "Node", target: "Node"):
        self.amps = amps
        self.source = source
        self.target = target

    def __repr__(self):
        return f"({self.amps}A {self.source.name} -> {self.target.name})"


"""
Circuit components
"""


class CircuitComponent:
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        return hash(self) < hash(other)


class Node(CircuitComponent):
    def __init__(self, name: str):
        CircuitComponent.__init__(self, name)

        # What we are trying to find
        self.voltage = None

    def __repr__(self):
        return f"Node<{self.name}{'' if self.voltage is None else f', {self.voltage}V'}>"


class Resistor(CircuitComponent):
    def __init__(self, name: str, resistance: float, nodes: (Node, Node)):
        CircuitComponent.__init__(self, name)

        self.resistance = resistance
        self.nodes = tuple(sorted(nodes))

        # These are what we are trying to find
        self.current = None
        self.voltage_drop = None

        self.replacements = {}

    def __repr__(self):
        return f"Resistor<{self.name}, {self.resistance}Ω, ({', '.join(n.name for n in self.nodes)})>"


class VoltageSource(CircuitComponent):
    def __init__(self, name: str, voltage: float, neg_node: Node, pos_node: Node):
        CircuitComponent.__init__(self, name)

        self.voltage = voltage
        self.pos_node = pos_node
        self.neg_node = neg_node

    def __repr__(self):
        return f"Resistor<{self.name}, {self.voltage}V, {self.pos_node.name} → {self.neg_node.name}>"


"""
Transformations
"""


class Transformation:
    def __init__(self):
        pass

    def __repr__(self):
        return self.__class__.__name__


class ShortCircuit(Transformation):
    # Represents the removal of a short-circuited resistor, a resistor that connects to the same node on both sides

    def __init__(self, source: Resistor):
        Transformation.__init__(self)

        self.source = source


class DeadEnd(Transformation):
    # Represents the removal of a resistor that is attached to a node with nothing else connected to it

    def __init__(self, source: Resistor, dead_node: Node):
        Transformation.__init__(self)

        self.source = source
        self.dead_node = dead_node


class Series(Transformation):
    def __init__(self, source: [Resistor]):
        Transformation.__init__(self)

        # TODO: maybe specify that the source will basically always be only two resistors
        self.source = source
        resistance = self.get_resistance()
        end_nodes = self.get_end_nodes()
        self.result = Resistor("".join([resistor.name for resistor in self.source]), resistance, end_nodes)

    def get_end_nodes(self) -> (Node, Node):
        """
        Return the end nodes of this transition's series of resistors
        """
        count = Counter(list(sum([r.nodes for r in self.source], ())))
        return tuple([node for node in count if count[node] == 1])

    def get_resistance(self) -> float:
        """
        Calculate the equivalent resistance of all resistors in the series
        """
        return sum([resistor.resistance for resistor in self.source])


class Parallel(Transformation):
    def __init__(self, source: [Resistor]):
        Transformation.__init__(self)

        self.source = source
        resistance = self.get_resistance()
        self.result = Resistor("".join([resistor.name for resistor in self.source]), resistance, self.source[0].nodes)

    def get_resistance(self) -> float:
        """
        Calculate the equivalent resistance of all resistors in the parallel
        """
        return 1 / sum([1 / resistor.resistance for resistor in self.source])


class WyeDelta(Transformation):
    def __init__(self, source: [Resistor]):
        Transformation.__init__(self)

        self.source = source
        self.result = self.get_result()

    def get_result(self) -> [Resistor]:
        """
        Return the new resistors after performing a Wye-Delta transformation
        """
        _a, _b, _c = self.source

        _d = self.get_new_resistor(_a, _b, other=_c)
        _e = self.get_new_resistor(_a, _c, other=_b)
        _f = self.get_new_resistor(_b, _c, other=_a)

        return [_d, _e, _f]

    def get_new_resistor(self, _a: Resistor, _b: Resistor, *, other: Resistor) -> Resistor:
        """
        Get the resistor that goes over given resistors a and b in a Wye-Delta transformation
        """
        count = Counter(list(sum([r.nodes for r in self.source], ())))
        center = [n for n in count if count[n] == 3][0]

        nodes = (
            _a.nodes[0] if _a.nodes[0] != center else _a.nodes[1],
            _b.nodes[0] if _b.nodes[0] != center else _b.nodes[1]
        )
        r = _a.resistance + _b.resistance + ((_a.resistance * _b.resistance) / other.resistance)
        return Resistor(_a.name + _b.name, r, nodes)


"""
Circuit stuff
"""


class SingleVoltCircuit:
    """
    A circuit that includes only a single voltage source
    """

    def __init__(self, nodes: [str], resistors: {str: (float, str, str)}, voltage_source: (str, float, str, str)):
        self.nodes = {name: Node(name) for name in nodes}

        self.resistors = {
            name: Resistor(name, ohm, (self.nodes[node1], self.nodes[node2]))
            for name, (ohm, node1, node2) in resistors.items()
        }

        name, volt, _from, _to = voltage_source
        self.voltage_source = VoltageSource(name, volt, self.nodes[_from], self.nodes[_to])

    def simplify(self) -> (Resistor, [Transformation]):
        """
        Simplify this circuit down to a single resistor,
        returning the resistor and list of transformations it took to simplify
        """

        active_resistors = self.resistors.copy()
        transformations = []

        while len(active_resistors) > 1:
            count = Counter(list(sum([r.nodes for r in active_resistors.values()], ())))
            combi_count = Counter([r.nodes for r in active_resistors.values()])

            count[self.voltage_source.pos_node] += 1j
            count[self.voltage_source.neg_node] += 1j

            # Rule 0a. Short-Circuit
            print(active_resistors)
            if short_circuited := [r for r in active_resistors.values() if r.nodes[0] is r.nodes[1]]:
                for resistor in short_circuited:
                    short_circuit = ShortCircuit(resistor)
                    transformations.append(short_circuit)
                    del active_resistors[resistor.name]

            # Rule 0b. Dead End
            elif dead_nodes := [n for n in count if count[n] == 1]:
                for dead_node in dead_nodes:
                    resistor = [r for r in active_resistors.values() if dead_node in r.nodes][0]
                    dead_end = DeadEnd(resistor, dead_node)
                    transformations.append(dead_end)
                    del active_resistors[resistor.name]

            # Rule 1. Series
            elif series_nodes := [n for n in count if count[n] == 2]:
                node = series_nodes[0]
                resistors = [r for r in active_resistors.values() if node in r.nodes]
                series = Series(resistors)
                transformations.append(series)
                for r in resistors:
                    del active_resistors[r.name]
                active_resistors[series.result.name] = series.result

            # Rule 2. Parallel
            elif parallel_pairs := [combi for combi in combi_count if combi_count[combi] > 1]:
                pair = parallel_pairs[0]
                resistors = [r for r in active_resistors.values() if pair == r.nodes]
                parallel = Parallel(resistors)
                transformations.append(parallel)
                for r in resistors:
                    del active_resistors[r.name]
                active_resistors[parallel.result.name] = parallel.result

            # Rule 3. Wye-Delta
            elif wye_nodes := [n for n in count if count[n] == 3]:
                node = wye_nodes[0]
                resistors = [r for r in active_resistors.values() if node in r.nodes]
                wye_delta = WyeDelta(resistors)
                transformations.append(wye_delta)
                for r in resistors:
                    del active_resistors[r.name]
                for r in wye_delta.result:
                    active_resistors[r.name] = r

            else:
                # Uncertain whether these rules are enough, but at the moment it seems to be
                raise Exception("No rule applicable on the current circuit")

        return list(active_resistors.values())[0], transformations

    def solve(self):
        """
        Solve the circuit, calculating the current and voltage everywhere in the circuit
        """
        # Get the equivalent resistor and the steps it took to get it
        eq_resistor, transformations = self.simplify()

        # Set the initial voltages and currents
        self.voltage_source.pos_node.voltage = self.voltage_source.voltage
        self.voltage_source.neg_node.voltage = 0
        current = self.voltage_source.voltage / eq_resistor.resistance
        eq_resistor.current = Current(current, *sorted(eq_resistor.nodes, key=lambda n: n.voltage, reverse=True))
        eq_resistor.voltage_drop = self.voltage_source.voltage

        # Work backwards through the steps, solving currents and voltages along the way
        for step in reversed(transformations):
            match step:
                case Series(source=[a, b], result=c):
                    # Determine the order in which a and b occur,
                    # stronger being the resistor bordering the higher voltage node
                    weaker, stronger = (a, b) if c.current.target in a.nodes else (b, a)

                    # Both have the same amps in their current. Weaker has the same target node as c,
                    # while stronger targets the node that disappeared during the transformation
                    source_target = sorted(stronger.nodes, key=lambda n: 1 if n.voltage is None else 0)
                    stronger.current = Current(c.current.amps, *source_target)
                    weaker.current = Current(c.current.amps, stronger.current.target, c.current.target)

                    # Calculate the voltage drops
                    stronger.voltage_drop = stronger.current.amps * stronger.resistance
                    weaker.voltage_drop = weaker.current.amps * weaker.resistance
                    stronger.current.target.voltage = stronger.current.source.voltage - stronger.voltage_drop

                case Parallel(source=resistors, result=eq):
                    for resistor in resistors:
                        # No fuss, voltage drop is the same, as are source/target nodes. Only current is calculated with I=V/R
                        resistor.voltage_drop = eq.voltage_drop
                        resistor.current = Current(resistor.voltage_drop / resistor.resistance, eq.current.source, eq.current.target)

                case WyeDelta(source=[a, b, c], result=[d, e, f]):
                    # Get the center node, which disappears during the Wye-Delta transformation
                    center = next(n for n in a.nodes if n.voltage is None)

                    # a gets d and e's currents combined, b gets d and f, c gets e and f
                    for original, first, second in [(a, d, e), (b, d, f), (c, e, f)]:
                        # Whichever node isn't the center node
                        non_center = next(n for n in original.nodes if n is not center)

                        # If both currents go in the same direction, add them together
                        if first.current.source == non_center and second.current.source == non_center:
                            original.current = Current(first.current.amps + second.current.amps, non_center, center)
                        elif first.current.target == non_center and second.current.target == non_center:
                            original.current = Current(first.current.amps + second.current.amps, center, non_center)
                        # Otherwise take the positive difference in amps between the two
                        else:
                            weak, strong = sorted((first.current, second.current), key=lambda cur: cur.amps)
                            source_target = (center, strong.target) if strong.target is non_center else (strong.source, center)
                            original.current = Current(strong.amps - weak.amps, *source_target)

                        # Calculate voltage drop of the resistor and voltage of the new node
                        original.voltage_drop = original.current.amps * original.resistance
                        if original.current.target.voltage is None:
                            original.current.target.voltage = original.current.source.voltage - original.voltage_drop

                case ShortCircuit(source=resistor):
                    resistor.current = Current(0, *resistor.nodes)
                    resistor.voltage_drop = 0

                case DeadEnd(source=resistor, dead_node=dead_node):
                    resistor.current = Current(0, *resistor.nodes)
                    resistor.voltage_drop = 0
                    dead_node.voltage = 0


class Circuit:
    """
    A circuit of resistors and voltage sources connected by nodes
    """

    def __init__(self, nodes: [str], resistors: {str: (float, str, str)}, voltage_sources: {str: (float, str, str)}):
        self.nodes_blueprint = nodes
        self.resistors_blueprint = resistors
        self.voltage_sources_blueprint = voltage_sources

        self.nodes = {name: Node(name) for name in self.nodes_blueprint}
        self.resistors = {
            name: Resistor(name, ohm, (self.nodes[node1], self.nodes[node2]))
            for name, (ohm, node1, node2) in resistors.items()
        }
        self.voltage_source = {
            name: VoltageSource(name, volt, self.nodes[_from], self.nodes[_to])
            for name, (volt, _from, _to) in voltage_sources.items()
        }

    def solve(self):
        """
        Split the circuit up into single voltage-source circuits, solve each individually, and merge them
        """
        circuits = []

        # For every voltage source
        for vs in self.voltage_sources_blueprint:
            # Get the almost-zero resistors that replace the other
            vs_resistors = self.create_vs_resistors(vs)

            # Create and solve the single voltage-source circuit
            voltage_source = (vs, *self.voltage_sources_blueprint[vs])
            sv_circuit = SingleVoltCircuit(self.nodes_blueprint, self.resistors_blueprint | vs_resistors, voltage_source)
            sv_circuit.solve()

            # Store the resulting solved circuit and the replacements that took place (needed for current merging)
            circuits.append(sv_circuit)

        # Merge all single voltage-source circuits into one
        self.merge_circuits(circuits)

    def create_vs_resistors(self, voltage_source: str) -> [(str, str)]:
        """
        Create resistors out of all voltage sources except the given voltage source
        """
        vs_resistors = {}
        for vs, (_, _from, _to) in self.voltage_sources_blueprint.items():
            if vs != voltage_source:
                vs_resistors[vs] = (0.00000000001, _from, _to)
        return vs_resistors

    def merge_circuits(self, circuits: [SingleVoltCircuit]):
        """
        Merge all Single Volt Circuits into one circuit
        """
        # Merge all nodes, simply by adding their voltages together across the circuits
        for node in self.nodes:
            self.nodes[node].voltage = sum([c.nodes[node].voltage for c in circuits])

        for resistor in self.resistors:
            # Take the first circuit as the default
            current: Current = circuits[0].resistors[resistor].current

            # For every other circuit
            for circuit in circuits[1:]:
                other: Current = circuit.resistors[resistor].current

                if current.source == other.source:
                    current.amps += other.amps
                else:
                    if current.amps > other.amps:
                        current.amps -= other.amps
                    else:
                        current.source, current.target = other.source, other.target
                        current.amps = other.amps - current.amps

            self.resistors[resistor].current = current
            self.resistors[resistor].voltage_drop = self.resistors[resistor].current.amps * self.resistors[resistor].resistance


if __name__ == '__main__':
    # List of node names
    N = ["alpha", "beta", "gamma", "delta", "epsilon"]

    # Resistor name as key, (resistance, node1, node2) as value
    R = {
        "A": (8, "alpha", "beta"),
        "B": (6, "beta", "delta"),
        "C": (3, "beta", "gamma"),
        "D": (4, "delta", "epsilon")
    }

    # Voltage source name as key, (voltage, from, to) as value
    V = {
        "V0": (6, "epsilon", "alpha"),
        "V1": (3, "gamma", "delta")
    }

    example_circuit = Circuit(N, R, V)

    # test
    example_circuit.solve()
    for _r in example_circuit.resistors.values():
        print(_r.name, _r.resistance, _r.current, _r.voltage_drop, f"({' <-> '.join([n.name for n in _r.nodes])})")
    for _n in example_circuit.nodes.values():
        print(_n.name, _n.voltage)


"""
Misc tests

# Series and parallel example, see whiteboard photo
N = ["alpha", "beta", "gamma", "delta"]
R = {
    "A": (5, "alpha", "beta"),
    "B": (8, "beta", "delta"),
    "C": (3, "beta", "gamma").
    "D": (7, "gamma", "delta")
}

R = [
    Resistor("A", 5, (N["alpha"], N["beta"])),
    Resistor("B", 8, (N["beta"], N["delta"])),
    Resistor("C", 3, (N["beta"], N["gamma"])),
    Resistor("D", 7, (N["gamma"], N["delta"]))
]
V = [VoltageSource("V0", 9, N["alpha"], N["delta"])]


# Wye-Delta, parallel, and series, see WYE-DELTA QUESTION google doc
N = {
    "alpha": Node("alpha"),
    "beta": Node("beta"),
    "gamma": Node("gamma"),
    "delta": Node("delta")
}
R = [
    Resistor("A", 6, (N["alpha"], N["beta"])),
    Resistor("B", 8, (N["alpha"], N["gamma"])),
    Resistor("C", 4, (N["beta"], N["gamma"])),
    Resistor("D", 8, (N["beta"], N["delta"])),
    Resistor("E", 10, (N["gamma"], N["delta"]))
]
V = [VoltageSource("V0", 8, N["alpha"], N["delta"])]


# Simple series test
N = {
    "alpha": Node("alpha"),
    "beta": Node("beta"),
    "gamma": Node("gamma")
}
R = [
    Resistor("A", 6, (N["alpha"], N["beta"])),
    Resistor("B", 8, (N["beta"], N["gamma"]))
]
V = [VoltageSource("V0", 8, N["alpha"], N["gamma"])]

"""
