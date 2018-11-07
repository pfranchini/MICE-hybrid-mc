bsub -W 240:00 -n 1 -q scarf-ibis -o run_all.log -e run_all.log \
    python scripts/run_all.py
