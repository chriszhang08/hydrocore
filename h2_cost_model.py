import numpy as np
import math

LIFETIME = 10  # years
WACC = 0.1  # 10% discount rate
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


def calculate_stack_replacements(economic_lifetime_years, operating_hours_per_year, stack_durability_hours):
    """
    Calculate the number of stack replacements during the economic lifetime of an electrolysis unit.

    Parameters:
    - economic_lifetime_years (int or float): Expected lifetime of the electrolyzer in years.
    - operating_hours_per_year (int or float): Number of hours the electrolyzer operates per year.
    - stack_durability_hours (int or float): Expected durability of the electrolyzer stack in hours.

    Returns:
    - int: Number of stack replacements required.
    """
    total_operating_hours = economic_lifetime_years * operating_hours_per_year
    stack_replacements = math.floor(total_operating_hours / stack_durability_hours)  # Round down

    return stack_replacements

# Example usage
economic_lifetime = 20  # years
operating_hours_per_year = 8000  # hours per year
stack_durability = 60000  # hours

replacements = calculate_stack_replacements(economic_lifetime, operating_hours_per_year, stack_durability)
print(f"Number of stack replacements required: {replacements}")


def net_present_value(cost_of_capital, yearly_hydrogen_output):
    """
    Calculate the Net Present Value (NPV) of a hydrogen production project.

    Parameters:
    - cost_of_capital (float): Discount rate or cost of capital.
    - hydrogen_output (int): total hydrogen output over lifetime of the project.

    Returns:
    - float: Net Present Value of the project.
    """
    # todo

def calculate_hydrogen_cost(
        electricity_cost_per_mwh,  # Electricity cost in $/MWh
        electrolyzer,  # Type of electrolyzer (e.g., "PEM", "Alkaline")
        capacity_factor,  # Electrolyzer utilization as a fraction (e.g., 0.8 for 80%)
        o_and_m_cost_per_kg,  # Fixed O&M cost per kg of H2 ($/kg)
        discount_rate  # Weighted Average Cost of Capital (WACC %)
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

    # Annualized capital cost using Capital Recovery Factor (CRF)
    # crf = net_present_value(# TODO)

    # Capital cost per kg H2 (spread over the lifetime of the electrolyzer)
    capital_cost_per_kg = (electrolyzer_capex_per_kw * crf) / \
                          (electrolyzer_efficiency_kwh_per_kg * capacity_factor * 8760)  # Annual operating hours

    # Total cost per kg H2
    lcoh = capital_cost_per_kg + electricity_cost_per_kg + o_and_m_cost_per_kg

    return round(lcoh, 2)


electrolyzer_options = {
    "PEM": {
        "capex_per_kw": 400,  # $400/kW
        "efficiency_kwh_per_kg": 50,  # 50 kWh/kg H2
        "lifetime_years": 20  # 20-year lifespan
    },
    "Alkaline": {
        "capex_per_kw": 300,  # $300/kW
        "efficiency_kwh_per_kg": 55,  # 55 kWh/kg H2
        "lifetime_years": 30  # 30-year lifespan
    }
}


# Example usage with realistic assumptions
lcoh = calculate_hydrogen_cost(
    electricity_cost_per_mwh=50,  # $50/MWh
    electrolyzer="PEM",  # Proton Exchange Membrane electrolyzer
    capacity_factor=1,  # 80% utilization
    o_and_m_cost_per_kg=1.0,  # $1/kg H2 O&M cost
    discount_rate=0.08  # 8% WACC
)

print(f"Estimated Levelized Cost of Hydrogen: ${lcoh}/kg H₂")
