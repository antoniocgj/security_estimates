import sys, time, itertools, os, platform, subprocess, re, io
from concurrent.futures import ProcessPoolExecutor, wait, as_completed
import resource, pickle, tqdm
from functools import partial
from types import SimpleNamespace
from sage.all import next_prime, is_prime
## lattice estimator
from estimator.estimator.lwe import Parameters, estimate, mitm, dual_hybrid, dual, primal_bdd, primal_hybrid, primal_usvp, coded_bkw 
from estimator.estimator.lwe_dual import dual_hybrid as dual_Alb17
from estimator.estimator.nd import DiscreteGaussian as dg
from estimator.estimator.nd import SparseTernary as st
CHHS19_mitm = partial(dual_Alb17, mitm_optimization=True)
bdd_hybrid = partial(primal_hybrid, mitm=False, babai=False)
estimator_list_of_attacks = {dual_hybrid: "dual_hybrid", primal_hybrid: "primal_hybrid", primal_usvp: "primal_usvp", coded_bkw: "coded_bkw", bdd_hybrid: "bdd_hybrid", dual: "dual", primal_bdd: "primal_bdd", dual_Alb17: "dual_Alb17", CHHS19_mitm: "CHHS19_mitm", mitm: "mitm"}
## PrimalMeetEstimate
from PrimalMeetLWE.estimator.estimator import primal_may
PrimalMeetLWE_params = SimpleNamespace(M = 2**15, T = 2)
## SparseLWE-estimator
from SparseLWEestimator.estimator_sparseLWE import hybrid_primal as SparseLWEestimator_hybrid_primal, \
                                                   hybrid_dual as SparseLWEestimator_hybrid_dual, \
                                                   BKZ as SparseLWEestimator_BKZ

NUM_THREADS = 96

class RunLatticeEstimator:
  def __init__(self, N, hw, q, sigma=3.19, ternary=True, tfhe_like=False):
    self.parameters = (N, hw, q, sigma)
    hw_minus_ones = 0
    if(ternary):
      hw_minus_ones = (hw+1)//2
      hw = hw//2
    if(tfhe_like):
      self.p = Parameters(N, 2**64, st(hw, n=N, m=hw_minus_ones), dg((2**64)/q))
    else:
      self.p = Parameters(N, q, st(hw, n=N, m=hw_minus_ones), dg(sigma))
      self.p_primalMeetLWE = [N, q, 'gaussian', sigma, hw+hw_minus_ones, PrimalMeetLWE_params.M]
      prime_q = q if is_prime(q) else next_prime(q)
      self.p_SparseLWEestimator = {"n": N, 
                                   "alpha": 8/prime_q, 
                                   "q": prime_q, 
                                   "secret_distribution":((-1,1),hw+hw_minus_ones),
                                   "reduction_cost_model": SparseLWEestimator_BKZ.sieve}

  def add_common(self, result):
    result["resources"] = resource.getrusage(resource.RUSAGE_SELF)
    result["parameters"] = self.parameters

  def lattice_estimator(self, f, p, name):
    t_ini = time.process_time()
    try:
      est = f(p)
      result = {"attack": name, "estimate": est}
    except Exception as e:
      result = {"attack": name, "estimate": "fail", "exception": e}
    t_end = time.process_time()
    result["exec_time"] = (t_end - t_ini)
    self.add_common(result)
    return {"tool": "lattice-estimator" , "result": result}
  
  def primal_meet_estimator(self, p):
    t_ini = time.process_time()
    try:
      est = primal_may(p, t=PrimalMeetLWE_params.T)
      result = {"attack": "primal", "estimate": est}
    except Exception as e:
      result = {"attack": "primal", "estimate": "fail", "exception": e}
    t_end = time.process_time()
    result["exec_time"] = (t_end - t_ini)
    self.add_common(result)
    return {"tool": "primal-meet-estimator", "result": result}

  
  def sparse_LWE_Estimator_dual(self, p):
    t_ini = time.process_time()
    try:
      sec_dual = SparseLWEestimator_hybrid_dual(**p)
      result = {"attack": "dual", "estimate": sec_dual}
    except Exception as e:
      result = {"attack": "dual", "estimate": "fail", "exception": e}
    t_end = time.process_time()
    result["exec_time"] = (t_end - t_ini)
    self.add_common(result)
    return {"tool": "sparse-lwe-estimator", "result": result}

  def sparse_LWE_Estimator_primal(self, p):
    t_ini = time.process_time()
    try:
      sec_primal = SparseLWEestimator_hybrid_primal(**p)
      result = {"attack": "primal", "estimate": sec_primal}
    except Exception as e:
      result = {"attack": "primal", "estimate": "fail", "exception": e}
    t_end = time.process_time()
    result["exec_time"] = (t_end - t_ini)
    self.add_common(result)
    return {"tool": "sparse-lwe-estimator", "result": result}
  
  def run_all(self, processPool):
    tasks = []
    for atk in estimator_list_of_attacks:
      tasks.append(processPool.submit(self.lattice_estimator, atk, self.p, estimator_list_of_attacks[atk]))
    tasks.append(processPool.submit(self.primal_meet_estimator, self.p_primalMeetLWE))
    tasks.append(processPool.submit(self.sparse_LWE_Estimator_dual, self.p_SparseLWEestimator))
    # tasks.append(processPool.submit(self.sparse_LWE_Estimator_primal, self.p_SparseLWEestimator))
    return tasks
  
def get_processor_name():
  if platform.system() == "Windows":
    return platform.processor()
  elif platform.system() == "Darwin":
    os.environ['PATH'] = os.environ['PATH'] + os.pathsep + '/usr/sbin'
    command ="sysctl -n machdep.cpu.brand_string"
    return subprocess.check_output(command).strip()
  elif platform.system() == "Linux":
    command = "cat /proc/cpuinfo"
    all_info = subprocess.check_output(command, shell=True).decode().strip()
    for line in all_info.split("\n"):
      if "model name" in line:
        return re.sub( ".*model name.*:", "", line,1)
  return ""

def get_git_info():
  return {"commit": subprocess.check_output("git rev-parse HEAD", shell=True).decode().strip(), 
          "submodules" : subprocess.check_output("git submodule status", shell=True).decode().strip().split("\n")}
  
def run_param(p, estimate_pool, fd):
  est = RunLatticeEstimator(*p)
  def write_results(result):
    pickle.dump(result.result(), fd)

  tasks = est.run_all(estimate_pool)
  list(map(lambda t: t.add_done_callback(write_results), tasks))
  return tasks


def mp_run_params(p_list):
  print_file = io.StringIO()
  print_file = open("out/debug_output.txt", "w")
  def redirect_output():
    sys.stdout = print_file

  estimate_pool = ProcessPoolExecutor(max_workers=NUM_THREADS, initializer=redirect_output)
  f = open("out/results.pyobj", "wb")
  env = {"machine": get_processor_name()}
  env.update(get_git_info())
  pickle.dump(env, f)

  _run_param = partial(run_param, estimate_pool=estimate_pool, fd=f)
  all_tasks = sum(map(_run_param, p_list), start=[])
  bar = tqdm.tqdm(total=len(all_tasks))
  for _ in as_completed(all_tasks):
    bar.update()
  f.close()

