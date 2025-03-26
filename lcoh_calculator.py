import math
import matplotlib.pyplot as plt
import numpy as np

LIFETIME = 10  # years
WACC = 0.1  # 10% discount rate
CAPACITY_FACTOR = 0.8  # 80% capacity factor

def calculate_wacc(DF, RROE, IR, TR, inflation):
    """
    Calculate the Weighted Average Cost of Capital (WACC).

    Parameters:
    DF (float): Debt fraction (0 to 1)
    RROE (float): Required return on equity (as a decimal)
    IR (float): Interest rate on debt (as a decimal)
    TR (float): Corporate tax rate (as a decimal)
    inflation (float): Inflation rate (as a decimal)

    # Example usage
    DF = 0.5  # 50% debt financing
    RROE = 0.08  # 8% return on equity
    IR = 0.05  # 5% interest rate on debt
    TR = 0.25  # 25% corporate tax rate
    inflation = 0.02  # 2% inflation rate
    lifetime = 20  # Asset lifetime in years

    Returns:
    float: WACC as a decimal
    """
    wacc = (1 + (1 - DF) * ((1 + RROE) * (1 + inflation) - 1) +
            DF * ((1 + IR) * (1 + inflation) - 1) * (1 - TR)) / (1 + inflation) - 1
    return wacc


def calculate_crf(WACC, lifetime):
    """
    Calculate the Capital Recovery Factor (CRF).

    Parameters:
    WACC (float): Weighted Average Cost of Capital (as a decimal)
    lifetime (int): Economic lifetime of the asset (years)

    Returns:
    float: CRF as a decimal
    """
    if WACC == 0:  # To prevent division by zero
        return 1 / lifetime
    crf = WACC / (1 - (1 / ((1 + WACC) ** lifetime)))
    return crf


def calculate_stack_cost(electrolyzer, cf=CAPACITY_FACTOR):
    """
    Calculate the number of stack replacements during the economic lifetime of an electrolysis unit.

    Returns:
    - int: Number of stack replacements required.
    """
    total_operating_hours = electrolyzer_options[electrolyzer]["lifetime_years"] * cf * 8760  # 8760 hours in a year
    stack_replacements = math.floor(total_operating_hours / electrolyzer_options[electrolyzer]["stack_durability"])  # Round down

    return stack_replacements * electrolyzer_options[electrolyzer]["stack_cost"]


def total_capex(capex_per_kw, size_kw, bop_cost):
    """
    Calculate the total capital expenditure (CAPEX) for an electrolyzer system.

    Parameters:
    - capex_per_kw (float): Capital cost per kilowatt ($/kW)
    - size_kw (float): Size of the electrolyzer system in kilowatts (kW)
    - bop_cost (float): Cost of balance of plant equipment ($)

    Returns:
    - float: Total capital expenditure ($)
    """
    cost_of_stack_replacements = calculate_stack_cost("PEM")

    return capex_per_kw * size_kw + bop_cost + cost_of_stack_replacements

def calculate_lcoh(
        electricity_cost_per_mwh,  # Electricity cost in $/MWh
        electrolyzer,  # Type of electrolyzer (e.g., "PEM", "Alkaline")
        system_size_kw, # Electrolyzer system size in kilowatts (kW)
        o_and_m_cost_per_kg,  # Fixed O&M cost per kg of H2 ($/kg)
        cf=CAPACITY_FACTOR,  # Electrolyzer utilization as a fraction (e.g., 0.8 for 80%)
        wacc=WACC,  # Weighted Average Cost of Capital (WACC) as a decimal
        tax_credit=False,  # Whether to include the federal tax credit
):
    """
    Calculate the Levelized Cost of Hydrogen (LCOH) in $/kg H2.
    """

    # Convert electricity cost to $/kWh
    electricity_cost_per_kwh = electricity_cost_per_mwh / 1000

    efficiency_data = electrolyzer_options.get(electrolyzer)

    if efficiency_data is None:
        raise ValueError(f"Electrolyzer type '{electrolyzer}' not found in the database.")

    electrolyzer_capex_per_kw = efficiency_data["capex_per_kw"]
    electrolyzer_efficiency_kwh_per_kg = efficiency_data["efficiency_kwh_per_kg"]
    electrolyzer_lifetime_years = efficiency_data["lifetime_years"]

    # Electricity cost per kg H2
    electricity_cost_per_kg = electricity_cost_per_kwh * electrolyzer_efficiency_kwh_per_kg

    # Capital cost per kg H2 (spread over the lifetime of the electrolyzer)
    capital_cost = calculate_crf(wacc, electrolyzer_lifetime_years) * total_capex(electrolyzer_capex_per_kw, system_size_kw, 0)

    kg_hydrogen = cf * 8760 * system_size_kw / electrolyzer_efficiency_kwh_per_kg

    capital_cost_per_kg = capital_cost / kg_hydrogen

    # Total cost per kg H2
    lcoh = electricity_cost_per_kg + o_and_m_cost_per_kg

    if tax_credit:
        lcoh = lcoh - 3

    return round(lcoh, 2)


