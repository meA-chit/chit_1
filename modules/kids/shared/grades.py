"""German-style averages (scale 1 best to 6). Pure functions.

A subject has two graded types, written exam and oral / short test. Each type is averaged on its own, then the two are
combined with the household's weights for the subject type (core, minor or elective). A subject with only one type uses it alone.
"""
from __future__ import annotations


def mean(values):
    return sum(values) / len(values) if values else None


def subject_average(kind, grades, weights):
    written = mean([g["grade"] for g in grades if g["grade_type"] == "written"])
    oral = mean([g["grade"] for g in grades if g["grade_type"] == "oral"])
    pct = weights["%s_written_pct" % kind]
    if written is not None and oral is not None:
        average = (written * pct + oral * (100 - pct)) / 100
    else:
        average = written if written is not None else oral
    return {"written": _r(written), "oral": _r(oral), "average": _r(average)}


def trend(grades):
    """'better' / 'worse' / 'steady' from the two latest grades against the earlier ones; None below three grades."""
    ordered = [g["grade"] for g in sorted(grades, key=lambda g: g["given_on"])]
    if len(ordered) < 3:
        return None
    recent, earlier = mean(ordered[-2:]), mean(ordered[:-2])
    if recent <= earlier - 0.25:
        return "better"
    return "worse" if recent >= earlier + 0.25 else "steady"


def _r(value):
    return None if value is None else round(value, 2)
