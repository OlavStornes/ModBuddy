from pathlib import Path
import sys
from xml.etree import ElementTree
from PySide6.QtWidgets import QLabel, QRadioButton, QApplication
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel,QRadioButton, QGridLayout, QWizard, QWizardPage, QTextEdit

class FomodParser:
    def __init__(self, mod_folder:Path):
        self.mod_folder = mod_folder
        self.fomod_file = Path(mod_folder) / 'fomod/ModuleConfig.xml'

        xml = ElementTree.parse(self.fomod_file).getroot()
        
        self.module_name = xml.findtext("./moduleName")
        self.install_steps = [InstallSteps(x) for x in xml.findall("./installSteps")]

        self.build_ui()
        
    def build_ui(self):
        self.ui = QWizard()
        for install_steps_collection in self.install_steps:
            for install_step in install_steps_collection.install_steps:
                for optional_file_group in install_step.optional_file_groups:
                    for group in optional_file_group.groups:
                        new_page = QWizardPage()
                        new_layout = QGridLayout()
                        new_layout.addWidget(QLabel(group.name), 0, 0)
                        for plugin_collection in group.plugin_collection:
                            for i, plugin in enumerate(plugin_collection.plugins):
                                target_radio = QRadioButton(plugin.name)
                                new_layout.addWidget(target_radio, i+1, 0)
                                target_radio.toggled.connect(plugin.update)
                                new_layout.addWidget(QTextEdit(plugin.description), i+1, 1)

                                if plugin.image:
                                    parsed_img = self.mod_folder / plugin.image.replace('\\', '/')
                                    img = QPixmap(parsed_img)
                                
                                    test = QLabel()
                                    test.setPixmap(img)
                                    new_layout.addWidget(test, i+1, 2)
                            new_page.setTitle(install_step.name)
                            new_page.setLayout(new_layout)
                            self.ui.addPage(new_page)

        final_page = QWizardPage()
        self.finished = self.ui.button(QWizard.FinishButton)
        final_page.setFinalPage(True)
        self.ui.addPage(final_page)

    def handle_results(self) -> dict:
        tmp = {}
        print("hanlding results")
        for install_steps_collection in self.install_steps:
            for i, install_step in enumerate(install_steps_collection.install_steps):
                for optional_file_group in install_step.optional_file_groups:
                    for group in optional_file_group.groups:
                        for plugins_collection in group.plugin_collection:
                            for plugin in plugins_collection.plugins:
                                if plugin.enabled:
                                    for files in plugin.files_collection:
                                        print(plugin.enabled, group.name)
                                        for folder in files.folders:
                                            tmp[f"{str(i)}{group.name}"] = folder.to_dict()
        return tmp

class InstallSteps:
    def __init__(self, xml: ElementTree.Element):
        self.order = xml.get("order")
        
        self.install_steps = [InstallStep(x) for x in xml.findall("./installStep")]


class InstallStep:
    def __init__(self, xml:ElementTree.Element):
        self.name = xml.get("name")
        self.optional_file_groups = [OptionalFileGroups(x) for x in xml.findall("./optionalFileGroups")]


class OptionalFileGroups:
    def __init__(self, xml:ElementTree.Element):
        self.order = xml.get("order")
        self.groups = [Group(x) for x in xml.findall("./group")]

class Group:
    def __init__(self, xml:ElementTree.Element):
        self.name = xml.get("name")
        self.type = xml.get("type")
        self.plugin_collection = [Plugins(x) for x in xml.findall("./plugins")]

class Plugins:
    def __init__(self, xml:ElementTree.Element):
        self.name = xml.get("name")
        self.description = xml.findtext("description")
        self.plugins = [Plugin(x) for x in xml.findall("./plugin")]

class Plugin:
    def __init__(self, xml:ElementTree.Element):
        self.name = xml.get("name")
        self.description = xml.findtext("description")
        self.flags = [x.get("name") for x in xml.findall("./conditionFlags/flag")]
        self.enabled = False
        
        try:
            self.image = xml.find("./image").get('path')
        except AttributeError:
            self.image = None

        self.files_collection = [Files(x) for x in xml.findall("./files")]

    def update(self, arg):
        self.enabled = arg


class Files:
    def __init__(self, xml:ElementTree.Element):
        self.folders = [Folder(x) for x in xml.findall("./folder")]

class Folder:
    def __init__(self, xml:ElementTree.Element):
        self.source = xml.get("source")
        self.destination = xml.get("destination")
        self.priority = xml.get("priority")

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "destination": self.destination,
            "priority": self.priority
        }


if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)

    payload = sys.argv[1]
    parser = FomodParser(Path(payload))
    parser.ui.show()
    app.exec()

    parser.handle_results()

