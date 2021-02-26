from pathlib import Path
import json
import modpack

INPUT_FOLDER = 'input'
SETTINGS_NAME = 'settings.json'
ROOT_FOLDER_NAME = 'root_folder'
OUTPUT_FOLDER = Path('output') / ROOT_FOLDER_NAME


if __name__ == "__main__":
    in_p = Path(INPUT_FOLDER)
    settings = json.loads(Path(SETTINGS_NAME).read_text())
    print(settings)
    for single_mod in settings:
        print("~~~~ Adding {}".format(single_mod.get('name')))
        target_folder = in_p / single_mod.get('folder_name') / single_mod.get('subfolder')
        modpack.ModPack(target_folder, OUTPUT_FOLDER)
