import ai_agent
import prompt_utils
from dotenv import load_dotenv
import os




load_dotenv()
root = os.getenv('ROOT')

with open(root + "\\Prompt Engineering\\Instances\\Software Engineer Instance\\test.prompt","r") as f:
    ai = ai_agent.AIAgent(behaviour="You are a Expert ins SW Engineering")

    prompt = prompt_utils.Prompt(f.read(),ai)
    prompt.send_prompt()