"""Smoke tests — import validation and basic instantiation."""
import ast
import pathlib


def test_all_sources_parse():
    """Every .py file in the repository must parse cleanly."""
    root = pathlib.Path(__file__).parent.parent
    src = root / "src"
    if not src.exists():
        src = root
    errors = []
    for f in src.rglob("*.py"):
        try:
            ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError as e:
            errors.append(f"{f}: {e}")
    assert not errors, "\n".join(errors)


def test_package_importable():
    """Top-level package must import without SyntaxError."""
    try:
        import africa_coord_bus  # noqa: F401
    except ImportError:
        # Acceptable if optional deps absent in test env — SyntaxError is not.
        pass
