from Code.Common.ai_agent import AgentUtils
from Code.Common.prompt_utils import PromptUtils
from Code.Common.iteration_manager import IterationManager
from Code.Common.project_utils import ProjectUtils



class Implementation:
    def __init__(self):
        self.sw_eng_agent = AgentUtils.create_agent("Implementation Engineer", model="gpt-5.1")

        print("Initializing Implementation Generation:")

        sw_eng_init_prompt = PromptUtils.get_prompt("Implementation Engineer","Initialize",self.sw_eng_agent)
        sw_eng_init_prompt.send_prompt()

        print("Initialized!")

    def generate_first_time(self):
        sw_eng_implement_prompt = PromptUtils.get_prompt("Implementation Engineer","Implement",self.sw_eng_agent)
        sw_eng_implement_prompt.send_prompt()

        sw_eng_learn_prompt = PromptUtils.get_prompt("Implementation Engineer", "Learn Findings", self.sw_eng_agent)
        sw_eng_learn_prompt.send_prompt()

    def generate_with_findings(self):
        sw_eng_implement_prompt = PromptUtils.get_prompt("Implementation Engineer","Implement",self.sw_eng_agent)
        sw_eng_implement_prompt.send_prompt()


    def next(self):
        return "int"