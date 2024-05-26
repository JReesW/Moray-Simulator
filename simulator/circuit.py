from collections import Counter


class Current:
    def __init__(self, amps: float, towards: "Node"):
        self.amps = amps
        self.towards = towards

    def __repr__(self):
        return f"({self.amps}A -> {self.towards.name})"


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

        self.voltage = None

    def __repr__(self):
        return f"Node<{self.name}{"" if self.voltage is None else f", {self.voltage}V"}>"


class Resistor(CircuitComponent):
    def __init__(self, name: str, resistance: float, nodes: (Node, Node)):
        CircuitComponent.__init__(self, name)

        self.resistance = resistance
        self.nodes = tuple(sorted(nodes))
        self.current = None
        self.voltage_drop = None

    def __repr__(self):
        return f"Resistor<{self.name}, {self.resistance}Ω, ({", ".join(n.name for n in self.nodes)})>"


class VoltageSource(CircuitComponent):
    def __init__(self, name: str, voltage: float, pos_node: Node, neg_node: Node):
        CircuitComponent.__init__(self, name)

        self.voltage = voltage
        self.pos_node = pos_node
        self.neg_node = neg_node

    def __repr__(self):
        return f"Resistor<{self.name}, {self.voltage}V, {self.pos_node.name} → {self.neg_node.name}>"


"""
Transitions
"""


class Transformation:
    def __init__(self):
        pass


class Series(Transformation):
    def __init__(self, source: [Resistor]):
        Transformation.__init__(self)

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
        Get the resistor that goes over given resistors a and b in a wye-delta transformation
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
The Circuit itself
"""


class Circuit:
    def __init__(self, nodes: [Node], resistors: [Resistor], voltage_source: VoltageSource):
        self.nodes = {node.name: node for node in nodes}
        self.resistors = {resistor.name: resistor for resistor in resistors}
        self.voltage_source = voltage_source  # {voltage_source.name: voltage_source for voltage_source in voltage_sources}

    def simplify(self) -> (Resistor, [Transformation]):
        """
        Simplify this circuit down to a single resistor,
        returning the resistor and list of transformations it took to simplify
        """
        # TODO: add voltage source parameter to specify around which source the circuit should be simplified

        active_resistors = self.resistors.copy()
        transformations = []

        while len(active_resistors) > 1:
            count = Counter(list(sum([r.nodes for r in active_resistors.values()], ())))
            combi_count = Counter([r.nodes for r in active_resistors.values()])

            # TODO: replace with multi-V method
            count[self.voltage_source.pos_node] += 1j
            count[self.voltage_source.neg_node] += 1j

            # Rule 1. Series
            if series_nodes := [n for n in count if count[n] == 2]:
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
                # Uncertain whether the three rules are enough, but at the moment it seems to be
                raise Exception("No rule applicable on the current circuit")

        return list(active_resistors.values())[0], transformations

    def solve(self):
        """
        Solve the circuit, calculating the current and voltage drop going through each resistor
        """
        eq_resistor, transformations = self.simplify()

        self.voltage_source.pos_node.voltage = self.voltage_source.voltage
        self.voltage_source.neg_node.voltage = 0
        current = self.voltage_source.voltage / eq_resistor.resistance
        eq_resistor.current = Current(current, min(eq_resistor.nodes, key=lambda n: n.voltage))

        print(eq_resistor.current)


if __name__ == '__main__':
    # N = {
    #     "alpha": Node("alpha"),
    #     "beta": Node("beta"),
    #     "gamma": Node("gamma"),
    #     "delta": Node("delta"),
    #     "epsilon": Node("epsilon")
    # }
    # R = [
    #     Resistor("A", 5, (N["alpha"], N["beta"])),
    #     Resistor("B", 8, (N["beta"], N["delta"])),
    #     Resistor("C", 3, (N["beta"], N["gamma"])),
    #     Resistor("D", 3, (N["gamma"], N["epsilon"])),
    #     Resistor("E", 4, (N["epsilon"], N["delta"]))
    # ]
    # V = [VoltageSource("V0", 9, N["alpha"], N["delta"])]
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

    circuit = Circuit(N.values(), R, V[0])

    # test
    print(circuit.simplify())
    print(circuit.solve())
