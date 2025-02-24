import pandas
import pandas as pd
import numpy as np

data = pandas.read_csv("assets/mining_gas_demand.csv")

# drop all columns that start with symbol
data = data.drop(data.filter(regex='^Symbol').columns, axis=1)

# create an expense dataframe with columns 1, 3, 5, 7, 9, 11
expense = data.iloc[:, [3, 5, 7, 9, 11]]
usage = data.iloc[:, [2, 4, 6, 8, 10]]


def clean_columns(data):
    # rename columns by splitting the column name by comma and taking the first one
    data.columns = data.columns.str.split(',').str[0]

    # take out all the commas in the string number values
    data = data.replace({',': ''}, regex=True)

    # convert all the values in the dataframe to numeric except the first colujmn
    data = data.apply(pd.to_numeric)

    # add a new row that sums up all the values in each column
    data.loc['Total', :] = data.sum(axis=0)

    return data


expense = clean_columns(expense)
usage = clean_columns(usage)

# mulitply expense by 1000
expense = expense * 1000

usage = usage[['Gasoline - motor', 'Heavy Fuel Oil', 'Diesel fuel', 'Natural gas']]
usage_total_mat = usage.loc['Total', :].to_numpy()

# %%
# lado energy density
energy_density = pd.read_csv("assets/energy_density.csv")

# obtain energy density numpy matrix
energy_matrix = energy_density.iloc[:, 2:].to_numpy()

# divide first 3 rows by 1000
energy_matrix[0:3, :] = energy_matrix[0:3, :] / 1000

# convert Gj to kWh
energy_matrix = energy_matrix * 277.778

# multiply the energy density matrix with the data dataframe
result = energy_matrix[:, 0] * usage_total_mat

# sum all the values in the result
result = np.sum(result)

# %%
# load in the fuel charge data
fuel_charge = pandas.read_csv("assets/fuel_charge.csv")

# create a new dataframe of just the gasoline, diesel, natural gas, and heavy fuel oil
fuel_charge = fuel_charge.loc[[8, 9, 12, 15], :]

# extract all columns except the first 2 as a numpy matrix
fuel_charge = fuel_charge.iloc[:, 2:].to_numpy()

# %%
# multiply the values in the data dataframe with the fuel charge dataframe
tax_levy = fuel_charge * usage_total_mat[:, np.newaxis]

tax_levy_series = tax_levy.sum(axis=0)

# %%
base_cost = expense.loc['Total']
# duplicate the base cost 8 times
base_cost = pd.concat([base_cost] * 8, axis=1)

# rename the columns to 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030
base_cost.columns = [2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030]

# append the tax levy to the base cost
base_cost.loc['Fuel Charge Tax'] = tax_levy_series

# sum the fuel costs
base_cost.loc['All Fuels'] = base_cost.loc['Natural gas'] + base_cost.loc['Gasoline - motor'] + base_cost.loc[
    'Diesel fuel'] + base_cost.loc['Heavy Fuel Oil']

# reorder the rows to be Electricity, Tax Levy
base_cost = base_cost.reindex(['All Fuels', 'Fuel Charge Tax'])

# convert to million cad
base_cost = base_cost / 1000000

# %%
# calculate cost of substituting carbon fuels with hydrogen

# first calculate kwh potential of total usage
usage_total_kwh = usage_total_mat @ energy_matrix

kgs_hydrogen = usage_total_kwh / 33.33

# cost of hydrogen
cost_hydrogen = kgs_hydrogen * 1.5

# create a hydrogen cost dataframe
cost_hydrogen_df = pd.concat([pd.Series(cost_hydrogen)] * 8, axis=1)
cost_hydrogen_df.columns = [2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030]

# set the index of cost_hydrogen_df Hydrogen, Electricity
cost_hydrogen_df.index = ['Hydrogen']

# convert to million cad
cost_hydrogen_df = cost_hydrogen_df / 1000000

# %%
import matplotlib.pyplot as plt
import numpy as np

# Define colors
colors = {
    'All Fuels': '#BCAB79',
    'Hydrogen': '#2978A0',
    'Fuel Charge Tax': '#315659'
}
# Define bar width
bar_width = 0.4

# Get the number of categories (columns)
categories = base_cost.columns
x = np.arange(len(categories))  # X positions for bars

# Initialize figure and axis
fig, ax = plt.subplots()

# Plot base_cost as stacked bars
bottom_base = np.zeros(len(categories))  # Initialize bottom position
for label in base_cost.index:
    ax.bar(
        x - bar_width / 2,
        base_cost.loc[label],
        width=bar_width,
        label=f'{label}',
        bottom=bottom_base,
        color=colors.get(label, 'gray')  # Use the color from the dictionary, default to gray if missing
    )
    bottom_base += base_cost.loc[label].values  # Stack bars

# Plot cost_hydrogen_df as stacked bars, shifted to the right
bottom_hydrogen = np.zeros(len(categories))  # Initialize bottom position
for label in cost_hydrogen_df.index:
    ax.bar(
        x + bar_width / 2,
        cost_hydrogen_df.loc[label],
        width=bar_width,
        label=f'{label}',
        bottom=bottom_hydrogen,
        color=colors.get(label, 'gray')  # Use the color from the dictionary, default to gray if missing
    )
    bottom_hydrogen += cost_hydrogen_df.loc[label].values  # Stack bars

# Labels and title
ax.set_xticks(x)
ax.set_xticklabels(categories)
plt.title("Fuel Cost Comparison")
plt.ylabel("Cost (in million CAD)")
plt.xlabel("Year")
plt.legend()

plt.show()

#%%
# calculate cumulative savings of using hydrogen
cumulative_savings = base_cost.loc['All Fuels'] + base_cost.loc['Fuel Charge Tax'] - cost_hydrogen_df.loc['Hydrogen']