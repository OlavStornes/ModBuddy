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
        for x in self.install_steps:
            for y in x.install_steps:
                for z in y.optional_file_groups:
                    for lul in z.groups:
                        new_page = QWizardPage()
                        new_layout = QGridLayout()
                        new_layout.addWidget(QLabel(lul.name), 0, 0)
                        for kek in lul.plugin_collection:
                            for i, bur in enumerate(kek.plugins):
                                target_radio = QRadioButton(bur.name)
                                new_layout.addWidget(target_radio, i+1, 0)
                                target_radio.toggled.connect(bur.update)
                                new_layout.addWidget(QTextEdit(bur.description), i+1, 1)

                                if bur.image:
                                    parsed_img = self.mod_folder / bur.image.replace('\\', '/')
                                    img = QPixmap(parsed_img)
                                
                                    test = QLabel()
                                    test.setPixmap(img)
                                    new_layout.addWidget(test, i+1, 2)
                            new_page.setTitle(y.name)
                            new_page.setLayout(new_layout)
                            self.ui.addPage(new_page)

    def handle_results(self):
        print("hanlding results")
        for x in self.install_steps:
            for xx in x.install_steps:
                for y in xx.optional_file_groups:
                    for yy in y.groups:
                        for z in yy.plugin_collection:
                            for zz in z.plugins:
                                if zz.enabled:
                                    for mod in zz.files_collection:
                                        print(zz.enabled, yy.name)
                                        for folder in mod.folders:
                                            testpath = Path(sys.argv[1])
                                            testpath = testpath / str(folder.source)
                                            print(testpath.absolute(), testpath.exists())



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


if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)

    payload = sys.argv[1]
    parser = FomodParser(Path(payload))
    parser.ui.show()
    app.exec()

    parser.handle_results()

