import math
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

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


def calculate_stack_cost_arr(electrolyzer_options, system_size, cf=CAPACITY_FACTOR):
    """
    Calculate the number of stack replacements during the economic lifetime of an electrolysis unit.

    Returns:
    - int: Number of stack replacements required.
    """
    output_arr = []
    replacement_cycle_yrs = math.floor(electrolyzer_options["stack_durability"] / (cf * 8760))

    for yr in range(0,electrolyzer_options["lifetime_years"],replacement_cycle_yrs):
        replacement_cost = electrolyzer_options["stack_cost"][yr] * system_size
        # annualize cost over replacement cycle
        annualized_cost = replacement_cost / replacement_cycle_yrs
        output_arr += [annualized_cost] * replacement_cycle_yrs

    return output_arr


def total_capex(capex_per_kw, size_kw):
    """
    Calculate the total capital expenditure (CAPEX) for an electrolyzer system.

    Parameters:
    - capex_per_kw (float): Capital cost per kilowatt ($/kW)
    - size_kw (float): Size of the electrolyzer system in kilowatts (kW)
    - bop_cost (float): Cost of balance of plant equipment ($)

    Returns:
    - float: Total capital expenditure ($)
    """
    # cost_of_stack_replacements = calculate_stack_cost("PEM")

    return capex_per_kw * size_kw


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


def get_elec_cost_matrix(efficiency_data):
    ELECTRICITY_COST_CURVE = np.linspace(60, 50, efficiency_data["lifetime_years"])  # $/MWh
    # create a numpy array of electricity costs
    cost_matrix = np.zeros((len(ELECTRICITY_COST_CURVE), 100))

    for yr in range(0,efficiency_data["lifetime_years"]):
        mean = ELECTRICITY_COST_CURVE[yr]
        x = np.linspace(0.01, 1, 100)

        # Apply a log transformation to create left-skew
        log_values = np.log(x + 1)  # Log function introduces skew

        # Normalize and scale to center around yearly mean
        min_val, max_val = np.min(log_values), np.max(log_values)
        elec_prices_yr_distr = (mean + 30) - (log_values - min_val) / (max_val - min_val) * mean  # Scaling to range [30, mean + 30]

        # Calculate the cost of electricity per kg of hydrogen
        elec_prices_yr_distr = elec_prices_yr_distr * efficiency_data["efficiency_kwh_per_kg"] / 1000  # Convert to $/kg H2

        cost_matrix[yr] = elec_prices_yr_distr

    return cost_matrix

def calculate_lcoh(
        electrolyzer,  # Type of electrolyzer (e.g., "PEM", "Alkaline")
        system_size_kw, # Electrolyzer system size in kilowatts (kW)
        o_and_m_cost_per_kg,  # Fixed O&M cost per kg of H2 ($/kg)
        cf=CAPACITY_FACTOR,  # Electrolyzer utilization as a fraction (e.g., 0.8 for 80%)
        wacc=WACC,  # Weighted Average Cost of Capital (WACC) as a decimal
        include_capital=True,  # Toggle between operating vs levelized COH
):
    """
    Calculate the Cost of Hydrogen (LCOH) in $/kg H2.
    Includes a sensitivity analysis for the cost of electricity and stack cost
    """
    efficiency_data = electrolyzer_options.get(electrolyzer)

    if efficiency_data is None:
        raise ValueError(f"Electrolyzer type '{electrolyzer}' not found in the database.")

    electrolyzer_capex_per_kw = efficiency_data["capex_per_kw"]
    electrolyzer_lifetime_years = efficiency_data["lifetime_years"]

    lcoh_matrix = get_elec_cost_matrix(efficiency_data)

    # Capital cost per kg H2 (spread over the lifetime of the electrolyzer)
    if include_capital:
        capital_cost = calculate_crf(wacc, electrolyzer_lifetime_years) * total_capex(electrolyzer_capex_per_kw, system_size_kw)
    else:
        capital_cost = 0

    kg_hydrogen = calculate_annual_hydrogen_output(system_size_kw, electrolyzer)

    capital_cost_per_kg = capital_cost / kg_hydrogen

    stack_cost_arr = calculate_stack_cost_arr(efficiency_data, system_size_kw, cf)
    # divide each element by kg_hydrogen
    stack_cost_arr = [x / kg_hydrogen for x in stack_cost_arr]

    # for each year, add the stack cost to the lcoh_matrix
    for i in range(len(lcoh_matrix)):
        lcoh_matrix[i] += stack_cost_arr[i]
        lcoh_matrix[i] += o_and_m_cost_per_kg

    # duplicate the matrix
    lcoh_matrix_new = lcoh_matrix.copy()
    # subtract the tax credit from the matrix, set to 0 if negative
    tax_credit = 3
    lcoh_matrix_new = np.where(lcoh_matrix_new - tax_credit < 0, 0, lcoh_matrix_new - tax_credit)

    # weight the tax credit more heavily
    for i in range(3):
        lcoh_matrix = np.hstack((lcoh_matrix, lcoh_matrix_new))

    return lcoh_matrix


electrolyzer_options = {
    "PEM": {
        "capex_per_kw": 2000,  # $400/kW
        "efficiency_kwh_per_kg": 50,  # 50 kWh/kg H2
        "lifetime_years": 20,  # 20-year lifespan
        "stack_durability": 60000,  # 60,000 hours
        "stack_cost": 50  # $500/kW for stack replacement
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
        "lifetime_years": 10,
        "stack_durability": 25000,
        "stack_cost": np.linspace(200,50,10)  # stack cost per kW for 10 years
    }
}


LCOH = calculate_lcoh(
    electrolyzer="SOEC",  # Proton Exchange Membrane electrolyzer
    system_size_kw=1000,  # 1 MW electrolyzer
    o_and_m_cost_per_kg=1.0,  # $1/kg H2 O&M cost
)
years = np.arange(2025, 2025 + 10)  # Years from 2025 to 2034

# Create violin plot
plt.figure(figsize=(10, 6))
plt.boxplot(LCOH.T, positions=years, widths=0.6, patch_artist=True,
            boxprops=dict(facecolor='lightblue', color='blue'),
            whiskerprops=dict(color='black'),
            capprops=dict(color='black'),
            medianprops=dict(color='red'),
            showfliers=False,)

# Formatting
plt.xticks(ticks=years)
plt.xlabel("Year")
plt.ylabel("LCOH ($/kg H₂)")
plt.title("Monte Carlo Sim of Operating Cost of Hydrogen Over Time")

# Show the plot
plt.show()
