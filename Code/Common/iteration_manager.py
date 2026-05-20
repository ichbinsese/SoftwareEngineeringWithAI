from Code.Common.project_utils import ProjectUtils
import json
class IterationManager:

    VERSION = 1

    iterations = {
        "llr" : 1,
        "hlr" : 1,
        "llf" : 1,
        "lla" : 1,
        "dd" : 1,
        "df" : 1,
        "da" : 1,
     }

    @staticmethod
    def initialize():
        s = ProjectUtils.read_file(f"Requirements/Iteration.json")
        IterationManager.iterations = json.loads(s)

    @staticmethod
    def iterate(iteration_type:str):
        if iteration_type not in IterationManager.iterations.keys():
            print(f"Invalid iteration type: {iteration_type}")
            return
        IterationManager.iterations[iteration_type] += 1
        s = json.dumps(IterationManager.iterations, indent=4)
        ProjectUtils.write_file(f"Requirements/Iteration.json", s)



    @staticmethod
    def get_iteration(iteration_type:str):
        if iteration_type not in IterationManager.iterations.keys():
            print(f"Invalid iteration type: {iteration_type}")
            return  1
        else :
            return IterationManager.iterations[iteration_type]