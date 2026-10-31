"""Build the smallest useful face, a colour background with the default layout:
    python examples/minimal_face.py my-face.tbwf
Then import my-face.tbwf from Hello Haylou's Editor tab.
"""

import sys

from PIL import Image

from haylou_tools.tbwf import DIAL_SIZE, default_spec, write_face

BACKGROUND = (0x12, 0x2B, 0x4A)


def main() -> None:
    write_face(sys.argv[1], default_spec(), Image.new("RGB", (DIAL_SIZE, DIAL_SIZE), BACKGROUND))


if __name__ == "__main__":
    main()
