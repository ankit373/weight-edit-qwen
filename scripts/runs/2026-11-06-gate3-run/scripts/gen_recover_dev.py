"""run gate3-scripts generate.py unchanged, except the ReCoVeR steering directions are moved to
the model device once per prompt (recover.Steerer.set), instead of a cpu->mps copy inside the
hook at every layer and token (recover.py:102). speed only; outputs checked against the
unpatched run in the README.
usage: gen_recover_dev.py <generate.py args>
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "2026-11-06-gate3-scripts", "scripts")))
import generate  # noqa: E402
import recover  # noqa: E402

_set = recover.Steerer.set


def set_on_device(self, dirs):
    _set(self, dirs.to(self.layers[0].mlp.down_proj.weight.device))


recover.Steerer.set = set_on_device
sys.argv = [generate.__file__] + sys.argv[1:]
generate.main()
