# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
================
desiutil.bitmask
================

Mask bits for the spectro pipeline.

Individual packages will define their own mask bits and use this as a utility
access wrapper.  Typical users will get their bitmasks pre-made from those
packages, not from here.

Stephen Bailey, Lawrence Berkeley National Lab
Fall 2015

Examples
--------

desispec_ could create a ccdmask like this:

>>> from desiutil.bitmask import BitMask
>>> import yaml
>>> _bitdefs = yaml.load('''
... ccdmask:
...     - [BAD,       0, "Pre-determined bad pixel (any reason)"]
...     - [HOT,       1, "Hot pixel"]
...     - [DEAD,      2, "Dead pixel"]
...     - [SATURATED, 3, "Saturated pixel from object"]
...     - [COSMIC,    4, "Cosmic ray"]
... ''')
...
>>> ccdmask = BitMask('ccdmask', _bitdefs)

Users would then access this mask with:

>>> from desispec.bitmasks import ccdmask
>>> ccdmask.COSMIC | ccdmask.SATURATED  #- 2**4 + 2**3
24
>>> ccdmask.mask('COSMIC')     # 2**4, same as ccdmask.COSMIC
16
>>> ccdmask.mask(4)            # 2**4, same as ccdmask.COSMIC
16
>>> ccdmask.COSMIC             # 2**4, same as ccdmask.mask('COSMIC')
16
>>> ccdmask.bitnum('COSMIC')
4
>>> ccdmask.bitname(4)
'COSMIC'
>>> ccdmask.names()
['BAD', 'HOT', 'DEAD', 'SATURATED', 'COSMIC']
>>> ccdmask.names(3)
['BAD', 'HOT']
>>> ccdmask.comment(0)
'Pre-determined bad pixel (any reason)'
>>> ccdmask.comment('COSMIC')
'Cosmic ray'


.. _desispec: http://desispec.readthedocs.org
"""


class _MaskBit(int):
    """A single mask bit.

    Subclasses int to act like an int, but allows the ability to extend with
    blat.name, blat.comment, blat.mask, blat.bitnum.

    Attributes
    ----------
    name : str
        The name of the bit.
    bitnum : int
        The number of the bit.  The value of the bit is ``2**bitnum``.
    mask : int
        The value of the bit, ``2**bitnum``.
    comment : str
        A comment explaining the meaning of the bit.
    """
    def __new__(cls, name, bitnum, comment, extra=dict()):
        self = super(_MaskBit, cls).__new__(cls, 2**bitnum)
        self.name = name
        self.bitnum = bitnum
        self.mask = 2**bitnum
        self.comment = comment
        self._extra = extra
        for key, value in extra.items():
            if hasattr(self, key):
                raise AttributeError(
                    "Bit {0} extra key '{1}' is already in use by int objects.".format(name, key))
            self.__dict__[key] = value
        return self

    def __str__(self):
        return ('{0.name:16s} bit {0.bitnum} mask 0x{0.mask:X} - ' +
                '{0.comment}').format(self)

    # def __repr__(self):
    #     return "_MaskBit(name='{0.name}', bitnum={0.bitnum:d}, comment='{0.comment}')".format(self)


#  Class to provide mask bit utility functions
class BitMask(object):
    """BitMask object to represent bit names, masks, and comments.

    Typical users are not expected to create BitMask objects directly;
    other packages like desispec and desitarget will have used this
    to pre-create the bitmasks for them using definition files in those
    packages.

    Parameters
    ----------
    name : str
        Name of this mask, must be key in `bitdefs`.
    bitdefs : dict
        Dictionary of different mask bit definitions;
        each value is a list of ``[bitname, bitnum, comment]``.
        A 4th entry is optional, which must be a dictionary.
    """

    def __init__(self, name, bitdefs):
        """Init.
        """
        self._bits = dict()
        self._name = name
        for x in bitdefs[name]:
            bitname, bitnum, comment = x[0:3]
            if len(x) == 4:
                extra = x[3]
                if not isinstance(extra, dict):
                    raise ValueError(
                        '{} extra values should be a dict'.format(bitname))
            else:
                extra = dict()
            self._bits[bitname] = _MaskBit(bitname, bitnum, comment, extra)
            self._bits[bitnum] = self._bits[bitname]

    def __getitem__(self, bitname):
        """Return mask for individual bitname.
        """
        return self._bits[bitname]

    def bitnum(self, bitname):
        """Return bit number (int) for bitname (string).
        """
        return self._bits[bitname].bitnum

    def bitname(self, bitnum):
        """Return bit name (string) for this bitnum (integer).
        """
        return self._bits[bitnum].name

    def comment(self, bitname_or_num):
        """Return comment for this bit name or bit number.
        """
        return self._bits[bitname_or_num].comment

    def mask(self, name_or_num):
        """Return mask value.

        Examples
        --------

        >>> bitmask.mask(3)         #  2**3
        8
        >>> bitmask.mask('BLAT')
        >>> bitmask.mask('BLAT|FOO')
        """
        if isinstance(name_or_num, int):
            return self._bits[name_or_num].mask
        else:
            mask = 0
            for name in name_or_num.split('|'):
                mask |= self._bits[name].mask
            return mask

    def names(self, mask=None):
        """Return list of names of masked bits.

        Parameters
        ----------
        mask : int, optional
            The mask integer to convert to names. If not supplied,
            return names of all known bits.

        Returns
        -------
        names : list
            The list of names contained in the mask.
        """
        names = list()
        if mask is None:
            # return names in sorted order of bitnum
            bitnums = [x for x in self._bits.keys() if isinstance(x, int)]
            for bitnum in sorted(bitnums):
                names.append(self._bits[bitnum].name)
        else:
            bitnum = 0
            while bitnum**2 <= mask:
                if (2**bitnum & mask):
                    if bitnum in self._bits.keys():
                        names.append(self._bits[bitnum].name)
                    else:
                        names.append('UNKNOWN' + str(bitnum))
                bitnum += 1

        return names

    def __getattr__(self, name):
        """Enable ``mask.BITNAME`` equivalent to ``mask['BITNAME']``.
        """
        if name in self._bits:
            return self._bits[name]
        else:
            raise AttributeError('Unknown mask bit name ' + name)

    def __repr__(self):
        '''Return yaml representation defining the bits of this bitmask.
        '''
        result = list()
        result.append(self._name + ':')
        # return names in sorted order of bitnum
        bitnums = [x for x in self._bits.keys() if isinstance(x, int)]
        for bitnum in sorted(bitnums):
            bit = self._bits[bitnum]
            # format the line for single bit, with or without extra keys
            line = '  - [{:16s} {:2d}, "{}"'.format(
                bit.name+',', bit.bitnum, bit.comment)
            if len(bit._extra) > 0:
                line = line + ', '+str(bit._extra)+']'
            else:
                line = line + ']'
            result.append(line)

        return "\n".join(result)
