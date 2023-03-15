""" Tests for the basic household example. """
# clean
import os

from hisim import hisim_main
from hisim.simulationparameters import SimulationParameters
from hisim import log
from hisim.postprocessingoptions import PostProcessingOptions
from hisim import utils
import pytest

@pytest.mark.examples
@utils.measure_execution_time
def test_household_with_heatpump_and_pv():
    """ Single day. """
    path = "../examples/household_with_heatpump_and_pv.py"
    func = "household_pv_hp"
    mysimpar = SimulationParameters.one_day_only(year=2019, seconds_per_timestep=60)
    hisim_main.main(path, func, mysimpar)
    log.information(os.getcwd())