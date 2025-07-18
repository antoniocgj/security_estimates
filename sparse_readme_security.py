import sys, time, itertools
from estimator.estimator.lwe import Parameters, estimate, primal_usvp, dual, primal_bdd, mitm, primal_hybrid, Estimate
from estimator.estimator.lwe_dual import dual_hybrid as dual_Alb17
from estimator.estimator.nd import DiscreteGaussian as dg
from estimator.estimator.nd import SparseTernary as st
from functools import partial
from concurrent.futures import ProcessPoolExecutor
CHHS19_mitm = partial(dual_Alb17, mitm_optimization=True)
import resource, pickle, tqdm

NUM_THREADS_ESTIMATOR = 8
NUM_THREADS_PARAMS = 96

class RunLatticeEstimator:
  def __init__(self, N, hw, q, sigma=3.19, ternary=True, tfhe_like=False, threads=1):
    self.threads = threads
    hw_minus_ones = 0
    if(ternary):
      hw_minus_ones = (hw+1)//2
      hw = hw//2
    if(tfhe_like):
      self.p = Parameters(N, 2**64, st(hw, n=N, m=hw_minus_ones), dg(2**(64-q)))
    else:
      self.p = Parameters(N, q, st(hw, n=N, m=hw_minus_ones), dg(sigma))

  def my_estimate(self, p):
    return estimate(p, jobs=self.threads, add_list=[("dual_hybrid_Alb17", dual_Alb17),
                                                    ("CHHS19_mitm", CHHS19_mitm),
                                                    ("mitm_simple", mitm)],
                                                    deny_list=["arora-gb"])
    
  def run_all(self):
    try:
      sec = self.my_estimate(self.p)
      return sec
    except Exception as e:
      raise e
      return e
  
def run_param(p):
  est = RunLatticeEstimator(*p)
  t_ini = time.time()
  result = est.run_all()
  t_end = time.time()
  resources = resource.getrusage(resource.RUSAGE_CHILDREN)
  return {"params": p, "resources":  {"wall-time": (t_end - t_ini), "all": resources}, "est": result}

def mp_run_params(p_list):
  exec = ProcessPoolExecutor(max_workers=NUM_THREADS_PARAMS)
  f = open("results.pyobj", "wb")
  bar = tqdm.tqdm(total=len(p_list))
  for res in exec.map(run_param, p_list):
    pickle.dump(res, f)
    bar.update()
    f.flush()
  f.close()

def gen_param_list_sparse_readme():
  # list of params
  params = []
  import csv
  with open(sys.argv[1], newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for p in reader:
      params.append((2**int(p["log2(N)"]), int(p["HW"]), 2**int(p["log2(ctmod)"]), float(p["σ"])))
  # common options
  # {ternary=True, tfhe_like=False, threads=1} 
  opts = (True, False, NUM_THREADS_ESTIMATOR)
  return list(map(lambda x: x + opts, params))

if __name__ == "__main__":
  params = gen_param_list_sparse_readme()
  print(params)
  mp_run_params(params)

