from Code.Common.ai_agent import AgentUtils
from Code.Common.prompt_utils import PromptUtils
from Code.Common.iteration_manager import IterationManager
from Code.Common.project_utils import ProjectUtils
from Code.Common.findings_checker import FindingsChecker

IterationManager.initialize()

sw_eng_agent = AgentUtils.create_agent("Design Engineer",model="gpt-5.1")
sw_eng_init_prompt = PromptUtils.get_prompt("Design Engineer","Initialize",sw_eng_agent)
sw_eng_init_prompt.send_prompt()

sw_verify_agent = AgentUtils.create_agent("Design Verifier",model="gpt-5.1")
sw_verify_init_prompt =  PromptUtils.get_prompt("Design Verifier","Initialize",sw_verify_agent)
sw_verify_init_prompt.send_prompt()
#HL Req 1
sw_eng_refine_prompt = PromptUtils.get_prompt("Design Engineer", "Create", sw_eng_agent)
sw_eng_refine_prompt.send_prompt()
#LL Req 1
sw_verify_verify_prompt = PromptUtils.get_prompt("Design Verifier", "Verify", sw_verify_agent)
sw_verify_verify_prompt.send_prompt()
#Fingings 1

sw_eng_learn_prompt = PromptUtils.get_prompt("Design Engineer", "Learn Findings", sw_eng_agent)
sw_eng_learn_prompt.send_prompt()

while True:
    IterationManager.iterate("dd")
    sw_eng_correct_prompt = PromptUtils.get_prompt("Design Engineer", "Correct", sw_eng_agent)
    sw_eng_correct_prompt.send_prompt()
    # LL Req 2
    # Answer 1
    IterationManager.iterate("df")
    sw_verify_verify_prompt = PromptUtils.get_prompt("Design Verifier", "Verify With Answer", sw_verify_agent)
    sw_verify_verify_prompt.send_prompt()
    #Findings 2
    IterationManager.iterate("da")
    findings = ProjectUtils.read_file(f"Design/Documents/Findings/Design Findings_{IterationManager.get_iteration("df")}.xml")
    if findings == "clear":
        print("No Findings found")
        break
    else:
        print("Findings found, Correcting")
        checker = FindingsChecker(f"Design/Documents/Findings/Design Findings_{IterationManager.get_iteration("df")}.xml")
        if checker.check_catastrophic():
            if checker.get_phase() == "High Level Requirements":
                print("Catastrophic Finding found, Correct HLRs!")
                input("Press Enter to continue...")

            if checker.get_phase() == "Lowe Level Requirements":
                print("Catastrophic Finding found, Correct LLRs!")
                IterationManager.iterate("llf")
                ProjectUtils.write_file(f"Requirements/Low Level Requirements/Findings/Low Level Findings_{IterationManager.get_iteration("llf")}.xml",findings)

