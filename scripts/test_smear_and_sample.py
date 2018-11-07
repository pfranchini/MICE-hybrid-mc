import json
import unittest
import ROOT
import numpy

import libMausCpp
import MapPySmearAndSample
import maus_cpp.converter

def main():
    src_name = ""
    tgt_name = ""
    tgt_nevts = 1000
    SmearAndSample()

class TestSmearAndSample(unittest.TestCase):
    def setUp(self):
        self.input_file = '/tmp/smear_test.in'
        self.generate_source()
        self.config = {
            "smear_and_sample":{
                "n_events_per_spill":100,
                "input_file":self.input_file,
                "n_momentum_slices":10,
                "momentum_min":135.,
                "momentum_max":145.,
                "seed":0,
                "z_position":15065.,
            }
        }

    def tearDown(self):
        pass

    def test_birth(self):
        config_str = json.dumps(self.config)
        map_smear = MapPySmearAndSample.MapPySmearAndSample()
        map_smear.birth(config_str)

    def test_process(self):
        config_str = json.dumps(self.config)
        map_smear = MapPySmearAndSample.MapPySmearAndSample()
        map_smear.birth(config_str)
        fout = open("test_smear_and_sample.json", "w")
        for i in range(2):
            data = {}
            data["spill_number"] = i+1
            data["run_number"] = 999
            data["daq_event_type"] = "physics_event"
            data["maus_event_type"] = "Spill"
            data = maus_cpp.converter.data_repr(data)
            map_smear.process(data)
            print >> fout, json.dumps(maus_cpp.converter.json_repr(data), indent=2)

    def generate_source(self):
        cov = numpy.array([
                  [1000.,   0.,     0.,     0.,     0.,],
                  [0.,    600.,     0.,     0.,     0.,],
                  [0.,      0.,  1000.,     0.,     0.,],
                  [0.,      0.,     0.,   600.,     0.,],
                  [0.,      0.,     0.,     0.,   100.,],
              ])
        mean = numpy.array([0., 0., 0., 0., 140.])
        src_dist = numpy.random.multivariate_normal(mean, cov, 1000)
        fsrc = open(self.input_file, 'w')
        fsrc.write("{}\n") #metadata
        for item in src_dist:
            psv = item.tolist()
            psv.append(numpy.random.normal(item[4]/120-25., 0.5))
            psv.append(numpy.random.normal(item[4]/100+0.1, 0.5))
            fsrc.write(json.dumps(psv)+"\n")
        fsrc.close()
        return

        SmearAndSample(src_fname, tgt_fname, "icool_for003", tgt_nevents)

        fin = open(tgt_fname)
        tgt_bunch = Bunch.new_from_read_builtin("icool_for003", tgt_fname)
        tgt_dist = [[hit[key] for key in SmearAndSample.keys] for hit in tgt_bunch]

        if len(tgt_dist) != tgt_nevents:
            raise RuntimeError("Fail")

        tgt_dist = numpy.array(tgt_dist).transpose()
        numpy.set_printoptions(precision=8, linewidth=1000)
        print numpy.cov(src_dist.transpose())
        print
        print numpy.cov(tgt_dist)



if __name__ == "__main__":
    unittest.main()
