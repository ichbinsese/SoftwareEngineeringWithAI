import ai_agent
import prompt_utils
from dotenv import load_dotenv
import os


ai = ai_agent.AIAgent()

load_dotenv()
root = os.getenv('ROOT')

with open(root + "\\Prompt Engineering\\Instances\\Software Engineer Instance\\test.prompt","r") as f:
    prompt = prompt_utils.Prompt(f.read(),ai)
    prompt.send_prompt()