from typing import Any
import re


class Connectable:
    """
    Defines a thing's connections, one for each cardinal direction NESW
    """

    def __init__(self, open_sides: str, name: str = "---"):
        if not re.match(r"^(?!.*(.).*\1)[NESW]*$", open_sides):
            raise Exception("Invalid sides string given to Connectable. Only use one of each of NESW")

        self.connections: dict[str, Any] = {c: None for c in open_sides}
        self.name = name

    def rotate_connections(self, clockwise=True):
        cw = -1 if clockwise else 1
        self.connections = {"NESW"[i]: None for i in range(4) if "NESW"[(i + cw) % 4] in self.connections}

    def connect(self, other: "Connectable", connection: str):
        opposite = "NESW"[("NESW".index(connection) + 2) % 4]
        self.connections[connection] = other
        other.connections[opposite] = self

    def __repr__(self):
        res = ""
        for d in "NESW":
            res += f"{d}: "
            if d not in self.connections:
                res += "Blocked\n"
            elif self.connections[d] is None:
                res += "None\n"
            else:
                res += self.connections[d].name + "\n"
        return res


if __name__ == '__main__':
    b = Connectable("", "B")
    test = Connectable("NSW", "A")
    test.connect(b, "S")
    print(test)
    test.rotate_connections()
    print(test)
