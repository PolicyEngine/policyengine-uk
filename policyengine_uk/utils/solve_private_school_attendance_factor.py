from policyengine_uk import Microsimulation
from policyengine_core.reforms import Reform
from tqdm import tqdm

# Initialize variables to track the best private_school_factor and its result
best_factor = None
smallest_difference = float("inf")

# Loop over values of private_school_factor from 0.7 to 0.8 in steps of 0.01
for factor in tqdm([round(x * 0.01, 2) for x in range(70, 91)]):
    # Define the reform with the current private_school_factor value
    reform = {
        "gov.contrib.labour.private_school_vat": {
            "2024-01-01.2100-12-31": 0.2
        },
        "gov.simulation.private_school_vat.private_school_factor": {
            "2024-01-01.2100-12-31": factor
        },
    }

    # Run the reformed microsimulation
    reformed = Microsimulation(
        reform=reform,
    )
    reformed.baseline_simulation.get_holder(
        "attends_private_school"
    ).delete_arrays()

    # Calculate the number of students attending private school in thousands
    private_school_attendance = (
        reformed.calculate("attends_private_school", period=2025).sum() / 1e3
    )

    # Compare the result with 550 and track the best value
    difference = abs(private_school_attendance - 550)
    if difference < smallest_difference:
        smallest_difference = difference
        best_factor = factor

# Report the best private_school_factor
print(
    f"The best private_school_factor is {best_factor} with a difference of {smallest_difference}"
)
# The best private_school_factor is 0.77 with a difference of 1.3427231160653719
