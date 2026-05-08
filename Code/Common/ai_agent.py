

from dotenv import load_dotenv
from openai import OpenAI
from Code.Common.project_utils import ProjectUtils
import os
import time

class _AgentLogger:
    def __init__(self,agent):
        self.agent = agent
        date_time = time.strftime("%Y-%m-%d--%H-%M-%S")
        self.log_path = f"Logs/session_{date_time}.log"
        ProjectUtils.write_file(self.log_path,f"Log of {self.agent.identifier}\n")

    def log_received_message(self,message:str):
        date_time = time.strftime("%Y-%m-%d--%H:%M:%S")
        ProjectUtils.write_file(self.log_path, f"[{date_time}]Agent: {message}\n",overwrite=False)

    def log_sent_message(self,message:str):
        date_time = time.strftime("%Y-%m-%d--%H:%M:%S")
        ProjectUtils.write_file(self.log_path, f"[{date_time}]User: {message}\n",overwrite=False)



class AIAgent:
    responses = []

    chat_history = []

    identifier = ""

    def __init__(self,behaviour:str=None,identifier:str = None,model:str = None):
        load_dotenv()
        self.api_key = os.getenv('API_KEY')
        if behaviour is not None:
            self.chat_history.append( {"role": "system", "content": behaviour} )
        if identifier is None:
            self.identifier = "Default Name"
        else:
            self.identifier = identifier
        if model is None:
            self.model = "gpt-5-nano"
        else:
            self.model = model
        self.client = OpenAI(
            api_key=self.api_key
        )
        self.logger = _AgentLogger(self)

    def _send_message(self, message:str):
        self.logger.log_sent_message(message)
        self.chat_history.append({"role": "user", "content": message})
        print("Message sent")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.chat_history,
        )
        print("Answer received")
        response_text = response.choices[0].message.content
        self.logger.log_received_message(response_text)
        self.responses.append(response_text)
        return response_text

    def send_message(self, message:str):
        response = self._send_message(message)
        self.chat_history.append({"role": "assistant", "content": response})

    def send_message_no_reply(self,message:str):
        self._send_message(message)
        self.chat_history.append({"role": "assistant", "content": "Answered the Request."})

    def get_last_response(self):
        if len(self.responses) > 0:
            return self.responses[-1]
        else:
            return None


class AgentUtils:
    @staticmethod
    def create_agent(agent_type:str,model:str=None):
        behaviour = ProjectUtils.get_behaviour_text(agent_type)
        return  AIAgent(behaviour,agent_type,model)