from  Code.Implementation.code_extractor import CodeExtractor
from  Code.Common.project_utils import ProjectUtils

path = f"{ProjectUtils.get_path()}\\Implementation\\Micromouse\\Raw\\Implementation.xml"
extractor = CodeExtractor(path)
extractor.extract_code()


