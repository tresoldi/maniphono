# maniphono

[![Build Status](https://travis-ci.org/tresoldi/maniphono.svg?branch=main)](https://travis-ci.org/tresoldi/maniphono)
[![codecov](https://codecov.io/gh/tresoldi/maniphono/branch/main/graph/badge.svg)](https://codecov.io/gh/tresoldi/maniphono)

Python library for the symbolic manipulation of phoneme representations

## Installation

In any standard Python environment, `maniphono` can be installed with:

```bash
$ pip install maniphono
```

## Example usage

```python
>>> import maniphono
>>> snd1 = maniphono.Sound(maniphono.IPA, "p")
>>> snd1
voiceless bilabial plosive consonant
>>> str(snd1)
'p'
>>> snd2 = snd1 + "voiced,alveolar"
>>> str(snd2)
'd'
```

## TODO

  - Consider expanding checks in `model.parse_constraints()` to evaluate non-shallow
    constraints (from different layers); this is not such a problem for the data as it
    is, because graphemes will be rejected if necessary, but it would be nice to
    have such a check in the function (it involves building a tree of contraints,
    which is interesting and potentially useful in itself)
  - Consider adding option in `model.py` to Unicode-normalize graphemes

## What is new

Version 0.2:
  - Added support for disjunction in constraints
  - Renamed default model to MIPA ("Modified IPA"), expanded in number of sounds
    hard-coded and constraints to features and values
  - Added a `.values2sound()` method, modelled after `distfeat`'s
    `features2graphemes()` function.
