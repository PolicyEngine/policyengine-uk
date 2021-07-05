from time import time
import yaml

def test_speed():
    start_time = time()
    from openfisca_uk import Microsimulation
    import_time = time()
    sim = Microsimulation()
    init_time = time()
    sim.calc("household_net_income")
    calc_time = time()
    output = dict(
        import_model = import_time - start_time,
        init_model = init_time - start_time,
        run_time = calc_time - start_time,
        total_time = calc_time - start_time
    )
    for key in output:
        output[key] = f"{round(output[key], 2)}s"
    print(yaml.dump(output))

test_speed()