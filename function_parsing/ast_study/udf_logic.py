import ast
import random
from typing import List

import astpretty
import astunparse

# Define reconstructed function string (expected result)
run_all_str = """
def run_all_cudf(leadi, leadii, leadiii, leadavr, i_ii, i_iii, i_avr):
    def sub(x, y):
        return x - y

    def run_all(leadi, leadii, leadiii, leadavr):
        i_ii = sub(leadi, leadii)
        i_iii = sub(leadi, leadiii)
        i_avr = sub(leadi, leadavr)

        return [i_ii, i_iii, i_avr]   # or i_ii, i_iii, i_avr

    for idx, (a, b, c, d) in enumerate(zip(leadi, leadii, leadiii, leadavr)):
        i_ii[idx], i_iii[idx], i_avr[idx] = run_all(a, b, c, d)
"""
exec(run_all_str)


class UDFLogic:
    """User-defined function logic.

    Note that this class might be inherited from a child class of
    `LogicBase`. Hence, some properties and common logic can't be seen
    here.

    1. What if there's operation taking class attributes into
       consideration?
    """

    @property
    def input_column_names(self):
        return [
            "leadi",
            "leadii",
            "leadiii",
            "leadavr",
        ]

    @property
    def output_column_names(self):
        return ["i_ii", "i_iii", "i_avr"]

    @property
    def output_column_dtypes(self):
        """Prototyped in logic base, but flexible. (only in cudf mode)"""
        return {"i_ii": np.int16, "i_iii": np.int16, "i_avr": np.int16}

    @property
    def run_all_boost(self):
        self.__check()
        run_all_numba = self.__parse_run_all()
        print(ast.dump(run_all_numba))
        
        return run_all_numba

    def sub(self, x, y):
        return x - y

    def run_all(self, leadi, leadii, leadiii, leadavr):
        i_ii = self.sub(leadi, leadii)
        i_iii = self.sub(leadi, leadiii)
        i_avr = self.sub(leadi, leadavr)

        return [i_ii, i_iii, i_avr]

    def __check(self):
        pass

    def __parse_run_all(self):
        """Parse `run_all` and construct corresponding numba kernel.
        
        For convenience of parsing, location fields are always ignored,
        making astpretty.pprint raise error (Name obj has no attr lineno).
        """
        with open(__file__, "r") as f:
            module = ast.parse(f.read())

        for node in module.body:
            if isinstance(node, ast.ClassDef) and node.name == self.__class__.__name__:
                for in_cls_node in node.body:
                    if (
                        isinstance(in_cls_node, ast.FunctionDef)
                        and in_cls_node.name == "run_all"
                    ):
                        # Retrieve udf input columns (arguments)
                        run_all_inputs = in_cls_node.args.args
                        run_all_inputs.pop(0)  # Remove parameter `self`

                        # Retrieve udf output columns (returns)
                        for sub_node in in_cls_node.body:
                            if isinstance(sub_node, ast.Return):
                                run_all_outputs = sub_node.value.elts

                        # Convert class method call to normal function call
                        cls_method_trafo = ClassMethodTrafo()
                        run_all_inner = cls_method_trafo.visit(in_cls_node)
                
                inner_fns = self.__build_inner_sub_logics(node, cls_method_trafo.sub_logics)
                inner_fns.append(run_all_inner)

                run_all_numba = self.__gen_run_all_numba_kernel(
                    run_all_inputs, run_all_outputs, inner_fns
                )
        
        return run_all_numba
        
    def __build_inner_sub_logics(
        self, node: ast.AST, sub_logics: List[str]
    ) -> List[ast.FunctionDef]:
        """Return inner functions called by user defined function
        `run_all`.

        Parameter:
            node: user-defined logic class node
            sub_logics: inner function names

        Return:
            inner_fns: list of inner functions
        """
        inner_fns = []
        for in_cls_node in node.body:
            if isinstance(in_cls_node, ast.FunctionDef) and in_cls_node.name in sub_logics:
                in_cls_node.args.args.pop(0)   # Remove parameter `self`
                inner_fns.append(in_cls_node)

        return inner_fns

    def __gen_run_all_numba_kernel(
        self, args: List[ast.arg], returns: List[ast.Name], body: List[ast.FunctionDef]
    ) -> ast.FunctionDef:
        """Return numba kernel function corresponding to user-defined
        function `run_all`.
        
        Parameters:
            args: list of input columns
            returns: list of output columns
            body: function body
        
        Return:
            run_all_numba: numba kernel function
        """
        def __build_inner_for() -> ast.For:
            """Build numba kernel inner for loop.
            
            Return:
                inner_for: numba kernel inner for loop
            """
            inner_for = ast.For(
                target=ast.Tuple(
                    elts=[
                        ast.Name(id="i", ctx=ast.Store()),
                        ast.Tuple(
                            elts=[
                                ast.Name(id=f"x{i}", ctx=ast.Store())
                                for i in range(len(args))
                            ],
                            ctx=ast.Store(),
                        ),
                    ],
                    ctx=ast.Store(),
                ),
                iter=ast.Call(
                    func=ast.Name(
                        id="enumerate",
                        ctx=ast.Load(),
                    ),
                    args=[
                        ast.Call(
                            func=ast.Name(
                                id="zip",
                                ctx=ast.Load(),
                            ),
                            args=args,
                            keywords=[],
                        ),
                    ],
                    keywords=[],
                ),
                body=ast.Assign(
                    targets=[
                        ast.Tuple(
                            elts=[
                                ast.Subscript(
                                    value=output,
                                    slice=ast.Index(value=ast.Name(id="i", ctx=ast.Load())),
                                    ctx=ast.Store(),
                                )
                                for output in returns
                            ],
                            ctx=ast.Store(),
                        )
                    ],
                    value=ast.Call(
                        func=ast.Name(id="run_all", ctx=ast.Load()),
                        args=[
                            ast.Name(id=f"x{i}", ctx=ast.Load()) for i in range(len(args))
                        ],
                        keywords=[],
                    ),
                    type_comment=False,
                ),
                orelse=[],
                type_comment=False,
            )
            
            return inner_for
        
        # Reconstruct numba kernel function arguments
        run_all_numba_args = ast.arguments(
            posonlyargs=[],
            args=args + returns,
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[],
        )

        # Reconstruct numba kernel function body
        run_all_numba_body = body.copy()
        inner_for = __build_inner_for()
        run_all_numba_body.append(inner_for)
        
        # Define numba kernal function
        run_all_numba = ast.FunctionDef(
            name="run_all_numba",
            args=run_all_numba_args,
            body=run_all_numba_body,
            decorator_list=[],
            returns=None,
            type_comment=None,
        )

        return run_all_numba


class ClassMethodTrafo(ast.NodeTransformer):
    """Node transformer converting class method call to normal function
    call.

    All class methods called in `run_all` are recorded for further
    inner function reconstruction.
    """

    def __init__(self):
        self.sub_logics = []

    def visit_Call(self, node: ast.Call) -> ast.Call:
        """Apply trafo to visited node.
        
        Parameters:
            node: visited node to transform
            
        Return:
            node_trans: transformed node
        """
        if node.func.value.id == "self":
            sub_logic_name = node.func.attr
            if sub_logic_name not in self.sub_logics:
                self.sub_logics.append(sub_logic_name)
                
        node_trans = ast.copy_location(
            ast.Call(
                func=ast.Name(
                    id=node.func.attr,
                    ctx=ast.Load(),
                ),
                args=node.args,
                keywords=node.keywords,
            ),
            node,
        )

        return node_trans


def main() -> None:
    udf_logic = UDFLogic()
    run_all_boost = udf_logic.run_all_boost


if __name__ == "__main__":
    main()
