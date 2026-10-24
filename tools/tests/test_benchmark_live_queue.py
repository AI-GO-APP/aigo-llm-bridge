import math

from tools.benchmark_live_queue import valid_answer


def test_live_probability_checks_contract_without_claiming_model_calibration():
    for p in (0, .1, .9, 1):
        assert valid_answer({'answers': {'q': {'type': 'noul', 'noul': p}}}, True)
    for p in (True, -.1, 1.1, math.nan, math.inf, '0.9', None):
        assert not valid_answer({'answers': {'q': {'type': 'noul', 'noul': p}}}, True)
    assert not valid_answer({'answers': {'q': {'type': 'noul', 'noul': .9, 'extra': 1}}}, True)
    assert not valid_answer({'answers': {'q': {'type': 'choice', 'noul': .9}}}, True)
    assert not valid_answer({'answers': {'q': {'type': 'noul', 'noul': .9}, 'other': {}}}, True)
    assert valid_answer({'choices': [{'message': {'content': 'OK'}}]}, False)
    assert not valid_answer({'choices': [{'message': {'content': 'wrong'}}]}, False)
