import pickle, sys, datetime, csv
from math import log2

TFHE_STYLE = False
PRINT_TIME = True

def sizeof_fmt(num, suffix="B"):
  for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
    if abs(num) < 1024.0:
      return f"{num:3.1f}{unit}{suffix}"
    num /= 1024.0
  return f"{num:.1f}Yi{suffix}"

def fmt_time(x):
  return (str(int(x//86400)) + "d" if x//86400 > 0 else "") + \
         (str(int((x%86400)//3600)) + "h" if (x%86400)//3600 > 0 else "") + \
         (str(int((x%3600)//60)) + "m" if (x%3600)//60 > 0 else "") + \
         ("%.1fs" % (x%60))
         

def load_data(fd):
  data = {}
  while True:
    try:
      p = pickle.load(fd)
    except EOFError:
      break
    tool = p["tool"]
    if tool not in data:
      data[tool] = {"attacks": [], "results": []}
    if p["result"]["attack"] not in data[tool]["attacks"]:
      data[tool]["attacks"].append(p["result"]["attack"])
    ## treat other estimators
    if(tool == "primal-meet-estimator" and p["result"]["estimate"] != "fail"):
      p["result"]["estimate"]["rop"] = 2**(float(p["result"]["estimate"]["cost"]))
    data[tool]["results"].append(p["result"])
  return data

from collections import OrderedDict
def gen_estimator_table(data, all_columns):
  table = {} 
  errors = []
  for res in data["results"]:
    parameters = res["parameters"]
    resources = res["resources"]
    attack = res["attack"]
    exec_time = res["exec_time"]
    estimate = res["estimate"]
    if(parameters not in table):
      table[parameters] = OrderedDict()
      table[parameters]["N"] = int(log2(parameters[0]))
      table[parameters]["hw"] = parameters[1]
      table[parameters]["q"] = int(log2(parameters[2]))
      table[parameters]["sigma"] = parameters[3]
    table[parameters][attack + "_sec"] = log2((estimate["rop"])) if estimate != "fail" else ""
    table[parameters][attack + "_time"] = fmt_time(exec_time)
    table[parameters][attack + "_umem"] = sizeof_fmt(resources.ru_maxrss*1024)
    if(estimate == "fail"):
      errors.append("Lattice Estimator failed with parameters (N,hw,q,sigma) = %s when estimating attack %s. Exception: %s\n\n" %(parameters, attack, res["exception"]))
  for t in table:
    table[t].update(all_columns)
  return table, errors
  

f = open(sys.argv[1], "rb")
env = pickle.load(f)
print(env)
all_columns = {"machine" : env["machine"],
               "Main Repo" : env["commit"],
               "SparseLWEestimator": env["submodules"][0],
               "Lattice Estimator": env["submodules"][1]}
data = load_data(f)
all_errors = []
for tool in data:
  table, errors = gen_estimator_table(data[tool], all_columns)
  all_errors += errors
  header = list((list(table.values())[0]).keys())
  header = header[:4] + sorted(header[4:-4]) + header[-4:]
  print(header)
  fout = open("out/" + tool + ".csv", "w")
  output = csv.DictWriter(fout, header)
  output.writeheader()
  for param in table:
    output.writerow(table[param])
  fout.close()

fout = open("out/errors.txt", "w")
fout.write("".join(all_errors))
fout.close()
