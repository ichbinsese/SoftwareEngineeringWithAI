import xml.etree.cElementTree as elementTree
import os
from Code.Common.project_utils import ProjectUtils
from html import unescape

class CodeExtractor:
    def __init__(self,path):
        file = ""
        with open(path,"r") as f:
            file = f.read()
        self.phase = ""
        self.error = False
        try:
            self.root = elementTree.fromstring(file)
        except Exception as e:
            self.error = True
            print(e)
            print("Error parsing XML:")
            print(file)

    def create_file(self,path):
        code = self.root.find("Code")
        short_path = path.replace("Implementation/Micromouse/","")
        for codeFile in code.findall("CodeFile"):
            if codeFile.attrib["name"] == short_path:
                ProjectUtils.write_file(path,unescape(codeFile.text))


    def traverse(self,path,node):
        for file in node.findall("File"):
            self.create_file(f"{path}/{file.text}")
        for direc in node.findall("Directory"):
            os.mkdir(f"{ProjectUtils.get_path()}/{path}/{direc.attrib["name"]}")
            self.traverse(f"{path}/{direc.attrib["name"]}",direc)

    def extract_code(self):
        structure = self.root.find("Structure")
        path = "Implementation/Micromouse"
        self.traverse(path,structure)
