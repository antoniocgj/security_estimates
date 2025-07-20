from security import *

def gen_param_list(ternary=True):
  # list of params
  dimensions = [2048, 4096, 8192]
  hw = list(range(42, 20, -1))
  moduli = [i for i in range(15, 27)]
  params = itertools.product(dimensions, hw, moduli)
  # common options
  # {sigma=3.19, ternary=True, tfhe_like=False, threads=1} 
  opts = (3.19, ternary, True, NUM_THREADS_ESTIMATORS)
  return list(map(lambda x: x + opts, params))

def gen_param_list_ccs():
  # list of params
  params = [(2048, 256, 44, 0, True, True, NUM_THREADS_ESTIMATORS),
            (4096, 256, 44, 0, True, True, NUM_THREADS_ESTIMATORS),
            (8192, 256, 44, 0, True, True, NUM_THREADS_ESTIMATORS),
            (2048, 512, 50, 0, True, True, NUM_THREADS_ESTIMATORS),
            (8192, 512, 51, 0, True, True, NUM_THREADS_ESTIMATORS),
            (2048, 39, 15, 0, False, True, NUM_THREADS_ESTIMATORS),
            (2048, 42, 17, 0, False, True, NUM_THREADS_ESTIMATORS),
            (4096, 33, 21, 0, False, True, NUM_THREADS_ESTIMATORS),
            (8192, 27, 21, 0, False, True, NUM_THREADS_ESTIMATORS),
            (4096, 34, 24, 0, False, True, NUM_THREADS_ESTIMATORS),
            (8192, 28, 24, 0, False, True, NUM_THREADS_ESTIMATORS),
            (2048, 35, 15, 0, True, True, NUM_THREADS_ESTIMATORS),
            (2048, 38, 17, 0, True, True, NUM_THREADS_ESTIMATORS),
            (4096, 30, 21, 0, True, True, NUM_THREADS_ESTIMATORS),
            (8192, 25, 21, 0, True, True, NUM_THREADS_ESTIMATORS),
            (4096, 32, 24, 0, True, True, NUM_THREADS_ESTIMATORS),
            (8192, 26, 23, 0, True, True, NUM_THREADS_ESTIMATORS),
            ]
  return params

if __name__ == "__main__":
  # params = gen_param_list()
  # params += gen_param_list(False)
  params = gen_param_list_ccs()
  print(params)
  mp_run_params(params)