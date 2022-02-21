from pathlib import PosixPath
import sys
from xml.etree import ElementTree


class FomodParser:
    def __init__(self, xml_path:PosixPath|str):
        xml = ElementTree.parse(xml_path).getroot()
        
        self.module_name = xml.findtext("./moduleName")
        print(self.module_name)
        self.install_steps = [InstallSteps(x) for x in xml.findall("./installSteps")]

class InstallSteps:
    def __init__(self, xml: ElementTree.Element):
        self.order = xml.get("order")
        print(self.order)
        
        self.install_steps = [InstallStep(x) for x in xml.findall("./installStep")]


class InstallStep:
    def __init__(self, xml:ElementTree.Element):
        self.name = xml.get("name")
        self.optional_file_groups = [OptionalFileGroups(x) for x in xml.findall("./optionalFileGroups")]
        print("install" + str(self.name))


class OptionalFileGroups:
    def __init__(self, xml:ElementTree.Element):
        self.order = xml.get("order")
        print(self.order)
        self.groups = [Group(x) for x in xml.findall("./group")]

class Group:
    def __init__(self, xml:ElementTree.Element):
        self.name = xml.get("name")
        self.type = xml.get("type")
        print(self.name)
        self.plugin_collection = [Plugins(x) for x in xml.findall("./plugins")]

class Plugins:
    def __init__(self, xml:ElementTree.Element):
        self.name = xml.get("name")
        self.description = xml.findtext("description")
        print(self.name, self.description)
        self.plugins = [Plugin(x) for x in xml.findall("./plugin")]

class Plugin:
    def __init__(self, xml:ElementTree.Element):
        self.name = xml.get("name")
        self.description = xml.findtext("description")
        self.flags = [x.get("name") for x in xml.findall("./conditionFlags/flag")]
        
        try:
            self.image = xml.find("./image").get('path')
        except AttributeError:
            self.image = None
        print("Plugin:")
        print(self.name)
        print(self.image)
        print(self.flags)

        self.files_collection = [Files(x) for x in xml.findall("./files")]

class Files:
    def __init__(self, xml:ElementTree.Element):
        self.folders = [Folder(x) for x in xml.findall("./folder")]

class Folder:
    def __init__(self, xml:ElementTree.Element):
        self.source = xml.get("source")
        self.destination = xml.get("destination")
        self.priority = xml.get("priority")

        print(self.source)
        


if __name__ == "__main__":
    payload = sys.argv[1]
    parser = FomodParser(payload)

    print(parser)
