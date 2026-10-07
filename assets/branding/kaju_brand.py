"""Canonical KAJU wordmark and the reference's triangular line mark."""
import re

BRAND = 'KAJU'
SPACED_BRAND = 'K A J U'
LOGO_PATHS = (
    ((0, 1), (-.85, -.55), (.85, -.55), (0, 1)),
    ((0, .75), (0, -.10), (-.70, -.45)),
    ((0, -.10), (.70, -.45)),
    ((-.50, -.38), (0, .30), (.50, -.38), (-.50, -.38)),
)


def replace_wordmark(body):
    return re.sub(r'\bK(\s*)A(\s*)Z(\s*)E\b',
                  lambda match: 'K'+match[1]+'A'+match[2]+'J'+match[3]+'U', body)


def logo_paths():
    return [list(path) for path in LOGO_PATHS]
