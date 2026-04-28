

from dotenv import load_dotenv
from openai import OpenAI
import os
import time

class _Logger:
    def __init__(self,agent):
        load_dotenv()
        self.root = os.getenv('ROOT')
        self.agent = agent
        date_time = time.strftime("%Y-%m-%d--%H-%M-%S")
        self.log_path = f"{self.root}/Logs/session_{date_time}.log"
        with open(self.log_path,"w+",encoding="UTF-8") as file:
            file.write(f"Log of {self.agent.identifier}\n")

    def log_received_message(self,message:str):
        date_time = time.strftime("%Y-%m-%d--%H:%M:%S")
        with open(self.log_path, "a",encoding="UTF-8") as file:
            file.write(f"[{date_time}]Agent: {message}\n")

    def log_sent_message(self,message:str):
        date_time = time.strftime("%Y-%m-%d--%H:%M:%S")
        with open(self.log_path, "a",encoding="UTF-8") as file:
            file.write(f"[{date_time}]User: {message}\n")


class AIAgent:

    responses = []

    chat_history = []


    def __init__(self,behaviour:str=None,identifier:str = None,model:str = None):
        load_dotenv()
        self.api_key = os.getenv('API_KEY')
        if behaviour is not None:
            self.chat_history.append( {"role": "system", "content": behaviour} )
        if identifier is None:
            self.identifier = "Default Name"
        if model is None:
            self.model = "gpt-5-nano"
        self.client = OpenAI(
            api_key=self.api_key
        )
        self.logger = _Logger(self)

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


