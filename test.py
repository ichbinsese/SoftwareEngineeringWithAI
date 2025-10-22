import pprint

from dotenv import load_dotenv
from openai import OpenAI
import os

# get api key
load_dotenv()
api_key = os.getenv('API_KEY')

client = OpenAI(
    api_key=api_key
)

response = client.responses.create(
    model = "gpt-5-nano",
    input = "Say Hello World",
    store = True
)

print(response.output_text)


