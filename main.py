from pathlib import Path
import modpack

INPUT_FOLDER = 'input'
ROOT_FOLDER = 'root_folder'
OUTPUT_FOLDER = 'output'


if __name__ == "__main__":
    in_p = Path(INPUT_FOLDER)

    for single_mod in sorted(in_p.iterdir()):
        print("~~~~ Adding {}".format(single_mod.name))
        modpack.ModPack(single_mod)
