from Code.Common.ai_agent import AgentUtils
from Code.Common.prompt_utils import PromptUtils
from Code.Common.iteration_manager import IterationManager
from Code.Common.project_utils import ProjectUtils
from Code.Common.findings_checker import FindingsChecker

class RequirementGeneration:
    def __init__(self):

        print("Initializing Requirements Generation:")

        self.sw_eng_agent = AgentUtils.create_agent("Software Engineer", model="gpt-5.1")
        self.sw_verify_agent = AgentUtils.create_agent("Software Verifier",model="gpt-5.1")

        sw_eng_init_prompt = PromptUtils.get_prompt("Software Engineer","Initialize",self.sw_eng_agent)
        sw_eng_init_prompt.send_prompt()

        sw_verify_init_prompt =  PromptUtils.get_prompt("Software Verifier","Initialize",self.sw_verify_agent)
        sw_verify_init_prompt.send_prompt()

        print("Initialized!")

    def generate_first_time(self):

        #HL Req 1
        sw_eng_refine_prompt = PromptUtils.get_prompt("Software Engineer", "Refine", self.sw_eng_agent)
        sw_eng_refine_prompt.send_prompt()
        #LL Req 1
        sw_verify_verify_prompt = PromptUtils.get_prompt("Software Verifier", "Verify", self.sw_verify_agent)
        sw_verify_verify_prompt.send_prompt()
        #Fingings 1

        sw_eng_learn_prompt = PromptUtils.get_prompt("Software Engineer", "Learn Findings", self.sw_eng_agent)
        sw_eng_learn_prompt.send_prompt()

    def generate_with_findings(self):
        IterationManager.iterate("llr")
        sw_eng_correct_prompt = PromptUtils.get_prompt("Software Engineer", "Correct", self.sw_eng_agent)
        sw_eng_correct_prompt.send_prompt()
        # LL Req 2
        # Answer 1
        IterationManager.iterate("llf")
        sw_verify_verify_prompt = PromptUtils.get_prompt("Software Verifier", "Verify With Answer", self.sw_verify_agent)
        sw_verify_verify_prompt.send_prompt()
        # Findings 2
        IterationManager.iterate("lla")

    def next(self):
        findings = ProjectUtils.read_file(f"Requirements/Low Level Requirements/Findings/Low Level Findings_{IterationManager.get_iteration("llf")}.xml")
        if findings == "clear":
            print("No Findings found")
            return "dd"
        else:
            print("Findings found, Correcting")
            checker = FindingsChecker(f"Requirements/Low Level Requirements/Findings/Low Level Findings_{IterationManager.get_iteration("llf")}.xml")
            if checker.check_catastrophic():
                ProjectUtils.write_file(
                    f"Requirements/High Level Requirements/Findings/High Level Findings_{IterationManager.get_iteration("hlf")}.xml",
                    findings)
                return "hlr"
            else:
                return "llr"

