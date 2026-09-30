from datetime import datetime
from app.logic import gen_now


def test_now():
    assert gen_now().replace('D-', '') == datetime.now().strftime('%Y/%m/%d/%H/%M/%S')
