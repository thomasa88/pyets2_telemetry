SCS_CHANNELS = []

def identity(val):
    return val

def mps_to_kph(mps):
    return 3.6 * mps

def non_zero(value):
    return value != 0

class ScsChannel:
    def __init__(self, name, type, indexed, json_name=None, conversion_func=identity):
        self.name = name
        self.type = type
        # Indicates if the value is indexed - not the channel
        self.indexed = indexed
        if json_name:
            if not isinstance(json_name, list):
                self.json_name = json_name.split('.')
            else:
                self.json_name = [x.split('.') for x in json_name]
        else:
            self.json_name = None
        self.conversion_func = conversion_func
        self.id = len(SCS_CHANNELS)
        SCS_CHANNELS.append(self)
        
SCS_RESULT_ok = 0
SCS_RESULT_unsupported = -1
SCS_RESULT_invalid_parameter = -2
SCS_RESULT_already_registered = -3
SCS_RESULT_not_found = -4
SCS_RESULT_unsupported_type = -5
SCS_RESULT_not_now = -6
SCS_RESULT_generic_error = -7

SCS_TELEMETRY_CHANNEL_FLAG_none = 0x00000000
SCS_TELEMETRY_CHANNEL_FLAG_each_frame = 0x00000001
SCS_TELEMETRY_CHANNEL_FLAG_no_value = 0x00000002

SCS_U32_NIL = -1

SCS_VALUE_TYPE_INVALID = 0
SCS_VALUE_TYPE_bool = 1
SCS_VALUE_TYPE_s32 = 2
SCS_VALUE_TYPE_u32 = 3
SCS_VALUE_TYPE_u64 = 4
SCS_VALUE_TYPE_float = 5
SCS_VALUE_TYPE_double = 6
SCS_VALUE_TYPE_fvector = 7
SCS_VALUE_TYPE_dvector = 8
SCS_VALUE_TYPE_euler = 9
SCS_VALUE_TYPE_fplacement = 10
SCS_VALUE_TYPE_dplacement = 11
SCS_VALUE_TYPE_string = 12
SCS_VALUE_TYPE_s64 = 13

