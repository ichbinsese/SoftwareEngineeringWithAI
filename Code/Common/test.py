import ai_agent
import prompt_utils



agent = ai_agent.AgentUtils.create_agent("Software Engineer")
prompt = prompt_utils.PromptUtils.get_prompt("Software Engineer","Initialize",agent)
prompt.send_prompt()
