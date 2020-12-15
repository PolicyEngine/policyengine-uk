# Individual Simulations

Individual-focused simulations calculate variables for hypothetical, manually specified people, benefit units and households. This can be useful for different applications:
- Calculating taxes and benefits for a specific group
- Evaluating how the computed variables change when one property is varied

## Example: calculating the effective marginal tax rate schedule

In this example, we specify the input data being a lone parent with one child. By setting the ```earnings``` field to vary (by default, between £0 and £200k) we can plot the line graph of earnings against the effective marginal tax rate. 

Note that ```universal_credit_reported``` is required here - the UK is currently phasing out legacy benefits and phasing in the new Universal Credit benefit - we decide which to simulate based on reported receipt. 

from openfisca_uk import IndividualSim
import plotly.express as px

# define the simulation and populate it

sim = IndividualSim()
sim.add_person(name="parent", age=24, is_benunit_head=True)
sim.add_person(name="child", age=2)
sim.add_benunit(adults=["parent"], children=["child"], universal_credit_reported=True)
sim.add_household(adults=["parent"], children=["child"])

# replicate the simulation along the earnings dimension

sim.vary("earnings", min=0, max=200000, step=100)

# retrive the arrays of earnings and marginal tax rates

earnings = sim.calc("earnings", target="parent")
mtr = sim.calc_mtr(target="parent")

# plot the results

fig = px.line(x=earnings, y=mtr, title="Effective marginal tax schedule")
fig.update_layout(yaxis_tickformat="%", xaxis_tickprefix="£", xaxis_title="Earnings", yaxis_title="Marginal tax rate")
fig.show()