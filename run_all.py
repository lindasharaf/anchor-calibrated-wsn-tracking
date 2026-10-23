"""
run_all.py - the full experiment (paper Section V). Runs every scenario many times with
different random seeds and saves all summaries to results.pkl.

    python run_all.py            # 50 runs per configuration (about 15 minutes on 2 cores)
    python run_all.py 5          # quick check with 5 runs
"""
import sys, pickle, time
from multiprocessing import Pool, cpu_count
from method import simulate

CONFIGS = [('S1', 4), ('S2', 4), ('S3', 4), ('S4', 4),     # main scenarios, 16 anchors
           ('S1', 3), ('S2', 3), ('S1', 5), ('S2', 5)]     # S5: density, 9 and 25 anchors

def job(args):
    sc, per_row, seed = args
    return (sc, per_row, seed), simulate(sc, seed=seed, per_row=per_row)

if __name__ == '__main__':
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    jobs = [(sc, pr, s) for sc, pr in CONFIGS for s in range(runs)]
    t0 = time.time()
    with Pool(cpu_count()) as p:
        results = dict(p.map(job, jobs, chunksize=4))
    pickle.dump(results, open('results.pkl', 'wb'))
    print(f'{len(results)} runs saved to results.pkl in {time.time() - t0:.0f}s')
