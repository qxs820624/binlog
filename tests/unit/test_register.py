from random import shuffle, randint, sample

from hypothesis import given
from hypothesis import strategies as st
import pytest

from binlog import register
from binlog.binlog import Record


#
# Register
#
def test_Register_exists():
    """The Register exists."""
    assert hasattr(register, 'Register')

#
# Register().reg
#
def test_Register_None_reg_makes_empty_reg():
    """
    If `reg` argument is not passed into Register, then the `reg`
    attribute must be an empty dictionary.
    """

    r = register.Register()

    assert r.reg == {}


def test_Register_reg_is_a_copy():
    """The attribute Register.reg must be a copy of the `reg` parameter."""

    original = {1: [(1, 20), (30, 30)],
                2: [(2, 2)]}
    r = register.Register(original)

    assert r.reg == original
    assert r.reg is not original


#
# Register().add
#
def test_Register_add():
    """The Register has the add method."""
    assert hasattr(register.Register, 'add')


def test_Register_add_must_be_Record():
    """The Register has the add only accepts Record objects."""
    r = register.Register()
    with pytest.raises(ValueError):
        r.add(None)


@given(data=st.tuples(st.integers(), st.integers(), st.text()))
def test_Register_add_on_empty(data):
    """
    When the add method is called on an empty Register, the `reg`
    attribute must have the same data as the record.

    """
    original = Record(*data)
    r = register.Register()
    r.add(original)

    assert original.liidx in r.reg
    assert [(original.clidx, original.clidx)] == r.reg[original.liidx]


@given(data=st.tuples(st.integers(min_value=2), st.integers(), st.text()))
def test_Register_add_but_different_liidx(data):
    """
    When the add method is called on a non empty Register. Then, the
    `reg` attribute must have the new `liidx` if the previous Record
    added have a different `liidx`.

    """
    r = register.Register()
    r.add(Record(liidx=1, clidx=1, value='value'))

    original = Record(*data)
    r.add(original)

    assert original.liidx in r.reg
    assert [(original.clidx, original.clidx)] == r.reg[original.liidx]


@given(clidx=st.integers(min_value=10))
def test_Register_add_same_liidx_non_consecutive_clidx(clidx):
    """
    When the add method is called on a non empty Register. Then, the key
    liidx on the `reg` attribute must have the new clidx appended in a
    tuple with this shape (clidx, clidx).

    """
    r = register.Register()
    r.add(Record(liidx=1, clidx=2, value='first'))
    r.add(Record(liidx=1, clidx=clidx, value='second'))

    assert (2, 2) in r.reg[1]
    assert (clidx, clidx) in r.reg[1]


@given(clidx=st.integers())
def test_Register_add_same_liidx_and_consecutive_clidx_upperbound(clidx):
    """
    If in the llidx key of the `reg` attribute exists a tuple which
    right value is the previous value of this clidx. Then, this tuple
    must be replaced with one in which the right value must be this
    clidx. Ex::

    Register.reg[1] = [(1, 4)]

    liidx = 1
    clidx = 5
    Register.add(Record(liidx, clidx, 'something'))
    Register.reg[1] = [(1, 5)]

    """
    r = register.Register()
    r.add(Record(liidx=1, clidx=clidx, value='first'))
    r.add(Record(liidx=1, clidx=clidx+1, value='second'))

    assert [(clidx, clidx+1)] == r.reg[1]


@given(clidx=st.integers())
def test_Register_add_same_liidx_and_consecutive_clidx_lowerbound(clidx):
    """
    If in the llidx key of the `reg` attribute exists a tuple which
    left value is the next value of this clidx. Then, this tuple
    must be replaced with one in which the left value must be this
    clidx. Ex::

    Register.reg[1] = [(4, 9)]

    liidx = 1
    clidx = 3
    Register.add(Record(liidx, clidx, 'something'))
    Register.reg[1] = [(3, 9)]

    """
    r = register.Register()
    r.add(Record(liidx=1, clidx=clidx, value='first'))
    r.add(Record(liidx=1, clidx=clidx-1, value='second'))

    assert [(clidx-1, clidx)] == r.reg[1]


@given(clidx=st.integers())
def test_Register_add_same_liidx_and_consecutive_clidx_lowerbound_and_upperbound(clidx):
    """

    If in the llidx key of the `reg` attribute exists a tuple which
    right value is the previous value of this clidx, and also exists
    other tuple which left value is the next value of the clidx. Then,
    those tuples must be merged in one in which left value must belong
    to the first tuple and the right value to the second one. Ex::

    Register.reg[1] = [(1, 3), (5, 9)]

    liidx = 1
    clidx = 4
    Register.add(Record(liidx, clidx, 'something'))
    Register.reg[1] = [(1, 9)]

    """
    r = register.Register()
    r.add(Record(liidx=1, clidx=clidx-1, value='first'))
    r.add(Record(liidx=1, clidx=clidx+1, value='second'))
    r.add(Record(liidx=1, clidx=clidx, value='second'))

    assert [(clidx-1, clidx+1)] == r.reg[1]


