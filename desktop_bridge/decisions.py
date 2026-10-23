"""Derive consistent System One answers from validated model probability estimates."""
import math

from .decision_contract import strict_loads
from .errors import BridgeError
from .schema_guard import validate_instances


def answer(text, question, schema, cancel=None):
    try:
        value = strict_loads(text)
        if not validate_instances([[schema,value]],cancel):raise ValueError()
        if question["type"] == "noul":
            p = value["noul"]
            if isinstance(p, bool) or not math.isfinite(p): raise ValueError()
            return {"type": "noul", "noul": p}
        p = value["probabilities"]
        if any(isinstance(v, bool) or not math.isfinite(v) for v in p): raise ValueError()
        total = sum(p)
        if abs(total-1) > 1e-6: raise ValueError()
        p = [v/total for v in p]  # Only absorb the validated floating-point tolerance.
        mode = p.index(max(p))  # Stable tie: first original criterion.
        n = len(p)
        if question["type"] == "choice":
            labels = list(question["criteria"])
            confidence = (max(p)-1/n)/(1-1/n) if n > 1 else 1.
            return {"type": "choice", "choice": labels[mode],
                    "probabilities": {k: round(v,12) for k,v in zip(labels,p)}, "confidence": round(confidence,12)}
        spread = sum(v*abs(i-mode) for i,v in enumerate(p))
        uniform_spread = sum(abs(i-(n-1)/2) for i in range(n))/n
        return {"type": "score", "score": round(sum(i*v for i,v in enumerate(p)),12),
                "legend": {str(i): v for i,v in enumerate(question["criteria"])},
                "probabilities": {str(i): round(v,12) for i,v in enumerate(p)},
                "confidence": round(max(0.,1-spread/uniform_spread),12)}
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        raise BridgeError(502, "invalid_structured_output", "模型輸出不符合 Decisions 題型與機率分布。") from None
