import os
import sys
import copy
import time
import shutil

import xboa.common

import murgle_geometry
import smear_and_sample

class Environment(object):
    def __init__(self, config):
        self.config = config
        self.run_number = config.run_number
        self.n_jobs = config.n_jobs
        self.simulation_geometry = config.simulation_geometry
        self.reconstruction_geometry = config.reconstruction_geometry
        self.beam_input_file = config.beam_input_file
        self.beam_z_position = config.beam_z_position
        self.n_events = config.n_events
        self.n_events_per_spill = config.n_events_per_spill
        self.job_name = config.job_name

    def setup_environment(self):
        self.make_dirs()
        self.make_geometry("simulation")
        self.make_geometry("reconstruction")
        #self.make_beams() ... moved to simulation mapper
        self.make_config("simulation")
        self.make_config("reconstruction")
        # note that because of the way geometry works, we have to make links
        # at run time for each geometry (geometry_xxxxx/<filename> is hardcoded
        # into the geometry)

    def get_geometry_ref_dir(self):
        dir_name =  "geometry_"+str(self.run_number)
        return dir_name

    def get_geometry_filename(self):
        filename = self.get_geometry_ref_dir()+"/ParentGeometryFile.dat"
        return filename

    def get_output_geometry_filename(self, prefix):
        geometry = os.path.split(self.get_geometry_filename())[0]
        return self.get_dir_root()+'/'+prefix+'_'+geometry

    def copy_geometry(self, prefix):
        geometry_src_root = os.getcwd()+"/work/"
        geometry = os.path.split(self.get_geometry_filename())[0]
        target = self.get_output_geometry_filename(prefix)
        shutil.copytree(geometry_src_root+geometry, target)

    def make_geometry(self, tag):
        self.copy_geometry(tag)
        geometry_dict = self.simulation_geometry
        geometry_dict["source_dir"] = self.get_output_geometry_filename(tag)
        geometry_dict["target_dir"] = self.get_output_geometry_filename(tag)
        geometry_dict["reference_dir"] = self.get_geometry_ref_dir()
        murgler = murgle_geometry.GeometryMurgler(geometry_dict)
        murgler.murgle()

    def get_beam_filename(self, index):
        return os.getcwd()+"/"+self.beam_input_file

    def make_beams(self):
        smear = smear_and_sample.SmearAndSample(self.beam_input_file, "", self.beam_format, self.n_events)
        for i in range(self.n_jobs):
            filename = self.get_beam_filename(i)
            smear.write(self.config.beam_z_position, i, filename)

    def get_config(self, index, prefix):
        return self.get_dir_name(index)+"/"+prefix+"_config.py"

    def make_config(self, prefix):
        print "Making config from", self.config.config_in
        for index in range(self.n_jobs):
            subs = {
                "__geometry_filename__":self.get_geometry_filename(),
                "__run__":str(self.run_number),
                "__seed__":str(index),
                "__beam_filename__":self.get_beam_filename(index),
                "__n_spills__":self.n_events/self.n_events_per_spill+1,
                "__output_filename__":"maus_"+prefix+".root",
                "__z_position__":self.beam_z_position,
                "__tof1_offset__":self.config.tof1_offset,
                "__tof0_offset__":self.config.tof0_offset,
            }
            xboa.common.substitute(self.config.config_in, self.get_config(index, prefix), subs)
  
    def get_dir_preroot(self):
        return os.getcwd()+"/work/"+str(self.run_number)+"_systematics_v"+str(self.config.iteration_number)

    def get_dir_root(self):
        return self.get_dir_preroot()+"/"+self.job_name+"/"

    def get_dir_name(self, job_id):
        job_name = str(job_id).rjust(4, '0')
        return self.get_dir_root()+"/"+job_name

    def make_dirs(self):
        print "Setting up dirs with name", self.get_dir_root()
        for i in range(self.n_jobs):
            os.makedirs(self.get_dir_name(i))
            print i,
            sys.stdout.flush()
        pause = min(self.n_jobs, 10)
        print "\nPause for", pause, "seconds to give OS a chance to finish"
        for i in range(pause):
            time.sleep(1)
            print i+1,
            sys.stdout.flush()
        print
