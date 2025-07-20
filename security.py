import sys, time, itertools
from concurrent.futures import ProcessPoolExecutor, wait
import resource, pickle, tqdm
from functools import partial
from types import SimpleNamespace
from sage.all import next_prime, is_prime
## lattice estimator
from estimator.estimator.lwe import Parameters, estimate, mitm
from estimator.estimator.lwe_dual import dual_hybrid as dual_Alb17
from estimator.estimator.nd import DiscreteGaussian as dg
from estimator.estimator.nd import SparseTernary as st
CHHS19_mitm = partial(dual_Alb17, mitm_optimization=True)
## PrimalMeetEstimate
from PrimalMeetLWE.estimator.estimator import primal_may
PrimalMeetLWE_params = SimpleNamespace(M = 2**15, T = 2)
## SparseLWE-estimator
from SparseLWEestimator.estimator_sparseLWE import hybrid_primal as SparseLWEestimator_hybrid_primal, \
                                                   hybrid_dual as SparseLWEestimator_hybrid_dual, \
                                                   BKZ as SparseLWEestimator_BKZ

NUM_THREADS_ESTIMATORS = 16
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
      self.p_primalMeetLWE = [N, q, 'gaussian', sigma, hw+hw_minus_ones, PrimalMeetLWE_params.M]
      prime_q = q if is_prime(q) else next_prime(q)
      self.p_SparseLWEestimator = {"n": N, 
                                   "alpha": 8/prime_q, 
                                   "q": prime_q, 
                                   "secret_distribution":((-1,1),hw+hw_minus_ones),
                                   "reduction_cost_model": SparseLWEestimator_BKZ.sieve}

  def lattice_estimator(self, p):
    try:
      my_threads = self.threads - 3 if (self.threads - 3 > 0) else 1 # 3 threads are for the other attacks
      result = estimate(p, jobs=my_threads, add_list=[("dual_hybrid_Alb17", dual_Alb17),
                                                        ("CHHS19_mitm", CHHS19_mitm),
                                                        ("mitm_simple", mitm)],
                                                        deny_list=["arora-gb"])
    except Exception as e:
      raise e
    return result
    
  def primal_meet_estimator(self, p):
    return primal_may(p, t=PrimalMeetLWE_params.T)
  
  def sparse_LWE_Estimator_dual(self, p):
    try:
      t_ini = time.process_time()
      sec_dual = SparseLWEestimator_hybrid_dual(**p)
      t_end = time.process_time()
      sec_dual.update({"exec_time": (t_end - t_ini)})
    except Exception as e:
      sec_dual = {"sec_dual":"fail", "exception": e}
    return sec_dual

  def sparse_LWE_Estimator_primal(self, p):
    try:
      t_ini = time.process_time()
      sec_primal = SparseLWEestimator_hybrid_primal(**p)
      t_end = time.process_time()
      sec_primal.update({"exec_time": (t_end - t_ini)})
    except Exception as e:
      sec_primal = {"sec_primal":"fail", "exception": e}
    return sec_primal
  
  def run_all(self):
    exec = ProcessPoolExecutor(max_workers=self.threads)
    tasks = []
    tasks.append(exec.submit(self.lattice_estimator, self.p))
    tasks.append(exec.submit(self.primal_meet_estimator, self.p_primalMeetLWE))
    tasks.append(exec.submit(self.sparse_LWE_Estimator_dual, self.p_SparseLWEestimator))
    tasks.append(exec.submit(self.sparse_LWE_Estimator_primal, self.p_SparseLWEestimator))
    wait(tasks)
    return [i.result() for i in tasks]
  
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

