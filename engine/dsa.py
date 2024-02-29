from typing import Callable
from collections import defaultdict
import bisect


# TODO: remove test
class Test:
    def __init__(self, lbl: str, z: int):
        self.lbl = lbl
        self.z = z

    def __repr__(self):
        return f"<{self.lbl}>"


class LayerContainer[T]:
    def __init__(self, layer_func: Callable[[T], int]):
        """
        A Container with layers
        :param layer_func: the function that returns the layer int for a given element
        """
        self._layer_func = layer_func
        self._layer_ids: list[T] = []
        self._layers: dict[int: T] = defaultdict(lambda: [])

    def add(self, elem: T):
        """
        Add an element to the container
        """
        index = self._layer_func(elem)

        if index not in self._layer_ids:
            bisect.insort_left(self._layer_ids, index)

        self._layers[index].append(elem)

    def __repr__(self):
        kw = len(str(max(self._layer_ids, key=lambda x: len(str(x)))))
        vw = len(str(max(self._layers.values(), key=lambda x: len(str(x))))) - 2

        # deliciously disgusting...
        res = f"┌Layers{'─' * (kw + vw - 5)}┐\n"
        for i, k in enumerate(self._layer_ids):
            res += f"│{k: >{kw}}:{str(self._layers[k])[1:-1].ljust(vw)}│\n"
        res += f"└{'─' * (kw + vw + 1)}┘"

        return res


if __name__ == '__main__':
    layers = LayerContainer(lambda e: e.z)
    layers.add(Test('A', 2))
    layers.add(Test('B', 2))
    layers.add(Test('E', 2))
    layers.add(Test('F', 2))
    layers.add(Test('C', 15))
    layers.add(Test('D', 4))
    print(layers)
