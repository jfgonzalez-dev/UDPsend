from app.logic import gen_rep

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


def test_rep_in_order():
    assert gen_rep(timetable1).startswith('T030-045-060') and len(gen_rep(timetable1)) == 84


def test_rep_not_order():
    assert gen_rep(timetable2).startswith('T060-030-045') and len(gen_rep(timetable2)) == 84
