from Code.Common.project_utils import ProjectUtils
import xml.etree.cElementTree as elementTree
class FindingsChecker:
    def __init__(self, path:str):
        file = ProjectUtils.read_file(path)
        self.phase = ""
        self.error = False
        try:
            self.root = elementTree.fromstring(file)
        except Exception as e:
            self.error = True
            print(e)
            print("Error parsing XML:")
            print(file)


    def check_catastrophic(self) -> bool:
        if self.error:
            return True
        for finding in self.root.findall("Finding"):
            severity = finding.find("Severity")
            if severity is None:
                self.phase = finding.find("RollbackPhase").text
                return False
            if severity.text == "Catastrophic":
                return True
        return False

    def get_phase(self) -> str:
         return self.phase