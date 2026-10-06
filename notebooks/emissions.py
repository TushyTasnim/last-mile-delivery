"""Emission model for emissions-aware vehicle routing.

Exported from 03_emissions_model.ipynb and imported by Notebooks 4 and 5.
"""

GRAVITY = 9.81                  # m/s^2
DIESEL_CO2_KG_PER_L = 2.68      # kg CO2 released per litre burned
DIESEL_ENERGY_MJ_PER_L = 35.8   # energy in one litre of diesel
DRIVETRAIN_EFFICIENCY = 0.35    # share of fuel energy that reaches the wheels

# Vehicle -- must match Notebook 1.
CURB_WEIGHT_KG = 1500           # empty van
CAPACITY_KG = 600               # max payload

# Calibration assumptions -- tested in Notebook 5's sensitivity analysis.
FUEL_EMPTY_L_PER_100KM = 11.0   # empty van at the reference speed
LOAD_SENSITIVITY = 0.25         # +25% fuel when fully loaded
REFERENCE_SPEED_KMH = 60.0      # speed the fuel figure applies to


def speed_factor(speed_kmh):
    """Fuel-per-km multiplier relative to 60 km/h. U-shaped, lowest near 44 km/h."""
    A, B, C = 250.0, 5.0, 0.0015

    def f(v):
        return A / v + B + C * v * v

    return f(speed_kmh) / f(REFERENCE_SPEED_KMH)


def fuel_l_per_km(payload_kg, speed_kmh):
    """Litres of diesel per km for a given payload and speed."""
    load_ratio = payload_kg / CAPACITY_KG   # 0 = empty, 1 = full
    base_l_per_km = FUEL_EMPTY_L_PER_100KM / 100.0
    return base_l_per_km * (1 + LOAD_SENSITIVITY * load_ratio) * speed_factor(speed_kmh)


def co2_kg(distance_m, duration_s, payload_kg, climb_m=0.0):
    """kg of CO2 for driving one arc with `payload_kg` on board."""
    distance_km = distance_m / 1000.0

    # 1. Rolling term: fuel rate x distance x CO2 per litre.
    if duration_s > 0:
        speed_kmh = distance_km / (duration_s / 3600.0)
    else:
        speed_kmh = REFERENCE_SPEED_KMH   # avoid dividing by zero
    rolling_co2 = fuel_l_per_km(payload_kg, speed_kmh) * distance_km * DIESEL_CO2_KG_PER_L

    # 2. Gradient term: work m*g*h -> litres of fuel -> CO2.
    #    Downhill earns nothing back (no regenerative braking).
    climb_m = max(climb_m, 0.0)
    total_mass_kg = CURB_WEIGHT_KG + payload_kg
    work_joules = total_mass_kg * GRAVITY * climb_m
    fuel_litres = work_joules / (DRIVETRAIN_EFFICIENCY * DIESEL_ENERGY_MJ_PER_L * 1e6)
    gradient_co2 = fuel_litres * DIESEL_CO2_KG_PER_L

    return rolling_co2 + gradient_co2