SCS_TELEMETRY_CHANNEL_game_time = ScsChannel("game.time", SCS_VALUE_TYPE_u32, False)
SCS_TELEMETRY_CHANNEL_local_scale = ScsChannel("local.scale", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_CHANNEL_next_rest_stop = ScsChannel("rest.stop", SCS_VALUE_TYPE_s32, False)
SCS_TELEMETRY_JOB_CHANNEL_cargo_damage = ScsChannel("job.cargo.damage", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_TRAILER_CHANNEL_cargo_damage = ScsChannel("trailer.0.cargo.damage", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_TRAILER_CHANNEL_connected = ScsChannel("trailer.0.connected", SCS_VALUE_TYPE_bool, 'trailer.attached')
SCS_TELEMETRY_TRAILER_CHANNEL_local_angular_acceleration = ScsChannel("trailer.0.acceleration.angular", SCS_VALUE_TYPE_fvector, False)
SCS_TELEMETRY_TRAILER_CHANNEL_local_angular_velocity = ScsChannel("trailer.0.velocity.angular", SCS_VALUE_TYPE_fvector, False)
SCS_TELEMETRY_TRAILER_CHANNEL_local_linear_acceleration = ScsChannel("trailer.0.acceleration.linear", SCS_VALUE_TYPE_fvector, False)
SCS_TELEMETRY_TRAILER_CHANNEL_local_linear_velocity = ScsChannel("trailer.0.velocity.linear", SCS_VALUE_TYPE_fvector, False)
SCS_TELEMETRY_TRAILER_CHANNEL_wear_chassis = ScsChannel("trailer.0.wear.chassis", SCS_VALUE_TYPE_float, False, 'trailer.wear')
SCS_TELEMETRY_TRAILER_CHANNEL_wear_wheels = ScsChannel("trailer.0.wear.wheels", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_TRAILER_CHANNEL_wheel_lift_offset = ScsChannel("trailer.0.wheel.lift.offset", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_TRAILER_CHANNEL_wheel_lift = ScsChannel("trailer.0.wheel.lift", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_TRAILER_CHANNEL_wheel_on_ground = ScsChannel("trailer.0.wheel.on_ground", SCS_VALUE_TYPE_bool, False)
SCS_TELEMETRY_TRAILER_CHANNEL_wheel_rotation = ScsChannel("trailer.0.wheel.rotation", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_TRAILER_CHANNEL_wheel_steering = ScsChannel("trailer.0.wheel.steering", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_TRAILER_CHANNEL_wheel_substance = ScsChannel("trailer.0.wheel.substance", SCS_VALUE_TYPE_u32, False)
SCS_TELEMETRY_TRAILER_CHANNEL_wheel_susp_deflection = ScsChannel("trailer.0.wheel.suspension.deflection", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_TRAILER_CHANNEL_wheel_velocity = ScsChannel("trailer.0.wheel.angular_velocity", SCS_VALUE_TYPE_fvector, False)
SCS_TELEMETRY_TRAILER_CHANNEL_world_placement = ScsChannel("trailer.0.world.placement", SCS_VALUE_TYPE_dplacement, False, 'trailer.placement')
#SCS_TELEMETRY_TRUCK_CHANNEL_adblue_average_consumption = ScsChannel("truck.adblue.consumption.average", SCS_VALUE_TYPE_float, False, 'truck.adblueAverageConsumption')
SCS_TELEMETRY_TRUCK_CHANNEL_adblue = ScsChannel("truck.adblue", SCS_VALUE_TYPE_float, False, 'truck.adblue')
SCS_TELEMETRY_TRUCK_CHANNEL_adblue_warning = ScsChannel("truck.adblue.warning", SCS_VALUE_TYPE_bool, False, 'truck.adblueWarningOn')
SCS_TELEMETRY_TRUCK_CHANNEL_battery_voltage = ScsChannel("truck.battery.voltage", SCS_VALUE_TYPE_float, False, 'truck.batteryVoltage')
SCS_TELEMETRY_TRUCK_CHANNEL_battery_voltage_warning = ScsChannel("truck.battery.voltage.warning", SCS_VALUE_TYPE_bool, False, 'truck.batteryVoltageWarningOn')
SCS_TELEMETRY_TRUCK_CHANNEL_brake_air_pressure_emergency = ScsChannel("truck.brake.air.pressure.emergency", SCS_VALUE_TYPE_bool, False, 'truck.airPressureEmergencyOn')
SCS_TELEMETRY_TRUCK_CHANNEL_brake_air_pressure = ScsChannel("truck.brake.air.pressure", SCS_VALUE_TYPE_float, False, 'truck.airPressure')
SCS_TELEMETRY_TRUCK_CHANNEL_brake_air_pressure_warning = ScsChannel("truck.brake.air.pressure.warning", SCS_VALUE_TYPE_bool, False, 'truck.airPressureWarningOn')
SCS_TELEMETRY_TRUCK_CHANNEL_brake_temperature = ScsChannel("truck.brake.temperature", SCS_VALUE_TYPE_float, False, 'truck.brakeTemperature')
SCS_TELEMETRY_TRUCK_CHANNEL_cabin_angular_acceleration = ScsChannel("truck.cabin.acceleration.angular", SCS_VALUE_TYPE_fvector, False)
SCS_TELEMETRY_TRUCK_CHANNEL_cabin_angular_velocity = ScsChannel("truck.cabin.velocity.angular", SCS_VALUE_TYPE_fvector, False)
SCS_TELEMETRY_TRUCK_CHANNEL_cabin_offset = ScsChannel("truck.cabin.offset", SCS_VALUE_TYPE_fplacement, False)
SCS_TELEMETRY_TRUCK_CHANNEL_cruise_control = ScsChannel("truck.cruise_control", SCS_VALUE_TYPE_float, False, 'truck.cruiseControlSpeed', mps_to_kph) #cruiseControlOn when > 0
SCS_TELEMETRY_TRUCK_CHANNEL_dashboard_backlight = ScsChannel("truck.dashboard.backlight", SCS_VALUE_TYPE_float, False, ['truck.lightsDashboardValue', 'truck.lightDashboardOn'], [identity, non_zero])
SCS_TELEMETRY_TRUCK_CHANNEL_displayed_gear = ScsChannel("truck.displayed.gear", SCS_VALUE_TYPE_s32, False, 'truck.displayedGear')
SCS_TELEMETRY_TRUCK_CHANNEL_effective_brake = ScsChannel("truck.effective.brake", SCS_VALUE_TYPE_float, False, 'truck.gameBrake')
SCS_TELEMETRY_TRUCK_CHANNEL_effective_clutch = ScsChannel("truck.effective.clutch", SCS_VALUE_TYPE_float, False, 'truck.gameClutch')
SCS_TELEMETRY_TRUCK_CHANNEL_effective_steering = ScsChannel("truck.effective.steering", SCS_VALUE_TYPE_float, False, 'truck.gameSteer')
SCS_TELEMETRY_TRUCK_CHANNEL_effective_throttle = ScsChannel("truck.effective.throttle", SCS_VALUE_TYPE_float, False, 'truck.gameThrottle')
SCS_TELEMETRY_TRUCK_CHANNEL_electric_enabled = ScsChannel("truck.electric.enabled", SCS_VALUE_TYPE_bool, False, 'truck.electricOn')
SCS_TELEMETRY_TRUCK_CHANNEL_engine_enabled = ScsChannel("truck.engine.enabled", SCS_VALUE_TYPE_bool, False, 'truck.engineOn')
SCS_TELEMETRY_TRUCK_CHANNEL_engine_gear = ScsChannel("truck.engine.gear", SCS_VALUE_TYPE_s32, False, 'truck.gear')
SCS_TELEMETRY_TRUCK_CHANNEL_engine_rpm = ScsChannel("truck.engine.rpm", SCS_VALUE_TYPE_float, False, 'truck.engineRpm')
SCS_TELEMETRY_TRUCK_CHANNEL_fuel_average_consumption = ScsChannel("truck.fuel.consumption.average", SCS_VALUE_TYPE_float, False, 'truck.fuelAverageConsumption')
SCS_TELEMETRY_TRUCK_CHANNEL_fuel_range = ScsChannel("truck.fuel.range", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_TRUCK_CHANNEL_fuel = ScsChannel("truck.fuel.amount", SCS_VALUE_TYPE_float, False, 'truck.fuel')
SCS_TELEMETRY_TRUCK_CHANNEL_fuel_warning = ScsChannel("truck.fuel.warning", SCS_VALUE_TYPE_bool, False, 'truck.fuelWarningOn')
SCS_TELEMETRY_TRUCK_CHANNEL_head_offset = ScsChannel("truck.head.offset", SCS_VALUE_TYPE_fplacement, False)
SCS_TELEMETRY_TRUCK_CHANNEL_hshifter_selector = ScsChannel("truck.hshifter.select", SCS_VALUE_TYPE_bool, True)
SCS_TELEMETRY_TRUCK_CHANNEL_hshifter_slot = ScsChannel("truck.hshifter.slot", SCS_VALUE_TYPE_u32, False, 'truck.shifterSlot')
SCS_TELEMETRY_TRUCK_CHANNEL_input_brake = ScsChannel("truck.input.brake", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_TRUCK_CHANNEL_input_clutch = ScsChannel("truck.input.clutch", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_TRUCK_CHANNEL_input_steering = ScsChannel("truck.input.steering", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_TRUCK_CHANNEL_input_throttle = ScsChannel("truck.input.throttle", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_TRUCK_CHANNEL_lblinker = ScsChannel("truck.lblinker", SCS_VALUE_TYPE_bool, False, 'truck.blinkerLeftOn')
SCS_TELEMETRY_TRUCK_CHANNEL_light_aux_front = ScsChannel("truck.light.aux.front", SCS_VALUE_TYPE_u32, False, 'truck.lightsAuxFrontOn', non_zero)
SCS_TELEMETRY_TRUCK_CHANNEL_light_aux_roof = ScsChannel("truck.light.aux.roof", SCS_VALUE_TYPE_u32, False, 'truck.lightsAuxRoofOn', non_zero)
SCS_TELEMETRY_TRUCK_CHANNEL_light_beacon = ScsChannel("truck.light.beacon", SCS_VALUE_TYPE_bool, False, 'truck.lightsBeaconOn')
SCS_TELEMETRY_TRUCK_CHANNEL_light_brake = ScsChannel("truck.light.brake", SCS_VALUE_TYPE_bool, False, 'truck.lightsBrakeOn')
SCS_TELEMETRY_TRUCK_CHANNEL_light_high_beam = ScsChannel("truck.light.beam.high", SCS_VALUE_TYPE_bool, False, 'truck.lightsBeamHighOn')
SCS_TELEMETRY_TRUCK_CHANNEL_light_lblinker = ScsChannel("truck.light.lblinker", SCS_VALUE_TYPE_bool, False, 'truck.blinkerLeftActive')
SCS_TELEMETRY_TRUCK_CHANNEL_light_low_beam = ScsChannel("truck.light.beam.low", SCS_VALUE_TYPE_bool, False, 'truck.lightsBeamLowOn')
SCS_TELEMETRY_TRUCK_CHANNEL_light_parking = ScsChannel("truck.light.parking", SCS_VALUE_TYPE_bool, False, 'truck.lightsParkingOn')
SCS_TELEMETRY_TRUCK_CHANNEL_light_rblinker = ScsChannel("truck.light.rblinker", SCS_VALUE_TYPE_bool, False, 'truck.blinkerRightActive')
SCS_TELEMETRY_TRUCK_CHANNEL_light_reverse = ScsChannel("truck.light.reverse", SCS_VALUE_TYPE_bool, False, 'truck.lightsReverseOn')
SCS_TELEMETRY_TRUCK_CHANNEL_local_angular_acceleration = ScsChannel("truck.local.acceleration.angular", SCS_VALUE_TYPE_fvector, False)
SCS_TELEMETRY_TRUCK_CHANNEL_local_angular_velocity = ScsChannel("truck.local.velocity.angular", SCS_VALUE_TYPE_fvector, False)
SCS_TELEMETRY_TRUCK_CHANNEL_local_linear_acceleration = ScsChannel("truck.local.acceleration.linear", SCS_VALUE_TYPE_fvector, False, 'truck.acceleration')
SCS_TELEMETRY_TRUCK_CHANNEL_local_linear_velocity = ScsChannel("truck.local.velocity.linear", SCS_VALUE_TYPE_fvector, False)
SCS_TELEMETRY_TRUCK_CHANNEL_motor_brake = ScsChannel("truck.brake.motor", SCS_VALUE_TYPE_bool, False, 'truck.motorBrakeOn')
SCS_TELEMETRY_TRUCK_CHANNEL_navigation_distance = ScsChannel("truck.navigation.distance", SCS_VALUE_TYPE_float, False, 'navigation.estimatedDistance')
SCS_TELEMETRY_TRUCK_CHANNEL_navigation_speed_limit = ScsChannel("truck.navigation.speed.limit", SCS_VALUE_TYPE_float, False, 'navigation.speedLimit', mps_to_kph)
SCS_TELEMETRY_TRUCK_CHANNEL_navigation_time = ScsChannel("truck.navigation.time", SCS_VALUE_TYPE_float, False)
SCS_TELEMETRY_TRUCK_CHANNEL_odometer = ScsChannel("truck.odometer", SCS_VALUE_TYPE_float, False, 'truck.odometer')
SCS_TELEMETRY_TRUCK_CHANNEL_oil_pressure = ScsChannel("truck.oil.pressure", SCS_VALUE_TYPE_float, False, 'truck.oilPressure')
SCS_TELEMETRY_TRUCK_CHANNEL_oil_pressure_warning = ScsChannel("truck.oil.pressure.warning", SCS_VALUE_TYPE_bool, False, 'truck.oilPressureWarningOn')
SCS_TELEMETRY_TRUCK_CHANNEL_oil_temperature = ScsChannel("truck.oil.temperature", SCS_VALUE_TYPE_float, False, 'truck.oilTemperature')
SCS_TELEMETRY_TRUCK_CHANNEL_parking_brake = ScsChannel("truck.brake.parking", SCS_VALUE_TYPE_bool, False, 'truck.parkBrakeOn')
SCS_TELEMETRY_TRUCK_CHANNEL_rblinker = ScsChannel("truck.rblinker", SCS_VALUE_TYPE_bool, False, 'truck.blinkerRightOn')
SCS_TELEMETRY_TRUCK_CHANNEL_retarder_level = ScsChannel("truck.brake.retarder", SCS_VALUE_TYPE_u32, False, 'truck.retarderBrake')
SCS_TELEMETRY_TRUCK_CHANNEL_speed = ScsChannel("truck.speed", SCS_VALUE_TYPE_float, False, 'truck.speed', mps_to_kph)
SCS_TELEMETRY_TRUCK_CHANNEL_water_temperature = ScsChannel("truck.water.temperature", SCS_VALUE_TYPE_float, False, 'truck.waterTemperature')
SCS_TELEMETRY_TRUCK_CHANNEL_water_temperature_warning = ScsChannel("truck.water.temperature.warning", SCS_VALUE_TYPE_bool, False, 'truck.waterTemperatureWarningOn')
SCS_TELEMETRY_TRUCK_CHANNEL_wear_cabin = ScsChannel("truck.wear.cabin", SCS_VALUE_TYPE_float, False, 'truck.wearCabin')
SCS_TELEMETRY_TRUCK_CHANNEL_wear_chassis = ScsChannel("truck.wear.chassis", SCS_VALUE_TYPE_float, False, 'truck.wearChassis')
SCS_TELEMETRY_TRUCK_CHANNEL_wear_engine = ScsChannel("truck.wear.engine", SCS_VALUE_TYPE_float, False, 'truck.wearEngine')
SCS_TELEMETRY_TRUCK_CHANNEL_wear_transmission = ScsChannel("truck.wear.transmission", SCS_VALUE_TYPE_float, False, 'truck.wearTransmission')
SCS_TELEMETRY_TRUCK_CHANNEL_wear_wheels = ScsChannel("truck.wear.wheels", SCS_VALUE_TYPE_float, False, 'truck.wearWheels')
SCS_TELEMETRY_TRUCK_CHANNEL_wheel_lift_offset = ScsChannel("truck.wheel.lift.offset", SCS_VALUE_TYPE_float, True)
SCS_TELEMETRY_TRUCK_CHANNEL_wheel_lift = ScsChannel("truck.wheel.lift", SCS_VALUE_TYPE_float, True)
SCS_TELEMETRY_TRUCK_CHANNEL_wheel_on_ground = ScsChannel("truck.wheel.on_ground", SCS_VALUE_TYPE_bool, True)
SCS_TELEMETRY_TRUCK_CHANNEL_wheel_rotation = ScsChannel("truck.wheel.rotation", SCS_VALUE_TYPE_float, True)
SCS_TELEMETRY_TRUCK_CHANNEL_wheel_steering = ScsChannel("truck.wheel.steering", SCS_VALUE_TYPE_float, True)
SCS_TELEMETRY_TRUCK_CHANNEL_wheel_substance = ScsChannel("truck.wheel.substance", SCS_VALUE_TYPE_u32, True)
SCS_TELEMETRY_TRUCK_CHANNEL_wheel_susp_deflection = ScsChannel("truck.wheel.suspension.deflection", SCS_VALUE_TYPE_float, True)
SCS_TELEMETRY_TRUCK_CHANNEL_wheel_velocity = ScsChannel("truck.wheel.angular_velocity", SCS_VALUE_TYPE_float, True)
SCS_TELEMETRY_TRUCK_CHANNEL_wipers = ScsChannel("truck.wipers", SCS_VALUE_TYPE_bool, False, 'truck.wipersOn')
SCS_TELEMETRY_TRUCK_CHANNEL_world_placement = ScsChannel("truck.world.placement", SCS_VALUE_TYPE_dplacement, False, 'truck.placement')

# SCS_TELEMETRY_CONFIG_ATTRIBUTE_adblue_capacity = ScsConfig("adblue.capacity", SCS_VALUE_TYPE_float, False, 'truck.adblueCapacity')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_adblue_warning_factor = ScsConfig("adblue.warning.factor", SCS_VALUE_TYPE_float, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_air_pressure_emergency = ScsConfig("brake.air.pressure.emergency", SCS_VALUE_TYPE_float, False, 'truck.airPressureEmergencyValue')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_air_pressure_warning = ScsConfig("brake.air.pressure.warning", SCS_VALUE_TYPE_float, False, 'truck.AirPressureWarningValue')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_battery_voltage_warning = ScsConfig("battery.voltage.warning", SCS_VALUE_TYPE_float, False, 'truck.batteryVoltageWarningValue')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_body_type = ScsConfig("body.type", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_brand_id = ScsConfig("brand_id", SCS_VALUE_TYPE_string, False, 'truck.id')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_brand = ScsConfig("brand", SCS_VALUE_TYPE_string, False, 'truck.make')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_cabin_position = ScsConfig("cabin.position", SCS_VALUE_TYPE_fvector, False, 'truck.cabin')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_cargo_accessory_id = ScsConfig("cargo.accessory.id", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_cargo_id = ScsConfig("cargo.id", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_cargo_mass = ScsConfig("cargo.mass", SCS_VALUE_TYPE_float, False, 'trailer.mass')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_cargo = ScsConfig("cargo", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_cargo_unit_count = ScsConfig("cargo.unit.count", SCS_VALUE_TYPE_u32, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_cargo_unit_mass = ScsConfig("cargo.unit.mass", SCS_VALUE_TYPE_float, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_chain_type = ScsConfig("chain.type", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_delivery_time = ScsConfig("delivery.time", SCS_VALUE_TYPE_u32, False, 'job.deadlineTime')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_destination_city_id = ScsConfig("destination.city.id", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_destination_city = ScsConfig("destination.city", SCS_VALUE_TYPE_string, False, 'job.destinationCity')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_destination_company_id = ScsConfig("destination.company.id", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_destination_company = ScsConfig("destination.company", SCS_VALUE_TYPE_string, False, 'job.destinationCompany')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_differential_ratio = ScsConfig("differential.ratio", SCS_VALUE_TYPE_float, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_forward_gear_count = ScsConfig("gears.forward", SCS_VALUE_TYPE_u32, False, 'truck.forwardGears')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_forward_ratio = ScsConfig("forward.ratio", SCS_VALUE_TYPE_float, True)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_fuel_capacity = ScsConfig("fuel.capacity", SCS_VALUE_TYPE_float, False, 'truck.fuelCapacity')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_fuel_warning_factor = ScsConfig("fuel.warning.factor", SCS_VALUE_TYPE_float, False, 'truck.fuelWarningFactor')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_head_position = ScsConfig("head.position", SCS_VALUE_TYPE_fvector, False, 'truck.head')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_hook_position = ScsConfig("hook.position", SCS_VALUE_TYPE_fvector, False, 'truck.hook')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_id = ScsConfig("id", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_income = ScsConfig("income", SCS_VALUE_TYPE_u64, False, 'job.income')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_is_cargo_loaded = ScsConfig("cargo.loaded", SCS_VALUE_TYPE_bool, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_job_market = ScsConfig("job.market", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_license_plate_country_id = ScsConfig("license.plate.country.id", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_license_plate_country = ScsConfig("license.plate.country", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_license_plate = ScsConfig("license.plate", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_name = ScsConfig("name", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_oil_pressure_warning = ScsConfig("oil.pressure.warning", SCS_VALUE_TYPE_float, False, 'truck.oilPressureWarningValue')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_retarder_step_count = ScsConfig("retarder.steps", SCS_VALUE_TYPE_u32, False, 'truck.retarderStepCount')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_reverse_gear_count = ScsConfig("gears.reverse", SCS_VALUE_TYPE_u32, False, 'truck.reverseGears')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_reverse_ratio = ScsConfig("reverse.ratio", SCS_VALUE_TYPE_float, True)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_rpm_limit = ScsConfig("rpm.limit", SCS_VALUE_TYPE_float, False, 'truck.engineRpmMax')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_selector_count = ScsConfig("selector.count", SCS_VALUE_TYPE_u32, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_shifter_type = ScsConfig("shifter.type", SCS_VALUE_TYPE_string, False, 'truck.shifterType')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_slot_gear = ScsConfig("slot.gear", SCS_VALUE_TYPE_s32, True)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_slot_handle_position = ScsConfig("slot.handle.position", SCS_VALUE_TYPE_u32, True)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_slot_selectors = ScsConfig("slot.selectors", SCS_VALUE_TYPE_u32, True)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_source_city_id = ScsConfig("source.city.id", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_source_city = ScsConfig("source.city", SCS_VALUE_TYPE_string, False, 'job.sourceCity')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_source_company_id = ScsConfig("source.company.id", SCS_VALUE_TYPE_string, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_source_company = ScsConfig("source.company", SCS_VALUE_TYPE_string, False, 'job.sourceCompany')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_special_job = ScsConfig("is.special.job", SCS_VALUE_TYPE_bool, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_water_temperature_warning = ScsConfig("water.temperature.warning", SCS_VALUE_TYPE_float, False, 'truck.waterTemperatureWarningValue')
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_wheel_count = ScsConfig("wheels.count", SCS_VALUE_TYPE_u32, False)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_wheel_liftable = ScsConfig("wheel.liftable", SCS_VALUE_TYPE_bool, True)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_wheel_position = ScsConfig("wheel.position", SCS_VALUE_TYPE_fvector, True)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_wheel_powered = ScsConfig("wheel.powered", SCS_VALUE_TYPE_bool, True)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_wheel_radius = ScsConfig("wheel.radius", SCS_VALUE_TYPE_float, True)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_wheel_simulated = ScsConfig("wheel.simulated", SCS_VALUE_TYPE_bool, True)
# SCS_TELEMETRY_CONFIG_ATTRIBUTE_wheel_steerable = ScsConfig("wheel.steerable", SCS_VALUE_TYPE_bool, True)

#SCS_TELEMETRY_CONFIG_controls = ScsConfig("controls", SCS_VALUE_TYPE_, False)
#SCS_TELEMETRY_CONFIG_hshifter = ScsConfig("hshifter", SCS_VALUE_TYPE_, False)
#SCS_TELEMETRY_CONFIG_job = ScsConfig("job", SCS_VALUE_TYPE_, False)
#SCS_TELEMETRY_CONFIG_substances = ScsConfig("substances", SCS_VALUE_TYPE_, )
#SCS_TELEMETRY_CONFIG_trailer = ScsConfig("trailer", SCS_VALUE_TYPE_, False)
#SCS_TELEMETRY_CONFIG_truck = ScsConfig("truck", SCS_VALUE_TYPE_, False)
