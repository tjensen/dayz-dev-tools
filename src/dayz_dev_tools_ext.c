#define PY_SSIZE_T_CLEAN

#include <Python.h>

static void
get_pointer(Py_ssize_t *rpos, Py_ssize_t *rlen, Py_ssize_t outlen, unsigned short raw)
{
    *rpos = outlen - ((raw & 0xff) + ((raw & 0xf000) >> 4));
    *rlen = ((raw >> 8) & 0xf) + 3;
}

static int
expand_impl(unsigned char *outb, Py_ssize_t outlen, const unsigned char *inb, Py_ssize_t inlen)
{
    Py_ssize_t outidx = 0;
    Py_ssize_t inidx = 0;
    Py_ssize_t rpos, rlen;
    Py_ssize_t cpypos, cpyend;
    int bit, cnt;
    unsigned char flagbits;

    while (inidx < inlen)
    {
        flagbits = inb[inidx++];

        for (bit = 0; (bit < 8) && (inidx < inlen) && (outidx < outlen); ++bit)
        {
            if (flagbits >> bit & 1)
            {
                outb[outidx++] = inb[inidx++];
            }
            else if (inidx < inlen - 1)
            {
                get_pointer(&rpos, &rlen, outidx, inb[inidx + 1] << 8 | inb[inidx]);
                inidx += 2;

                if (rpos < 0)
                {
                    for (cnt = 0; (cnt < rlen) && (outidx < outlen); ++outidx)
                    {
                        outb[outidx] = ' ';
                    }
                }
                else if ((rpos + rlen) > outidx)
                {
                    cpyend = outidx + rlen;
                    if (cpyend > outlen)
                    {
                        break;
                    }

                    while (outidx < cpyend)
                    {
                        for (cpypos = rpos; (cpypos < outlen) && (outidx < cpyend); ++cpypos)
                        {
                            outb[outidx++] = outb[cpypos];
                        }
                    }
                }
                else
                {
                    cpyend = Py_MIN(rlen, outlen - outidx);
                    memcpy(&outb[outidx], &outb[rpos], cpyend);
                    outidx += cpyend;
                }
            }
        }
    }

    return 0;
}

static PyObject *
dayz_dev_tools_ext_expand(PyObject *self, PyObject *args)
{
    Py_buffer outbuffer;
    Py_buffer inbuffer;

    if (!PyArg_ParseTuple(args, "w*y*", &outbuffer, &inbuffer))
    {
        return NULL;
    }

    if (expand_impl(
                (unsigned char *)outbuffer.buf, outbuffer.len,
                (unsigned const char *)inbuffer.buf, inbuffer.len))
    {
        PyErr_SetString(
                PyExc_BufferError, "Unexpectedly reached end of output buffer in PBO expand");
        return NULL;
    }

    return Py_None;
}

static PyMethodDef ExtMethods[] = {
    {"expand", dayz_dev_tools_ext_expand, METH_VARARGS, "Expand a compressed buffer"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef ext_module = {
    PyModuleDef_HEAD_INIT,
    "dayz_dev_tools_ext",
    NULL,
    -1,
    ExtMethods
};

PyMODINIT_FUNC
PyInit_dayz_dev_tools_ext(void)
{
    return PyModule_Create(&ext_module);
}
