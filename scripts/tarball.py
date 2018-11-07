import glob
import os
import subprocess

dir_list = sorted(glob.glob("*_v1"))
for i, a_dir in enumerate(dir_list):
    target = a_dir+".tar.gz"
    if os.path.exists(target):
        print "Skipping", target
        continue
    command = ["tar", "-czf", target, a_dir]
    print "Doing", i+1, "of", len(dir_list), "with command", command
    proc = subprocess.Popen(command)
    proc.wait()
