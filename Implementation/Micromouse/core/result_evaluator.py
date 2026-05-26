
# SecondRunResultEvaluatorAndReporter.
# Trace:
#   - CMP--10 SecondRunResultEvaluatorAndReporter

class SecondRunResultEvaluatorAndReporter:
    def __init__(self, map_manager, logger):
        self._map_manager = map_manager
        self._logger = logger
        self._run_controller = None

    def set_run_controller(self, run_ctrl):
        self._run_controller = run_ctrl

    def on_second_run_completed(self, final_x, final_y, success, reason):
        if success:
            self._logger.log(
                "Second run SUCCESS at (%d,%d) reason=%s" % (final_x, final_y, reason),
                component="CMP--10",
            )
        else:
            self._logger.log(
                "Second run FAILURE at (%d,%d) reason=%s" % (final_x, final_y, reason),
                component="CMP--10",
            )
