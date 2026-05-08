from Code.Common.ai_agent import AgentUtils
from Code.Common.prompt_utils import PromptUtils

sw_eng_agent = AgentUtils.create_agent("Software Engineer")

sw_eng_refine_prompt = PromptUtils.get_prompt("Software Engineer", "Initialize", sw_eng_agent)
print(sw_eng_refine_prompt.prompt)

sw_eng_prompt = PromptUtils.get_prompt("Software Engineer", "Correct", sw_eng_agent)
print(sw_eng_prompt.prompt)