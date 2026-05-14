import os
import pathlib
from dotenv import load_dotenv


class ProjectUtils:

    @staticmethod
    def read_file(file_path: str) -> str:
        load_dotenv()
        root = os.getenv("ROOT")
        while True:
            path = pathlib.Path(f"{root}/{file_path}")
            if path.exists():
                with open(path, "r",encoding="utf-8") as file:
                    return file.read()
            else:
                print(f"READ ERROR: File {file_path} does not exist")
                file_path = input("Please enter the local file path to recover: ")

    @staticmethod
    def get_path():
        load_dotenv()
        root = os.getenv("ROOT")
        return root

    @staticmethod
    def write_file(file_path: str, content: str, overwrite = True) -> None:
        if content.startswith("help"):
            print(content)

        mode = "w+"
        if not overwrite:
            mode = "a"
        load_dotenv()
        root = os.getenv("ROOT")
        while True:
            path = pathlib.Path(f"{root}/{file_path}")
            if path.parent.exists():
                with open(path, mode, encoding="utf-8") as file:
                    file.write(content)
                    return
            else:
                print(f"WRITE ERROR: File {file_path} does not exist")
                file_path = input("Please enter the local file path to recover: ")

    @staticmethod
    def get_prompt_text(instance: str, prompt: str) -> str:
        return ProjectUtils.read_file(f"Prompt Engineering/Instances/{instance}/{prompt}.prompt")


    @staticmethod
    def get_behaviour_text(instance: str):
        return ProjectUtils.read_file(f"Prompt Engineering/Instances/{instance}/{instance}.behaviour")