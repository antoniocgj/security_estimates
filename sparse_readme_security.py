from security import *

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
  opts = (True, False)
  return list(map(lambda x: x + opts, params))

if __name__ == "__main__":
  params = gen_param_list_sparse_readme()
  print(params)
  mp_run_params(params)

