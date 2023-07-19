import sys
import os
import shutil

def main(path: str) -> None:
    start = os.getcwd()
    os.chdir(path)
    os.system("asar extract ./app.asar ./data/")
    shutil.copyfile(f'{start}\\plugins\\skip_song\\back.js', './data/plugins/skip_song/back.js')
    try:
        os.remove("./app.asar")
    except FileNotFoundError:
        pass
    os.system("asar pack .\data\ .\\app.asar")

if __name__ == "__main__":
    main(sys.argv[1])