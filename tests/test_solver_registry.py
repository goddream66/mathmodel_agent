from mathagent.solvers import SolverRegistry, SolverSpec, get_builtin_solver_registry


def test_solver_registry_selects_highest_score() -> None:
    registry = SolverRegistry()
    registry.register(
        SolverSpec(
            name="generic",
            matcher=lambda context: 0.1,
            builder=lambda context: ("generic summary", "print('generic')"),
        )
    )
    registry.register(
        SolverSpec(
            name="specialized",
            matcher=lambda context: 0.9 if context.get("kind") == "special" else 0.0,
            builder=lambda context: ("special summary", "print('special')"),
        )
    )

    selection = registry.select({"kind": "special"})

    assert selection is not None
    assert selection.name == "specialized"
    assert selection.summary == "special summary"
    assert selection.score == 0.9


def test_builtin_solver_registry_exposes_core_solvers() -> None:
    names = get_builtin_solver_registry().list_names()

    assert "forecast" in names
    assert "optimization" in names
    assert "path_network" in names
    assert "evaluation" in names
    assert "generic" in names
