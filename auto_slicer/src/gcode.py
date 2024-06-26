
__all__ = ["GCode", "Move"]


class Move:
    def __init__(self, command):
        self.__command: str = command
        self.__comment: str | bool = self.__command \
            .strip().split(";")[1] if ";" in self.__command else False
        self.__command: str = self.__command.strip().split(";")[0].strip()

        self.type = self.__command[0].strip()
        self.number = self.__command[1:].split(" ", 1)[0].strip()
        param = self.__command[1:].split(" ", 1)[1:]
        self.parameters: dict[str, float] = {}
        if param:
            if ":" in param[0]:
                param = param[0].split(":")
                self.parameters = {param[i].strip(): param[i + 1].strip() for i in range(0, len(param), 2)}
            elif "_" in param[0]:
                param = param[0].split(" ")
                self.parameters = {"flags": [flag.strip() for flag in param]}
            else:
                param = param[0].split(" ") if param else []
                self.parameters = {p[0]: p[1:] for p in param if p}

        if self.type == "G" and self.parameters:
            for key in self.parameters:
                try:
                    self.parameters[key] = float(self.parameters[key])
                except ValueError:
                    pass

    def __str__(self):
        return f"{self.type} {self.number} {self.parameters if self.parameters else ''}" + \
            (f"\t # {self.__comment}" if self.__comment else "")

    def __repr__(self):
        return f"Move({str(self)})" + f" Comment({self.__comment})"

    def __len__(self):
        return len(self.__command)


class GCode:
    def __init__(self, gcode: str):
        if not isinstance(gcode, str):
            raise ValueError("GCode must be a string")
        self.__gcode_data: str = gcode
        self.__config: dict = {}
        self.__moves: list[Move] = []
        self.__data = self.__gcode_data.strip().split("\n")
        self.__parse()

    def __iter__(self):
        return iter(self.__data)

    def __parse(self):
        for line in self.__data:
            line = line.strip()
            if line.startswith("; ") or line.startswith(";"):
                if "=" in line:
                    key, value = line[2:].split("=", 1)
                    self.update_config({key.strip(): value.strip()})
            elif line.startswith(";="):
                continue
            else:
                if line:
                    move = Move(line)
                    self.update_moves([move])

    def update_config(self, config: dict):
        self.__config.update(config)

    def set_config(self, config: dict):
        self.__config = config

    def configs(self):
        return self.__config

    def update_moves(self, moves: list[Move]):
        self.__moves.extend(moves)

    def set_moves(self, moves: list):
        self.__moves = moves

    def moves(self, type: str | None = None):
        if type:
            return [move for move in self.__moves if move.type == type]
        return self.__moves

    def move_types(self):
        m = [str(move.type)+str(move.number) for move in self.__moves]
        types = list(set(m))
        types.sort()
        return types

    def __str__(self):
        return "\n".join([f"{key}: {value}" for key, value in self.__config.items()] + [str(move) for move in self.__moves])

    def __repr__(self):
        return f"GCode({str(self)})"

    def __len__(self):
        return len(self.__data)
