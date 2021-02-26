from pathlib import Path
import json
import modpack

INPUT_FOLDER = 'input'
ROOT_FOLDER_NAME = 'root_folder'
OUTPUT_FOLDER = Path('output') / ROOT_FOLDER_NAME


if __name__ == "__main__":
    in_p = Path(INPUT_FOLDER)
    settings_path = in_p / 'settings.json'
    test = json.loads(settings_path.read_text())
    print(test)
    for single_mod in test:
        print("~~~~ Adding {}".format(single_mod.get('name')))
        target_folder = in_p / single_mod.get('folder_name')
        modpack.ModPack(target_folder, OUTPUT_FOLDER)
