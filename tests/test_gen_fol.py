from app.logic import gen_fol


def test_single_digit():
    assert gen_fol("1") == "F01"


def test_double_digit():
    assert gen_fol("10") == "F10"
