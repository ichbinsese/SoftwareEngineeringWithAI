

class IterationManager:

    VERSION = 1

    iterations = {
        "llr" : 1,
        "hlr" : 1,
        "llf" : 1,
        "lla" : 1,
     }

    @staticmethod
    def initialize():
        pass

    @staticmethod
    def iterate(iteration_type:str):
        if iteration_type not in IterationManager.iterations.keys():
            print(f"Invalid iteration type: {iteration_type}")
            return
        IterationManager.iterations[iteration_type] += 1

    @staticmethod
    def get_iteration(iteration_type:str):
        if iteration_type not in IterationManager.iterations.keys():
            print(f"Invalid iteration type: {iteration_type}")
            return  1
        else :
            return IterationManager.iterations[iteration_type]