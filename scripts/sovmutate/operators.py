"""Mechanical mutation operators over a Python syntax tree.

Every operator is a deterministic transform of the source under test. Nothing
here encodes an opinion about what the code should do: a mutant is produced by
arithmetic on the tree, not by judgement, which is what lets a mutation score
witness a test suite without the suite's author also authoring its adversary.

One call to ``mutate`` changes exactly one site, so a surviving mutant names a
single unasserted behaviour rather than a diffuse gap.
"""

from __future__ import annotations

from dataclasses import dataclass
import ast

COMPARE_SWAPS = {
    ast.Lt: ast.LtE, ast.LtE: ast.Lt,
    ast.Gt: ast.GtE, ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
    ast.Is: ast.IsNot, ast.IsNot: ast.Is,
    ast.In: ast.NotIn, ast.NotIn: ast.In,
}

BINOP_SWAPS = {
    ast.Add: ast.Sub, ast.Sub: ast.Add,
    ast.Mult: ast.FloorDiv, ast.FloorDiv: ast.Mult,
}

BOOLOP_SWAPS = {ast.And: ast.Or, ast.Or: ast.And}


@dataclass(frozen=True)
class Site:
    """One mutable location: what would change, and how it reads in a report."""

    index: int
    line: int
    operator: str
    description: str


def _describe(node: ast.AST) -> tuple[str, str] | None:
    """Name the mutation this node admits, or None if it admits none."""
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        op = type(node.ops[0])
        if op in COMPARE_SWAPS:
            return "compare", f"{op.__name__} -> {COMPARE_SWAPS[op].__name__}"
    if isinstance(node, ast.BinOp) and type(node.op) in BINOP_SWAPS:
        op = type(node.op)
        return "binop", f"{op.__name__} -> {BINOP_SWAPS[op].__name__}"
    if isinstance(node, ast.BoolOp) and type(node.op) in BOOLOP_SWAPS:
        op = type(node.op)
        return "boolop", f"{op.__name__} -> {BOOLOP_SWAPS[op].__name__}"
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return "unary", "drop not"
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return "constant", f"{node.value} -> {not node.value}"
        if isinstance(node.value, int):
            return "constant", f"{node.value} -> {node.value + 1}"
    if isinstance(node, ast.Return) and node.value is not None:
        return "return", "return value -> None"
    return None


def _mutate_node(node: ast.AST) -> ast.AST:
    """Return the mutated form of a node ``_describe`` accepted."""
    if isinstance(node, ast.Compare):
        return ast.Compare(
            left=node.left,
            ops=[COMPARE_SWAPS[type(node.ops[0])]()],
            comparators=node.comparators,
        )
    if isinstance(node, ast.BinOp):
        return ast.BinOp(left=node.left, op=BINOP_SWAPS[type(node.op)](), right=node.right)
    if isinstance(node, ast.BoolOp):
        return ast.BoolOp(op=BOOLOP_SWAPS[type(node.op)](), values=node.values)
    if isinstance(node, ast.UnaryOp):
        return node.operand
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return ast.Constant(value=not node.value)
        return ast.Constant(value=node.value + 1)
    if isinstance(node, ast.Return):
        return ast.Return(value=None)
    raise ValueError(f"no mutation defined for {type(node).__name__}")


class _Walker(ast.NodeVisitor):
    """Collect every mutable site in deterministic document order."""

    def __init__(self) -> None:
        self.sites: list[Site] = []

    def generic_visit(self, node: ast.AST) -> None:
        described = _describe(node)
        if described is not None:
            operator, description = described
            self.sites.append(Site(
                index=len(self.sites),
                line=getattr(node, "lineno", 0),
                operator=operator,
                description=description,
            ))
        super().generic_visit(node)


class _Applier(ast.NodeTransformer):
    """Mutate exactly the site at ``target``, leaving every other site alone."""

    def __init__(self, target: int) -> None:
        self.target = target
        self.seen = 0
        self.applied = False

    def generic_visit(self, node: ast.AST) -> ast.AST:
        described = _describe(node)
        if described is None:
            return super().generic_visit(node)
        here = self.seen
        self.seen += 1
        if here != self.target:
            return super().generic_visit(node)
        self.applied = True
        return ast.copy_location(_mutate_node(node), node)


def sites(source: str) -> list[Site]:
    """Every mutable site in ``source``, in document order."""
    walker = _Walker()
    walker.visit(ast.parse(source))
    return walker.sites


def mutate(source: str, index: int) -> str:
    """Source with exactly the site at ``index`` mutated.

    Raises ``IndexError`` when the index names no site, so a caller can never
    silently score a mutant that was never applied.
    """
    tree = ast.parse(source)
    applier = _Applier(index)
    mutated = applier.visit(tree)
    if not applier.applied:
        raise IndexError(f"no mutation site at index {index}")
    ast.fix_missing_locations(mutated)
    return ast.unparse(mutated)
