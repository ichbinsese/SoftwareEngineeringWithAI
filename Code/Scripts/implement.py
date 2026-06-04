from Code.Common.ai_agent import AgentUtils
from Code.Common.prompt_utils import PromptUtils
from Code.Common.iteration_manager import IterationManager
from Code.Common.project_utils import ProjectUtils



IterationManager.initialize()

sw_eng_agent = AgentUtils.create_agent("Implementation Engineer",model="gpt-5.1")
sw_eng_init_prompt = PromptUtils.get_prompt("Implementation Engineer","Initialize",sw_eng_agent)
sw_eng_init_prompt.send_prompt()

sw_eng_implement_prompt = PromptUtils.get_prompt("Implementation Engineer","Implement",sw_eng_agent)
sw_eng_implement_prompt.send_prompt()