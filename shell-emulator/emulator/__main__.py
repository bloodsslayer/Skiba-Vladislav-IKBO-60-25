import sys

from .config import parse_args
from .gui import run


def main(argv=None):
    config = parse_args(argv)
    # Отладочный вывод дублируется в терминал ОС, из которого запущен эмулятор.
    print("\n".join(config.debug_lines()))
    return run(config)


if __name__ == "__main__":
    sys.exit(main())
