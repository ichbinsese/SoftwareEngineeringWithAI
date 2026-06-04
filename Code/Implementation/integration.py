from unittest import case

from Code.Common.ai_agent import AgentUtils
from Code.Common.project_utils import ProjectUtils
from Code.Common.iteration_manager import IterationManager
from Code.Common.prompt_utils import PromptUtils


class Integration:
    def __init__(self):
        self.sw_eng_agent = AgentUtils.create_agent("Fault Analyzer", model="gpt-5.1")
        analyze_prompt = PromptUtils.get_prompt("Fault Analyzer", "Initialize",  self.sw_eng_agent)
        analyze_prompt.send_prompt()


    def get_tester_answer(self):
        while True:
            answer = input("Did you find any Problems (y/n)")
            if answer == "n":
                 return True
            elif answer == "y":
                report = input("Describe the Problem")
                ProjectUtils.write_file(f"Implementation/Tester Findings/Tester Finding_{IterationManager.get_iteration("tf")}.xml", report)
                return False

    def generate(self):
        pass

    def analyze(self):
        analyze_prompt = PromptUtils.get_prompt("Fault Analyzer", "Analyze",  self.sw_eng_agent)
        analyze_prompt.send_prompt()
        IterationManager.iterate("it ")

    def next(self):
        if self.get_tester_answer():
            return "finished"
        else:
            self.analyze()
            phase = ProjectUtils.read_file(f"Implementation/Answers/Phase_{IterationManager.get_iteration("aa")}.xml")
            findings = ProjectUtils.read_file(f"Implementation/Answers/Findings_{IterationManager.get_iteration("aa")}.xml")

            path = ""


            match phase:
                case "hlr":
                    IterationManager.iterate("hlf")
                    print("Problem Found in High Level Requirements")
                    path = f"Requirements/High Level Requirements/Findings/High Level Findings_{IterationManager.get_iteration("hlf")}.xml"
                case "llr":
                    IterationManager.iterate("llf")
                    print("Problem Found in Low Level Requirements")
                    path = f"Requirements/Low Level Requirements/Findings/Low Level Findings_{IterationManager.get_iteration("hlf")}.xml"
                case "dd":
                    IterationManager.iterate("df")
                    print("Problem Found in Design")
                    path = f"Design/Documents/Findings/Design Level Findings_{IterationManager.get_iteration("df")}.xml"
                case "i":
                    print("Problem Found in Implementation")
                    path = f"Implementation/Findings/Implementation Findings_{IterationManager.get_iteration("if")}.xml"

            ProjectUtils.write_file(path,findings)
            return phase