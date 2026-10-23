"""Robustness check: the same four scenarios on the repo's second trajectory (tra2)."""
import pickle, numpy as np
from multiprocessing import Pool
from method import simulate
SC = ['S1', 'S2', 'S3', 'S4']
def job(a):
    sc, seed = a
    return (sc, seed), simulate(sc, seed=seed, path_name='tra2')
if __name__ == '__main__':
    with Pool(2) as p:
        res = dict(p.map(job, [(s, k) for s in SC for k in range(50)]))
    pickle.dump(res, open('results_path2.pkl', 'wb'))
    for m in ['KF', 'SURVEY', 'ORACLE', 'N']:
        row = []
        for sc in SC:
            part = 2 if sc == 'S1' else 1
            c = np.mean([r[m]['cov'][part] for (s, _), r in res.items() if s == sc])
            rad = np.mean([r[m]['rad'][part] for (s, _), r in res.items() if s == sc])
            row.append(f'{100*c:5.1f}/{rad:4.1f}')
        print(f'{m:7s}', '  '.join(row))
    s4 = [r for (s, _), r in res.items() if s == 'S4']
    print('fault detected', sum(r['detect_delay'] is not None for r in s4), '/50, delays',
          sorted(set(r['detect_delay'] for r in s4 if r['detect_delay'] is not None)),
          '| false alarms', sum(r['false_alarm'] for r in res.values()))
