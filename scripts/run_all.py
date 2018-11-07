import math
import environment
import run
import config
import copy
import glob

def do_one(config):
    my_env = environment.Environment(config)
    my_env.setup_environment()
    my_run = run.Run(my_env)
    my_run.prefix = "simulation"
    my_run.run_many()
    my_run.prefix = "reconstruction"
    my_run.run_many()
    #my_run.clear('maus_simulation.root') # delete the pure mc (to save space)

def get_iteration():
    key = '_systematics_v'
    valid_folders = glob.glob('*'+key+'*')
    iteration_number = 101
    for folder in valid_folders:
        index = folder.find(key)+len(key)
        iteration_number = max(iteration_number, int(folder[index:]))
    return iteration_number

def main():
    one_mrad = math.degrees(0.001)
    iteration = get_iteration()
    print "Running systematics mc iteration", iteration
    for run in [10069]: #, 10064, 10051, 10052,]: #
        my_config = config.build_config(run, "tku", "base", iteration)
        do_one(my_config)
        continue
        for tracker in ["tku", "tkd"]:
            rotation = {"x":one_mrad*3, "y":0., "z":0.}
            my_config = config.build_config(run, tracker, "rot_plus", iteration, rotation = rotation)
            do_one(my_config)
            position = {"x":3., "y":0., "z":0.}
            my_config = config.build_config(run, tracker, "pos_plus", iteration, position = position)
            do_one(my_config)
            scale = {"C":1.03, "E2":1.05, "E1":1.05}
            base_scale = {"E2":1.0, "E1":1.0, "C":1.0}
            for key in scale.keys():
                base_scale[key] = scale[key]
                name = "scale_"+key+"_plus"
                my_config = config.build_config(run, tracker, name, iteration, currents = base_scale)
                base_scale[key] = 1.0
                do_one(my_config)
            my_config = config.build_config(run, tracker, "density_plus", iteration, density = 3.0)
            do_one(my_config)

if __name__ == "__main__":
    main()
