"""Test for advanced heat pump hplib."""

import pytest
from tests import functions_for_testing as fft
from hisim import component as cp
from hisim.components.more_advanced_heat_pump_hplib import (
    HeatPumpHplibWithTwoOutputs,
    HeatPumpHplibWithTwoOutputsConfig,
    HeatPumpWithTwoOutputsState,
)
from hisim import loadtypes as lt
from hisim.simulationparameters import SimulationParameters
from hisim import log


@pytest.mark.base
def test_heat_pump_hplib_new():
    """Test heat pump hplib."""

    # Definitions for HeatPump init
    model: str = "Generic"
    group_id: int = 1
    t_in: float = -7
    t_out: float = 52
    p_th_set: float = 10000
    simpars = SimulationParameters.one_day_only(2017, 60)
    # Definitions for i_simulate
    timestep = 1
    force_convergence = False

    # Create fake component outputs as inputs for simulation
    on_off_switch_space_heating = cp.ComponentOutput(
        "Fake_on_off_switch", "Fake_on_off_switch", lt.LoadTypes.ANY, lt.Units.ANY
    )
    on_off_switch_dhw = cp.ComponentOutput(
        "Fake_on_off_switch", "Fake_on_off_switch", lt.LoadTypes.ANY, lt.Units.ANY
    )
    const_thermal_power_value_dhw = cp.ComponentOutput(
        "Fake_const_thermal_power_value_dhw", "Fake_const_thermal_power_value_dhw", lt.LoadTypes.ANY, lt.Units.ANY
    )
    t_in_primary = cp.ComponentOutput(
        "Fake_t_in_primary", "Fake_t_in_primary", lt.LoadTypes.ANY, lt.Units.ANY
    )
    t_in_secondary_space_heating = cp.ComponentOutput(
        "Fake_t_in_secondary_hot_water", "Fake_t_in_secondary_hot_water", lt.LoadTypes.ANY, lt.Units.ANY
    )
    t_in_secondary_dhw = cp.ComponentOutput(
        "Fake_t_in_secondary_dhw", "Fake_t_in_secondary_dhw", lt.LoadTypes.ANY, lt.Units.ANY
    )
    t_amb = cp.ComponentOutput(
        "Fake_t_amb", "Fake_t_amb", lt.LoadTypes.ANY, lt.Units.ANY
    )

    # Initialize component
    heatpump_config = HeatPumpHplibWithTwoOutputsConfig(
        name="Heat Pump",
        model=model,
        heat_source="air",
        group_id=group_id,
        heating_reference_temperature_in_celsius=t_in,
        flow_temperature_in_celsius=t_out,
        set_thermal_output_power_in_watt=p_th_set,
        cycling_mode=True,
        hx_building_temp_diff=2,
        minimum_idle_time_in_seconds=600,
        minimum_running_time_in_seconds=600,
        co2_footprint=p_th_set * 1e-3 * 165.84,
        cost=p_th_set * 1e-3 * 1513.74,
        lifetime=10,
        maintenance_cost_as_percentage_of_investment=0.025,
        consumption=0,
    )
    heatpump = HeatPumpHplibWithTwoOutputs(config=heatpump_config, my_simulation_parameters=simpars)
    heatpump.state = HeatPumpWithTwoOutputsState(
        time_on=0, time_off=0, time_on_cooling=0, on_off_previous=1, cumulative_electrical_energy_in_watt_hour=0, cumulative_thermal_energy_in_watt_hour=0
    )

    number_of_outputs = fft.get_number_of_outputs(
        [on_off_switch_space_heating, on_off_switch_dhw, const_thermal_power_value_dhw, t_in_primary, t_in_secondary_space_heating, t_in_secondary_dhw, t_amb, heatpump]
    )
    stsv: cp.SingleTimeStepValues = cp.SingleTimeStepValues(number_of_outputs)

    heatpump.on_off_switch_sh.source_output = on_off_switch_space_heating
    heatpump.on_off_switch_dhw.source_output = on_off_switch_dhw
    heatpump.const_thermal_power_value_dhw.source_output = const_thermal_power_value_dhw
    heatpump.t_in_primary.source_output = t_in_primary
    heatpump.t_in_secondary_sh.source_output = t_in_secondary_space_heating
    heatpump.t_in_secondary_dhw.source_output = t_in_secondary_dhw
    heatpump.t_amb.source_output = t_amb

    # Add Global Index and set values for fake Inputs
    fft.add_global_index_of_components(
        [on_off_switch_space_heating, on_off_switch_dhw, const_thermal_power_value_dhw,
         t_in_primary, t_in_secondary_space_heating, t_in_secondary_dhw, t_amb, heatpump]
    )
    stsv.values[on_off_switch_space_heating.global_index] = 1
    stsv.values[on_off_switch_dhw.global_index] = 0
    stsv.values[const_thermal_power_value_dhw.global_index] = 0
    stsv.values[t_in_primary.global_index] = -7
    stsv.values[t_in_secondary_space_heating.global_index] = 47.0
    stsv.values[t_in_secondary_dhw.global_index] = 55.0
    stsv.values[t_amb.global_index] = -7

    # Simulation
    heatpump.i_simulate(
        timestep=timestep, stsv=stsv, force_convergence=force_convergence
    )
    log.information(str(stsv.values))
    # Check
    assert p_th_set == stsv.values[heatpump.p_th_sh.global_index]
    assert 7074.033573088874 == stsv.values[heatpump.p_el_sh.global_index]
    assert 1.4136206588052005 == stsv.values[heatpump.cop.global_index]
    assert t_out == stsv.values[heatpump.t_out_sh.global_index]
    assert 0.47619047619047616 == stsv.values[heatpump.m_dot_sh.global_index]
    assert 60 == stsv.values[heatpump.time_on.global_index]
    assert 0 == stsv.values[heatpump.time_off.global_index]