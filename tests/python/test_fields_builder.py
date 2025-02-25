import pytest
from taichi.lang.exception import InvalidOperationError

import taichi as ti


@ti.test(arch=[ti.cpu, ti.cuda, ti.vulkan, ti.metal])
def test_fields_with_shape():
    n = 5
    x = ti.field(ti.f32, [n])

    @ti.kernel
    def func():
        for i in range(n):
            x[i] = i

    func()

    for i in range(n):
        assert x[i] == i

    y = ti.field(ti.f32, [n])

    @ti.kernel
    def func2():
        for i in range(n):
            y[i] = i * 2
        for i in range(n):
            x[i] = i * 3

    func2()

    for i in range(n):
        assert x[i] == i * 3
        assert y[i] == i * 2

    func()

    for i in range(n):
        assert x[i] == i


@ti.test(arch=[ti.cpu, ti.cuda, ti.vulkan, ti.metal])
def test_fields_builder_dense():
    n = 5

    fb1 = ti.FieldsBuilder()
    x = ti.field(ti.f32)
    fb1.dense(ti.i, n).place(x)
    fb1.finalize()

    @ti.kernel
    def func1():
        for i in range(n):
            x[i] = i * 3

    func1()
    for i in range(n):
        assert x[i] == i * 3

    fb2 = ti.FieldsBuilder()
    y = ti.field(ti.f32)
    fb2.dense(ti.i, n).place(y)
    z = ti.field(ti.f32)
    fb2.dense(ti.i, n).place(z)
    fb2.finalize()

    @ti.kernel
    def func2():
        for i in range(n):
            x[i] = i * 2
        for i in range(n):
            y[i] = i + 5
        for i in range(n):
            z[i] = i + 10

    func2()
    for i in range(n):
        assert x[i] == i * 2
        assert y[i] == i + 5
        assert z[i] == i + 10

    func1()
    for i in range(n):
        assert x[i] == i * 3


@ti.test(arch=[ti.cpu, ti.cuda, ti.metal])
def test_fields_builder_pointer():
    n = 5

    fb1 = ti.FieldsBuilder()
    x = ti.field(ti.f32)
    fb1.pointer(ti.i, n).place(x)
    fb1.finalize()

    @ti.kernel
    def func1():
        for i in range(n):
            x[i] = i * 3

    func1()
    for i in range(n):
        assert x[i] == i * 3

    fb2 = ti.FieldsBuilder()
    y = ti.field(ti.f32)
    fb2.pointer(ti.i, n).place(y)
    z = ti.field(ti.f32)
    fb2.pointer(ti.i, n).place(z)
    fb2.finalize()

    # test range-for
    @ti.kernel
    def func2():
        for i in range(n):
            x[i] = i * 2
        for i in range(n):
            y[i] = i + 5
        for i in range(n):
            z[i] = i + 10

    func2()
    for i in range(n):
        assert x[i] == i * 2
        assert y[i] == i + 5
        assert z[i] == i + 10

    # test struct-for
    @ti.kernel
    def func3():
        for i in y:
            y[i] += 5
        for i in z:
            z[i] -= 5

    func3()
    for i in range(n):
        assert y[i] == i + 10
        assert z[i] == i + 5

    func1()
    for i in range(n):
        assert x[i] == i * 3


@ti.test(arch=[ti.cpu, ti.cuda, ti.vulkan])
def test_fields_builder_destroy():
    def A(i):
        n = i * 10**3
        fb = ti.FieldsBuilder()
        a = ti.field(ti.f64)
        fb.dense(ti.i, n).place(a)
        c = fb.finalize()
        c.destroy()

    def B(i):
        n = i * 10**3
        fb = ti.FieldsBuilder()
        a = ti.field(ti.f64)
        fb.dense(ti.i, n).place(a)
        c = fb.finalize()

        ni = i * 10**3
        fbi = ti.FieldsBuilder()
        ai = ti.field(ti.f64)
        fbi.dense(ti.i, n).place(ai)
        ci = fbi.finalize()

        c.destroy()
        ci.destroy()

    for i in range(5):
        A(5)
    B(2)
    A(4)


@ti.test(arch=[ti.cpu, ti.cuda])
def test_fields_builder_exceeds_max():
    sz = 4

    def create_fb():
        fb = ti.FieldsBuilder()
        x = ti.field(ti.f32)
        fb.dense(ti.ij, (sz, sz)).place(x)
        fb.finalize()

    # kMaxNumSnodeTreesLlvm=32 in taichi/inc/constants.h
    for _ in range(32):
        create_fb()

    with pytest.raises(RuntimeError) as e:
        create_fb()
    assert 'LLVM backend supports up to 32 snode trees' in e.value.args[0]
