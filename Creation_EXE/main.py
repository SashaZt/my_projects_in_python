from PyInstaller.__main__ import run


def create_exe():
    opts = ['main.py', '--onefile']
    run(opts)


if __name__ == '__main__':
    create_exe()