from dotenv import load_dotenv
from openai import OpenAI
import os

class AIAgent:

    responses = []

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('API_KEY')

        self.client = OpenAI(
            api_key=self.api_key
        )


    def send_message(self, message:str):
        response = self.client.responses.create(
            model="gpt-5-nano",
            input=message,
            store=True
        )
        self.responses.append(response)


    def get_last_response(self):
        if len(self.responses) > 0:
            return self.responses[-1]
        else:
            return None