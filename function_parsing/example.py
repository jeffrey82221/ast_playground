# Demo python file


a = 31
b = 12


def simple_function(x, y, c=12):
    x = x + 1
    y = c + x
    y = y * 2
    return x + y


class Demo:
    def __init__(self):
        pass

    def simple_function(self, x, y, c=12):
        x = x + 1
        y = c + x
        y = y * 2
        return x + y
