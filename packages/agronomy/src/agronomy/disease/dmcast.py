"""DMCast — downy mildew infection model. Stubbed at Stage 00."""

from __future__ import annotations


def dmcast_dsv(*_args: object, **_kwargs: object) -> float:
    """Compute the daily severity value (DSV) for *Plasmopara viticola*.

    Stage 01 will implement the Magarey-Wachtel formulation. The Stage 00 stub
    raises so a downstream caller can never silently treat zero as a real score.
    """
    raise NotImplementedError("DMCast: implemented in Stage 01")
