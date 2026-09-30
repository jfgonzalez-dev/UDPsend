from app.logic import gen_vol

timetable1 = [
        {'time': '09:30', 'rep': '30', 'vol': '15'},
        {'time': '10:30', 'rep': '45', 'vol': '10'},
        {'time': '11:30', 'rep': '60', 'vol': '5'}
    ]

timetable2 = [
        {'time': '10:30', 'rep': '30', 'vol': '15'},
        {'time': '11:30', 'rep': '45', 'vol': '10'},
        {'time': '09:30', 'rep': '60', 'vol': '5'}
    ]


def test_vol_in_order():
    assert gen_vol(timetable1).startswith('V15-10-05') and len(gen_vol(timetable1)) == 63


def test_vol_not_order():
    assert gen_vol(timetable2).startswith('V05-15-10') and len(gen_vol(timetable1)) == 63

