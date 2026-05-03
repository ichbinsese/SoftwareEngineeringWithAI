import os

from Code.RequirementGeneration.excel_utils import RequirementExporter
from Code.Common.project_utils import ProjectUtils

VERSION = 1

root = ProjectUtils.get_path()
excel_path = os.path.join(root,"Requirements","High Level Requirements", "Excel")
exporter = RequirementExporter(VERSION, excel_path)
exporter.read_requirements()
xml_path = os.path.join(root,"Requirements","High Level Requirements", "Generated")
exporter.create_xml(xml_path)