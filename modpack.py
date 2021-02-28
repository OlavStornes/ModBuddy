from pathlib import Path


class ModPack():
    def __init__(self, mod_folder: Path, destination_folder: Path):
        self.modname = mod_folder.name
        self.mod_folder = mod_folder
        self.out_p = destination_folder

    def convert_from_input_to_output(self, in_path: Path):
        abs_input = str(in_path.resolve())
        x = abs_input.replace(str(self.mod_folder.resolve()), '').lstrip('/')
        output = self.out_p.joinpath(x)
        return output

    def handle_symlinking(self, file_path: Path):
        target_path = self.convert_from_input_to_output(file_path)
        if target_path.exists():
            print("DELETE {}".format(target_path))
            target_path.unlink()
        print("{} --> {}".format(file_path.resolve(), target_path.resolve()))
        file_path.link_to(target_path)

    def create_folder(self, folder_path: Path):
        print(folder_path)
        output_path = self.convert_from_input_to_output(folder_path)
        print("FOLDER AT {}".format(output_path.resolve()))
        output_path.mkdir(exist_ok=True)

    def add_mod(self):
        for input_path in self.mod_folder.glob('**/*'):
            if input_path.is_dir():
                self.create_folder(input_path)
                continue
            self.handle_symlinking(input_path)


def initialize_configs(config_payload: dict, input_folder: Path, output_folder: Path):
    for single_mod in config_payload:
        if single_mod.get('enabled'):
            target_folder = input_folder / single_mod.get('path')
            x = ModPack(target_folder, output_folder)
            x.add_mod()
