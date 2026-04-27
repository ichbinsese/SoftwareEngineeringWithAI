import ai_agent
import prompt_utils
import pathlib
ai = ai_agent.AIAgent()

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

with open(ROOT_DIR / "Prompt Engineering\\Instances\\Software Engineer Instance\\Initialize.prompt","r") as f:
    prompt = prompt_utils.Prompt(f.read(),ai)