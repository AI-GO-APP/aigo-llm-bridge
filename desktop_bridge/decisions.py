"""Derive consistent System One answers from validated model probability estimates."""
import math

from .decision_contract import strict_loads
from .errors import BridgeError
from .execution_budget import check


def typed_output(value, question):
    """Validate only our two generated structures, never arbitrary JSON Schema."""
    field = 'noul' if question['type'] == 'noul' else 'probabilities'
    if not isinstance(value, dict) or set(value) != {field}:
        raise ValueError()
    probabilities = [value[field]] if field == 'noul' else value[field]
    if not isinstance(probabilities, list): raise ValueError()
    expected = 1 if field == 'noul' else len(question['criteria'])
    if len(probabilities) != expected: raise ValueError()
    for p in probabilities:
        if type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1:
            raise ValueError()


def bounded_loads(text):
    if not isinstance(text,str) or len(text.encode('utf-8'))>1_000_000:raise ValueError()
    # Generated outputs need at most two levels; reject deeply nested junk before
    # handing it to the JSON parser. Braces inside strings do not count.
    depth=0;quoted=False;escaped=False
    for ch in text:
        if quoted:
            if escaped:escaped=False
            elif ch=='\\':escaped=True
            elif ch=='"':quoted=False
        elif ch=='"':quoted=True
        elif ch in '[{':
            depth+=1
            if depth>4:raise ValueError()
        elif ch in ']}':depth-=1
    return strict_loads(text)


def answer(text, question, schema, cancel=None):
    try:
        check()
        if cancel is not None and cancel.is_set():
            raise BridgeError(499, 'cancelled', '請求已取消。')
        value = bounded_loads(text)
        typed_output(value, question)
        check()
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
