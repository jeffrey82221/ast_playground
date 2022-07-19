import ast
import astunparse

# 1. Parsing the Simple Function


def simple_function_parsing(ast_module):
    for node in ast_module.body:
        if isinstance(node, ast.FunctionDef):
            print('Function Name:', node.name)
            for i, arg in enumerate(node.args.args):
                print('Arg', i, arg.arg)
            for const in node.args.defaults:
                print('Default value:', const.value)
            print('Unparsed Function:\n', astunparse.unparse(node))


# 2. Parsing the class method
def class_method_parsing(ast_module, class_name, function_name):
    for node in ast_module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            print('Class Name', node.name)
            for method in node.body:

                if method.name == function_name:
                    print('Function Name:', method.name)
                    for i, arg in enumerate(method.args.args):
                        print('Arg', i, arg.arg)
                    for const in method.args.defaults:
                        print('Default value:', const.value)
                    print('Unparsed Function:\n', astunparse.unparse(method))

# 3. Parsing class defined in the same file:


class UDFClass:
    def __init__(self):
        pass

    def run_all(self, x, y, c=12):
        x = x + 1
        y = c + x
        y = y * 2
        return x + y

    def parse_run_all(self):
        f = open(__file__, 'r')
        module = ast.parse(f.read())
        class_method_parsing(module, __class__.__name__, 'run_all')


if __name__ == '__main__':
    f = open('example.py', 'r')
    module = ast.parse(f.read())
    print(1, 'Parsing of Function in example.py')
    simple_function_parsing(module)
    print(2, 'Parsing of Class Method in example.py')
    class_method_parsing(module, 'Demo', 'simple_function')
    print(3, 'Parsing of Class Method Here!')
    UDFClass().parse_run_all()
