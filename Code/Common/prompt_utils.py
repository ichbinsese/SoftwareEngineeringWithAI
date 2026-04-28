from ai_agent import AIAgent as Agent, AIAgent
from dotenv import load_dotenv
import os

class _MarkerFunctions:
    #must return plain text
    @staticmethod
    def requirements(plain_text:str, position:int):
        return plain_text

    @staticmethod
    def HLRs(plain_text:str, position:int):
        return plain_text

    @staticmethod
    def LLRs(plain_text:str, position:int):
        return plain_text

    @staticmethod
    def file(plain_text:str, position:int):
        load_dotenv()
        root = os.getenv("ROOT")
        path = plain_text[plain_text.find("<") + 1:plain_text.find(">")]
        plain_text = plain_text.replace("<" + path + ">","",1)
        print(f"{root}/{path}")
        with open(f"{root}/{path}", "r",encoding="utf-8") as file:
            plain_text = plain_text[:position] + file.read() + plain_text[:position]
        return plain_text


class _SplitterFunctions:

    #must all hove text, plain_text and agent as parameters

    @staticmethod
    def sendoff(text: str, plain_text: str, agent: Agent):
        return [
            (_PromptFunctions.sendoff, [text, agent]),
        ]


    @staticmethod
    def send(text: str, plain_text: str, agent: Agent):
        return [
            (_PromptFunctions.send, [text, agent]),
        ]

    @staticmethod
    def check(text:str,plain_text:str,agent:Agent):
        return  [
           # ( _PromptFunctions.send ,  [text,agent]),
            ( _PromptFunctions.check , [agent.get_last_response])
        ]

    @staticmethod
    def store(text:str,plain_text:str,agent:Agent):
        path = plain_text[plain_text.find("<"):plain_text.find(">")]
        return  [
           # (_PromptFunctions.send , [text,agent]),
            (_PromptFunctions.store , [agent.get_last_response,path]),
        ]

class _PromptFunctions:

    @staticmethod
    def sendoff(text:str,agent:Agent):
        agent.send_message_no_reply(text)

    @staticmethod
    def send(text:str,agent:Agent):
        agent.send_message(text)

    @staticmethod
    def check(answer_method):
        answer = answer_method()
        if answer.lower() == "check":
            #todo change to debug function later
            print("Prompt Check!")
            return
        elif answer.lower().startswith("help"):
            print("Agent Needs Help")
            print(answer)
        else:
            print("Error: Unexpected answer:")
            print(answer)


    @staticmethod
    def store(answer_method, path:str):
        answer = answer_method()
        with open(path,"w+") as f:
            f.write(answer)


class Prompt(object):

    plain_prompt = ""

    markers = {
        "{{requirements}}" : _MarkerFunctions.requirements,
        "{{HLRs}}" : _MarkerFunctions.HLRs,
        "{{LLRs}}" : _MarkerFunctions.LLRs,
        "{{file}}" : _MarkerFunctions.file
    }

    splitters = {
        "{check}" : _SplitterFunctions.check,
        "{store}" : _SplitterFunctions.store,
        "{send}" : _SplitterFunctions.send,
        "{sendoff}" : _SplitterFunctions.sendoff,
    }

    prompt = []

    def __init__(self, prompt:str, agent:Agent):
        self.plain_prompt = prompt
        self.agent = agent
        self._fill_markers()
        self._split_prompt()
        print(self.prompt)


    def _fill_markers(self):
        for marker in self.markers.keys():
            while True:
                position = self.plain_prompt.find(marker)
                if position == -1:
                    break
                else:
                    self.plain_prompt = self.plain_prompt.replace(marker, "",1)
                    self.plain_prompt = self.markers[marker](self.plain_prompt, position)

    def _split_prompt(self):
        while True:
            matches = [(s,   self.plain_prompt.find(s)) for s in self.splitters.keys() if self.plain_prompt.find(s) != -1]
            if not matches:
                return  # no substring found
            res = min(matches, key=lambda x: x[1])
            self.plain_prompt = self.plain_prompt.replace(res[0], "",1)
            text = self.plain_prompt[0:res[1]]

            self.prompt +=  self.splitters[res[0]](text,self.plain_prompt,self.agent)
            self.plain_prompt = self.plain_prompt[res[1]:]


    def send_prompt(self):
        for sub_prompt in self.prompt:
           sub_prompt[0](*sub_prompt[1])