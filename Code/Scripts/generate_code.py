from  Code.DesignGeneration.design_generation import *
from Code.Implementation.implementation import *
from Code.RequirementGeneration.requirement_generation import *
from Code.RequirementGeneration.high_level_communication import *
from Code.Implementation.integration import *
from Code.Common.iteration_manager import  IterationManager
import sys

class GenerateCode:
    design_generator = DesignGeneration()
    requirement_generator = RequirementGeneration()
    implementation = Implementation()
    integration = Integration()

    @staticmethod
    def finished():
        print("Finished")
        sys.exit(0)

    states = {
        "hlr": {
            0: HighLevelCommunication.correct,
            1: HighLevelCommunication.correct,
            "generate": 1,
            "transition": HighLevelCommunication.next,
            "order": 0
        },
        "llr": {
            0 : requirement_generator.generate_first_time,
            1 : requirement_generator.generate_with_findings,
            "generate" : 0,
            "transition" : requirement_generator.next,
            "order": 1
        },
        "dd": {
            0: design_generator.generate_first_time,
            1: design_generator.generate_with_findings,
            "generate": 0,
            "transition": design_generator.next,
            "order": 2
        },
        "i": {
            0: implementation.generate_first_time,
            1: implementation.generate_with_findings,
            "generate": 0,
            "transition": implementation.next,
            "order": 3
        },
        "int" : {
            0: integration.generate,
            1: integration.generate,
            "generate": 1,
            "transition": integration.next,
            "order": 4
        },

        "finished": {
            1 : finished,
            "generate": 1,
            "order": 5
        }
    }

    state = "llr"

    @staticmethod
    def process_state():
        GenerateCode.states[GenerateCode.state][
            GenerateCode.states[GenerateCode.state]["generate"]]()  # run current state
        GenerateCode.states[GenerateCode.state]["generate"] = 1  # set to generation with findings
        next_state = GenerateCode.states[GenerateCode.state]["transition"]()
        if next_state != GenerateCode.state:
            GenerateCode.states[GenerateCode.state]["generate"] = 0 #revert when leaving state. As on regression, the next time the state is called no findings will exist for it

        if GenerateCode.states[next_state]["order"] < GenerateCode.states[GenerateCode.state]["order"]:
            GenerateCode.states[next_state]["generate"] = 1 # when regressing the next state will have to accept findings from the current state


        GenerateCode.state = next_state

    @staticmethod
    def generate():
        GenerateCode.state = "llr"
        while True:
          GenerateCode.process_state()

    @staticmethod
    def start_from_design():
        GenerateCode.state = "dd"
        IterationManager.initialize()
        while True:
            GenerateCode.process_state()


#GenerateCode.generate()
GenerateCode.start_from_design()