def calculate_annual_hydrogen_output(system_size_kw, electrolyzer, capacity_factor=CAPACITY_FACTOR):
    """
    Calculate the annual hydrogen production (kg/year) for a given electrolyzer system.

    Parameters:
    - system_size_kw (float): Size of the electrolyzer system in kilowatts (kW)
    - electrolyzer (str): Type of electrolyzer (e.g., "PEM", "Alkaline")
    - capacity_factor (float): Capacity factor of the electrolyzer (default: 0.8 or 80%)

    Returns:
    - float: Annual hydrogen production in kilograms (kg/year)
    """
    efficiency_data = electrolyzer_options.get(electrolyzer)

    if efficiency_data is None:
        raise ValueError(f"Electrolyzer type '{electrolyzer}' not found in the database.")

    efficiency_kwh_per_kg = efficiency_data["efficiency_kwh_per_kg"]

    # Total annual energy input (kWh)
    annual_energy_input_kwh = system_size_kw * capacity_factor * 8760

    # Annual hydrogen output (kg)
    annual_hydrogen_output = annual_energy_input_kwh / efficiency_kwh_per_kg

    return annual_hydrogen_output


electrolyzer_options = {
    "PEM": {
        "capex_per_kw": 2000,  # $400/kW
        "efficiency_kwh_per_kg": 50,  # 50 kWh/kg H2
        "lifetime_years": 20,  # 20-year lifespan
        "stack_durability": 60000,  # 60,000 hours
        "stack_cost": 5000  # $5000 per stack replacement
    },
    "Alkaline": {
        "capex_per_kw": 300,  # $300/kW
        "efficiency_kwh_per_kg": 55,  # 55 kWh/kg H2
        "lifetime_years": 30,  # 30-year lifespan
        "stack_durability": 80000,  # 80,000 hours
        "stack_cost": 4000  # $4000 per stack replacement
    },
    "SOEC": {
        "capex_per_kw": 2500,  # $2000/kW + $500/kW BoP cost
        "efficiency_kwh_per_kg": 37.5,  # https://www.bloomenergy.com/bloomelectrolyzer/
        "lifetime_years": 20,
        "stack_durability": 25000,
        "stack_cost": 5000
    }
}


LCOH = calculate_lcoh(
    electricity_cost_per_mwh=50,  # $80/MWh
    electrolyzer="SOEC",  # Proton Exchange Membrane electrolyzer
    system_size_kw=1000,  # 1 MW electrolyzer
    o_and_m_cost_per_kg=1.0,  # $1/kg H2 O&M cost
)

# create a numpy array of electricity costs
electric_costs = np.linspace(35, 100, 30)
lcoh_values = []

for cost in electric_costs:
    lcoh = calculate_lcoh(
        electricity_cost_per_mwh=cost,
        electrolyzer="SOEC",
        system_size_kw=1000,
        o_and_m_cost_per_kg=1.0,
    )
    if lcoh - 3 < 0:
        lcoh = 0
    else:
        lcoh -= 3

    lcoh_values.append(lcoh)

# graph lcoh values
plt.plot(electric_costs, lcoh_values)
plt.xlabel("Electricity Cost ($/MWh)")
plt.ylabel("LCOH ($/kg)")
plt.title("LCOH vs. Electricity Cost")
plt.show()
