"""  Basic household new system setup. """

# clean

from typing import Optional, Any
from hisim.simulator import SimulationParameters
from hisim.components import loadprofilegenerator_connector
from hisim.components import weather
from hisim.components import building
from hisim.components import more_advanced_heat_pump_hplib
from hisim.components import electricity_meter
from hisim.components import simple_hot_water_storage
from hisim.components import generic_hot_water_storage_modular
from hisim.components import heat_distribution_system
from hisim import loadtypes as lt

__authors__ = "Jonas Hoppe"
__copyright__ = ""
__credits__ = ["Jonas Hoppe"]
__license__ = "-"
__version__ = ""
__maintainer__ = ""
__status__ = ""



def setup_function(
    my_sim: Any, my_simulation_parameters: Optional[SimulationParameters] = None
) -> None:  # noqa: too-many-statements
    """Basic household system setup.

    This setup function emulates an household including the basic components. Here the residents have their
    electricity and heating needs covered by the photovoltaic system and the heat pump.

    - Simulation Parameters
    - Components
        - Occupancy (Residents' Demands)
        - Weather
        - Building
        - Heat Pump
        - Heat Pump Controller for dhw
        - Heat Pump Controller for building heating
        - Heat Distribution System
        - Heat Distribution Controller
        - Hot Water Storage
        - DHW Water Storage
    """

    # =================================================================================================================================
    # Set System Parameters

    # Set Simulation Parameters
    year = 2021
    seconds_per_timestep = 60

    # =================================================================================================================================
    # Build Components

    # Build Simulation Parameters
    if my_simulation_parameters is None:
        my_simulation_parameters = SimulationParameters.three_months_with_plots_only(
            year=year, seconds_per_timestep=seconds_per_timestep
        )

    my_sim.set_simulation_parameters(my_simulation_parameters)

    # Build Heat Distribution Controller
    my_heat_distribution_controller_config = heat_distribution_system.HeatDistributionControllerConfig.get_default_heat_distribution_controller_config()

    my_heat_distribution_controller = heat_distribution_system.HeatDistributionController(
        my_simulation_parameters=my_simulation_parameters,
        config=my_heat_distribution_controller_config
    )
    # Build Building
    my_building_config = building.BuildingConfig.get_default_german_single_family_home()

    my_building = building.Building(
        config=my_building_config,
        my_simulation_parameters=my_simulation_parameters
    )

    # Build Occupancy
    my_occupancy_config = loadprofilegenerator_connector.OccupancyConfig.get_default_chr01_couple_both_at_work()

    my_occupancy = loadprofilegenerator_connector.Occupancy(
        config=my_occupancy_config, my_simulation_parameters=my_simulation_parameters
    )

    # Build Weather
    my_weather_config = weather.WeatherConfig.get_default( location_entry=weather.LocationEnum.AACHEN)

    my_weather = weather.Weather(
        config=my_weather_config,
        my_simulation_parameters=my_simulation_parameters
    )

    # Build Electricity Meter
    my_electricity_meter = electricity_meter.ElectricityMeter(
        my_simulation_parameters=my_simulation_parameters,
        config=electricity_meter.ElectricityMeterConfig.get_electricity_meter_default_config(),
    )

    # Build Heat Pump Controller for hot water (heating building)
    my_heatpump_controller_hotwater_config = more_advanced_heat_pump_hplib.HeatPumpHplibControllerHotWaterStorageL1Config.get_default_generic_heat_pump_controller_config()

    my_heatpump_controller_hotWater = more_advanced_heat_pump_hplib.HeatPumpHplibControllerHotWaterStorage(
        config=my_heatpump_controller_hotwater_config,
        my_simulation_parameters=my_simulation_parameters
    )

    my_heatpump_controller_dhw_config = more_advanced_heat_pump_hplib.HeatPumpHplibControllerDHWL1Config.get_default_generic_heat_pump_controller_config()

    # Build Heat Pump Controller for dhw
    my_heatpump_controller_dhw = more_advanced_heat_pump_hplib.HeatPumpHplibControllerDHW(
        config=my_heatpump_controller_dhw_config,
        my_simulation_parameters=my_simulation_parameters
    )

    # Build Heat Pump
    my_heatpump_config = more_advanced_heat_pump_hplib.HeatPumpHplibConfig.get_default_generic_advanced_hp_lib()

    my_heatpump = more_advanced_heat_pump_hplib.HeatPumpHplib(
        config=my_heatpump_config,
        my_simulation_parameters=my_simulation_parameters,
    )

    # Build Heat Distribution System
    my_heat_distribution_config = heat_distribution_system.HeatDistributionConfig.get_default_heatdistributionsystem_config(
        heating_load_of_building_in_watt=my_building.my_building_information.max_thermal_building_demand_in_watt
    )

    my_heat_distribution = heat_distribution_system.HeatDistribution(
        config=my_heat_distribution_config,
        my_simulation_parameters=my_simulation_parameters,
    )

    # Build Heat Water Storage
    my_hot_water_storage_config = simple_hot_water_storage.SimpleHotWaterStorageConfig.get_default_simplehotwaterstorage_config()

    my_hot_water_storage = simple_hot_water_storage.SimpleHotWaterStorage(
        config=my_hot_water_storage_config,
        my_simulation_parameters=my_simulation_parameters,
    )

    # Build DHW Storage
    my_dhw_storage_config = generic_hot_water_storage_modular.StorageConfig.get_default_config_for_boiler()

    my_dhw_storage = generic_hot_water_storage_modular.HotWaterStorage(
        config=my_dhw_storage_config,
        my_simulation_parameters=my_simulation_parameters,
    )

    # =================================================================================================================================
    # Connect Components
    my_building.connect_only_predefined_connections(my_weather)
    my_building.connect_only_predefined_connections(my_occupancy)

    my_building.connect_input(
        my_building.ThermalPowerDelivered,
        my_heat_distribution.component_name,
        my_heat_distribution.ThermalPowerDelivered,
    )

    #################################
    my_heat_distribution_controller.connect_only_predefined_connections(
        my_weather, my_building, my_hot_water_storage
    )

    my_heat_distribution.connect_only_predefined_connections(
        my_building, my_heat_distribution_controller, my_hot_water_storage)

    #################################
    my_heatpump.connect_only_predefined_connections(
        my_heatpump_controller_hotWater, my_heatpump_controller_dhw, my_weather, my_hot_water_storage,
        my_dhw_storage)


    # Verknüpfung mit Luft als Umgebungswärmeqzuelle
    if my_heatpump.parameters['Group'].iloc[0] == 1.0 or my_heatpump.parameters['Group'].iloc[
        0] == 4.0:
        my_heatpump.connect_input(
            my_heatpump.TemperatureInputPrimary,
            my_weather.component_name,
            my_weather.DailyAverageOutsideTemperatures,
        )
    else:
        raise KeyError("Wasser oder Sole als primäres Wärmeträgermedium muss über extra Wärmenetz-Modell noch bereitgestellt werden")

        #todo: Water and Brine Connection




    my_heatpump_controller_hotWater.connect_only_predefined_connections(my_heat_distribution_controller,
                                                                        my_weather,
                                                                        my_hot_water_storage)

    my_heatpump_controller_dhw.connect_only_predefined_connections(my_dhw_storage)

    #################################
    my_hot_water_storage.connect_input(
        my_hot_water_storage.WaterTemperatureFromHeatDistribution,
        my_heat_distribution.component_name,
        my_heat_distribution.WaterTemperatureOutput,
    )

    my_hot_water_storage.connect_input(
        my_hot_water_storage.WaterTemperatureFromHeatGenerator,
        my_heatpump.component_name,
        my_heatpump.TemperatureOutputHotWater,
    )

    my_hot_water_storage.connect_input(
        my_hot_water_storage.WaterMassFlowRateFromHeatGenerator,
        my_heatpump.component_name,
        my_heatpump.MassFlowOutputHotWater,
    )

    #################################

    my_dhw_storage.connect_only_predefined_connections(my_occupancy)
    my_dhw_storage.connect_input(
        my_dhw_storage.ThermalPowerDelivered,
        my_heatpump.component_name,
        my_heatpump.ThermalOutputPowerDHW,
    )

    ################################

    my_electricity_meter.add_component_input_and_connect(
        source_object_name=my_occupancy.component_name,
        source_component_output=my_occupancy.ElectricityOutput,
        source_load_type=lt.LoadTypes.ELECTRICITY,
        source_unit=lt.Units.WATT,
        source_tags=[lt.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED],
        source_weight=999,
    )

    my_electricity_meter.add_component_input_and_connect(
        source_object_name=my_heatpump.component_name,
        source_component_output=my_heatpump.ElectricalInputPowerGesamt,
        source_load_type=lt.LoadTypes.ELECTRICITY,
        source_unit=lt.Units.WATT,
        source_tags=[
            lt.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED,
        ],
        source_weight=999,
    )

    # =================================================================================================================================
    # Add Components to Simulation Parameters

    my_sim.add_component(my_occupancy)
    my_sim.add_component(my_weather)
    my_sim.add_component(my_electricity_meter)
    my_sim.add_component(my_building)
    my_sim.add_component(my_heat_distribution_controller)
    my_sim.add_component(my_heat_distribution)
    my_sim.add_component(my_hot_water_storage)
    my_sim.add_component(my_dhw_storage)
    my_sim.add_component(my_heatpump_controller_hotWater)
    my_sim.add_component(my_heatpump_controller_dhw)
    my_sim.add_component(my_heatpump)
