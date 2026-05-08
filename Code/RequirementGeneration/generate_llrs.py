from Code.Common.ai_agent import AgentUtils
from Code.Common.prompt_utils import PromptUtils
from Code.Common.iteration_manager import IterationManager
from Code.Common.project_utils import ProjectUtils

sw_eng_agent = AgentUtils.create_agent("Software Engineer")
sw_eng_init_prompt = PromptUtils.get_prompt("Software Engineer","Initialize",sw_eng_agent)
sw_eng_init_prompt.send_prompt()

sw_verify_agent = AgentUtils.create_agent("Software Verifier")
sw_verify_init_prompt =  PromptUtils.get_prompt("Software Verifier","Initialize",sw_verify_agent)
sw_verify_init_prompt.send_prompt()
#HL Req 1
sw_eng_refine_prompt = PromptUtils.get_prompt("Software Engineer", "Refine", sw_eng_agent)
sw_eng_refine_prompt.send_prompt()
#LL Req 1
sw_verify_verify_prompt = PromptUtils.get_prompt("Software Verifier", "Verify", sw_verify_agent)
sw_verify_verify_prompt.send_prompt()
#Fingings 1

while True:
    IterationManager.iterate("llr")
    sw_eng_correct_prompt = PromptUtils.get_prompt("Software Engineer", "Correct", sw_eng_agent)
    sw_eng_correct_prompt.send_prompt()
    # LL Req 2
    # Answer 1
    IterationManager.iterate("llf")
    sw_verify_verify_prompt = PromptUtils.get_prompt("Software Verifier", "Verify With Answer", sw_verify_agent)
    sw_verify_verify_prompt.send_prompt()
    #Findings 2
    IterationManager.iterate("lla")
    findings = ProjectUtils.read_file(f"Requirements/Low Level Requirements/Findings/Low Level Findings_{IterationManager.get_iteration("llf")}.xml")
    if findings == "clear":
        print("No Findings found")
        break
    else:
        print("Findings found, Correcting")

