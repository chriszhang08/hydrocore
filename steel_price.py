from lcoh_calculator import calculate_lcoh, calculate_annual_hydrogen_output
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, FactorRange, Whisker
from bokeh.palettes import Category10
import pandas as pd
import numpy as np

LCOH = calculate_lcoh(
    electricity_cost_per_mwh=50,  # $80/MWh
    electrolyzer="PEM",  # Proton Exchange Membrane electrolyzer
    system_size_kw=1000,  # 1 MW electrolyzer
    o_and_m_cost_per_kg=1.0,  # $1/kg H2 O&M cost
)

kgs_hydrogen = calculate_annual_hydrogen_output(system_size_kw=1000, electrolyzer="PEM")

# define inputs
hrc_steel_price = 950  # $950/ton
production_capacity_yr = 3000  # 3,000 tons/year
capacity_factor = 0.9  # 90% capacity factor
green_premium = 0.1  # 10% premium for green steel
kg_h2_per_ton_steel = 50  # 50 kg H2 per ton of steel
kwh_per_ton_steel = 700  # 700 kWh per ton of steel to run EAF
price_per_kwh = 0.05  # $0.05/kWh
capex_per_ton_steel = 500  # $500/ton steel
iron_ore_price = 500  # $500/ton
labor_price_per_ton = 50  # $50/ton

# calculate the cost of electricity per tonne of steel
cost_of_electricity_per_ton_steel = kwh_per_ton_steel * price_per_kwh

# calculate the cost of hydrogen per tonne of steel
cost_of_hydrogen_per_ton_steel = kg_h2_per_ton_steel * LCOH

print(cost_of_electricity_per_ton_steel, cost_of_hydrogen_per_ton_steel)

# print kgs hydrogen
print(kgs_hydrogen)


# Cost data (replace with your actual values)
dri_eaf_breakdown = {
    "Iron Ore": 500,
    "Labor": 50,
    "Electricity": 150,  # Example: $150/ton
    "Energy": 200,       # Hydrogen cost
    "upper": 220,
    "lower": 180,
}

bf_bof_breakdown = {
    "Iron Ore": 500,
    "Labor": 50,
    "Electricity": 120,  # Example: $120/ton (cheaper electricity)
    "Energy": 120,         # No hydrogen cost
    "upper": 140,
    "lower": 100,
}

categories = list(dri_eaf_breakdown.keys())[:-2]
steel_types = ["Green Steel", "Regular Steel"]

# Create a DataFrame for stacking
data = {
    "categories": categories,
    "Green Steel": list(dri_eaf_breakdown.values())[:-2],
    "Regular Steel": list(bf_bof_breakdown.values())[:-2],
}
df = pd.DataFrame(data)

df.set_index("categories", inplace=True)
df = df.T
df.reset_index(inplace=True)

# Color palette
colors = Category10[4][:len(categories)]  # Adjust palette as needed

# Create figure
p = figure(
    x_range=FactorRange(*steel_types),
    height=400,
    width=600,
    title="Green Steel vs. Regular Steel Cost Breakdown",
    toolbar_location=None,
    y_axis_label="Cost per Ton ($)",
)

error_source = ColumnDataSource({
    'steel_type': steel_types,
    'upper': [
        sum(v for k,v in dri_eaf_breakdown.items() if k not in ('upper', 'lower', "Energy")) + dri_eaf_breakdown['upper'],
        sum(v for k,v in bf_bof_breakdown.items() if k not in ('upper', 'lower', "Energy")) + bf_bof_breakdown['upper']],
    'lower': [
        sum(v for k,v in dri_eaf_breakdown.items() if k not in ('upper', 'lower', "Energy")) + dri_eaf_breakdown['lower'],
        sum(v for k,v in bf_bof_breakdown.items() if k not in ('upper', 'lower', "Energy")) + bf_bof_breakdown['lower']],
})

# Add error whiskers
whisker = Whisker(
    base='steel_type',
    upper='upper',
    lower='lower',
    level='annotation',
    source=error_source,
    line_width=2,
    line_color='black'
)
p.add_layout(whisker)

# Plot stacked bars
p.vbar_stack(
    stackers=categories,
    x='index',
    width=0.5,
    color=colors,
    source=df,
    legend_label=categories,
)

# Customize plot
p.y_range.start = 0
p.x_range.range_padding = 0.1
p.xgrid.grid_line_color = None
p.axis.minor_tick_line_color = None
p.outline_line_color = None
p.legend.title = "Cost Components"
p.legend.location = "top_right"

# Show plot
show(p)