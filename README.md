# maniphono

![Python package](https://github.com/tresoldi/maniphono/workflows/Python%20package/badge.svg)

Python library for the symbolic manipulation of phoneme representations

## Installation

In any standard Python environment, `maniphono` can be installed with:

```bash
$ pip install maniphono
```

## Example usage

```python
>>> import maniphono
>>> snd1 = maniphono.Sound("p")
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
  - Added a `.values2sounds()` method, modelled after `distfeat`'s
    `features2graphemes()` function.
  - Added a `.minimal_matrix()` method, modelled after `distfeat`'s
    `minimal_matrix()` function.
  - Added a `.class_features()` method, modelled after `distfeat`'s
    `class_features()` function.
  - Added a general distance method, modelled after `distfeat`'s one,
    including local cache of the regressor
