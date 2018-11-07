import subprocess
import json
import copy

def is_scarf():
    uname = subprocess.check_output(['uname', '-a'])
    return 'scarf.rl.ac.uk' in uname

class Config(object):
    def __init__(self):
        self.run_number = 10052
        self.n_jobs = 3
        if is_scarf():
            self.n_jobs = 1000
        self.n_events = 1001 # 101
        self.n_events_per_spill = 100 # 100
        self.simulation_geometry = {
            "source_dir":None,
            "reference_dir":None,
            "target_dir":None,
            "tracker":"tku",
            "position":{"x":0., "y":0., "z":0.},
            "rotation":{"x":0., "y":0., "z":0.},
            "scale":{"E2":1., "E1":1., "C":1.},
            "density":2.0, #g/cm^3
            "silicon_fraction":0.0,
        }
        self.tof0_offset = -25.4 # note analysis script tof0_offset adds time; here we want to undo that offset so sign is negative
        self.tof1_offset = 0.
        self.beam_z_position = 13965.0 # 18836.8+8.
        self.reconstruction_geometry = copy.deepcopy(self.simulation_geometry)
        self.beam_input_file = "beams/"+str(self.run_number)+"/tku_5.json"
        self.config_in = "config.in"
        self.job_name = "normal"
        self.run = {
            "extra_args":["--maximum_number_of_steps", "200000"], # command line arguments for MAUS
            "delta_t":30, # seconds between each poll
            "max_t":60*60*5, # seconds before job is hard killed
            "n_procs":min(self.n_jobs, 150), # number of concurrent processes
        }

def build_config(run_number, tracker, job_name, iteration, position = None, rotation = None, density = None, currents = None):
    config = Config()
    config.iteration_number = iteration
    print "Setting config iteration number", config.iteration_number
    config.run_number = run_number
    config.beam_input_file = "beams/"+str(run_number)+"/tku_5.json"
    config.job_name = tracker+"_"+job_name
    if position == None:
        position = {"x":0., "y":0., "z":0.}
    if rotation == None:
        rotation = {"x":0., "y":0., "z":0.}
    if density == None:
        density = 2.0
    if currents == None:
        currents = {"E2":1., "E1":1., "C":1.}
    config.simulation_geometry["tracker"] = tracker
    config.simulation_geometry["position"] = position
    config.simulation_geometry["rotation"] = rotation
    config.simulation_geometry["density"] = density
    config.simulation_geometry["scale"] = currents
    print "Building config", job_name
    print json.dumps(config.simulation_geometry, indent = 2)
    return config
