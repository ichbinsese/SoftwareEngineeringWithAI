from Code.Common.ai_agent import AgentUtils
from Code.Common.prompt_utils import PromptUtils
from Code.Common.iteration_manager import IterationManager
from Code.Common.project_utils import ProjectUtils

sw_eng_agent = AgentUtils.create_agent("Software Engineer")
sw_eng_init_prompt = PromptUtils.get_prompt("Software Engineer","Initialize",sw_eng_agent)
sw_eng_init_prompt.send_prompt()

sw_verify_agent = AgentUtils.create_agent("Software Verifier")
sw_verify_init_prompt =  PromptUtils.get_prompt("Software Verifier","Initialize",sw_eng_agent)
sw_eng_init_prompt.send_prompt()

while True:
    sw_eng_refine_prompt = PromptUtils.get_prompt("Software Engineer","Refine",sw_eng_agent)
    sw_eng_refine_prompt.send_prompt()

    sw_verify_verify_prompt = PromptUtils.get_prompt("Software Verifier","Verify",sw_eng_agent)
    sw_verify_verify_prompt.send_prompt()

    findings = ProjectUtils.read_file(f"Requirements/Findings/Low Level Findings_{IterationManager.get_iteration("llr")}.xml")
    if findings == "clear":
        break