@given(clidx=st.integers(min_value=-50, max_value=50))
def test_Register_add_same_liidx_inside_existing_range(clidx):
    """
    If the clidx was added before, just ignore it.

    """
    r = register.Register()
    for i in range(-50, 51):
        r.add(Record(liidx=1, clidx=i, value='first'))

    r.add(Record(liidx=1, clidx=clidx, value='second'))

    assert [(-50, 50)] == r.reg[1]


@given(clidx=st.integers(min_value=-100, max_value=100))
def test_Register_add_randomized_range(clidx):
    """
    """
    r = register.Register()

    l = list(range(clidx, clidx+101)) * randint(1, 3)
    shuffle(l)
    for i in l:
        r.add(Record(liidx=1, clidx=i, value='data'))

    assert [(clidx, clidx+100)] == r.reg[1]


@given(clidx=st.integers(min_value=-100, max_value=100))
def test_Register_reg_is_always_sorted(clidx):
    """
    """
    r = register.Register()

    l = list(range(clidx, clidx+101)) * randint(1, 3)
    shuffle(l)
    for i in l:
        r.add(Record(liidx=1, clidx=i, value='data'))
        assert sorted(r.reg[1]) == r.reg[1]


#
# Register().next_li
#
def test_Register_next_li():
    """The Register has the next_li method."""
    assert hasattr(register.Register, 'next_li')

def test_Register_next_li_iteration():
    """The method next_li must iterate the liidx value and reset clidx to 1."""
    r = register.Register()

    for i in range(2, 101):
        for x in range(randint(1, 10)):
            r.next_cl()
        record = r.next_li()

        assert record.liidx == i
        assert record.clidx == 1


#
# Register().next_ci
#
def test_Register_next_cl():
    """The Register has the next_li method."""
    assert hasattr(register.Register, 'next_cl')


def test_Register_next_cl_iteration():
    """The method next_cl must iterate the clidx value."""
    r = register.Register()

    for i in range(1, 101):
        record = r.next_cl()

        assert record.clidx == i
        assert record.liidx == 1


#
# Register().reset
#
def test_Register_reset():
    """The Register has the reset method."""
    assert hasattr(register.Register, 'reset')


def test_Register_reset_do_reset():
    """Register.reset resets liidx & clidx."""
    r = register.Register()
    for i in range(100):
        if randint(0, 1): r.next_li()
        if randint(0, 1): r.next_cl()

    r.reset()
    assert r.liidx == 0
    assert r.clidx == 0


#
# Register().next
#
def test_Register_next():
    """The Register has the next method."""
    assert hasattr(register.Register, 'next')


def test_Register_next_on_empty_reg_cl():
    """next method when called behave like next_cl."""
    r = register.Register()
    o = register.Register()
    for i in range(100):
        r.next()
        o.next_cl()
        assert r.liidx == o.liidx
        assert r.clidx == o.clidx


def test_Register_next_on_empty_reg_li():
    """next method when called whith log=True behave like next_li."""
    r = register.Register()
    o = register.Register()
    for i in range(100):
        r.next(log=True)
        o.next_li()
        assert r.liidx == o.liidx
        assert r.clidx == o.clidx


@given(num=st.integers(min_value=1, max_value=100))
def test_Register_next_on_populated_reg(num):
    """
    When next(log=False) is called in a populated reg it will skip the
    values in reg.
    """
    numbers = list(range(1, 101))
    s = sample(numbers, num)

    r = register.Register()
    for n in s:
        r.add(Record(liidx=1, clidx=n, value='data'))

    x = []
    for _ in range(100 - num):
        n = r.next()
        x.append(n.clidx)
        
    assert sorted(x + s) == numbers 


@given(num=st.integers(min_value=1, max_value=10000))
def test_Register_next_on_populated_reg_multiple_logindex(num):
    """
    When next(log=False) is called in a populated reg it will skip the
    values in reg. Also if next(log=True) is called it will return the
    next's li value not in reg.
    """
    numbers = [] 
    for li in range(1, 101):
        for cl in range(1, 101):
            numbers.append((li, cl))

    s = sample(numbers, num)

    r = register.Register()
    for li, cl in s:
        r.add(Record(liidx=li, clidx=cl, value='data'))

    x = []
    for i in range(10000 - num):
        n = r.next()
        while n.clidx > 100:
            n = r.next(log=True)
        x.append((n.liidx, n.clidx))

    expected = []
    for i in range(1, 101):
        for n in range(1, 101):
            expected.append((i, n))

    assert sorted(x + s) == expected

#
# Register can start on an arbitrary logindex
#
def test_Register_starts_arbitrary_index():
    r = register.Register(liidx=3)
    assert r.liidx == 3
    rec = r.next()
    assert rec.liidx == 3
    assert rec.clidx == 1
