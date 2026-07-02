import runpy
import sys

DEFAULT_ARGS = [
    '--cov=src',
    '--cov-report=term-missing:skip-covered',
    '--cov-report=html',
]


def main():
    if len(sys.argv) == 1:
        sys.argv.extend(DEFAULT_ARGS)
    runpy.run_module('pytest', run_name='__main__', alter_sys=True)


if __name__ == '__main__':
    main()
