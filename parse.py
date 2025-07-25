import pickle, sys, datetime
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
         

sec = ['dual_hybrid', 'dual', 'bdd_mitm_hybrid', 'bdd_hybrid', 'bdd', 'usvp', 'bkw', 'mitm_simple',  'dual_hybrid_Alb17', 'CHHS19_mitm']
others = ["primal_meet", "sparse_dual"]
if(TFHE_STYLE): print("N", "hw", "q", "ternary", sep="\t", end="\t")
else: print("N", "hw", "q", "sigma", sep="\t", end="\t")
sec_times = sum(map(lambda x: [x, x + '_time'], sec), start=[])
others_times = sum(map(lambda x: [x, x + '_time'], others), start=[])
if(PRINT_TIME):
  print(*sec_times, sep="\t", end="\t")
  print(*others_times, sep="\t", end="\t")
else:
  print(*sec, sep="\t", end="\t")
  print(*others, sep="\t", end="\t")
print("time", "cpu time", "mem", sep="\t")
f = open(sys.argv[1], "rb")
while True:
  try:
    p = pickle.load(f)
  except EOFError:
    break
  params = p["params"] 
  if(TFHE_STYLE): print(int((params[0])), params[1], int((params[2])), params[4], sep="\t", end="\t")
  else: print(int(log2(params[0])), params[1], int(log2(params[2])), params[3], sep="\t", end="\t")
  for est in p["est"]:
    if(est["tool"] == "lattice-estimator"): 
      result = est["result"]
      for atk in sec:
        if(type(result) is dict and atk in result):
          if(PRINT_TIME): print("%.2f\t%s" %(log2(result[atk]["rop"]), fmt_time(result[atk]["exec_time"])), end="\t")
          else: print("%.2f" %(log2(result[atk]["rop"])), end="\t")
        else:
          if(PRINT_TIME): print("-\t-", end="\t")
          else: print("-", end="\t")
    elif(est["tool"] == "primal-meet-estimator"):
      result = est["result"]
      if(result["estimate"] != "fail"):
        print("%.2f\t%s" % (result["estimate"]["cost"], fmt_time(result["exec_time"])), end="\t")
      else:
        print("-\t%s" % fmt_time(result["exec_time"]), end="\t")
    elif(est["tool"] == "sparse-lwe-estimator"):
      result = est["result"]
      if(result["estimate"] != "fail"):
        security = log2(int(result["estimate"]["rop"]))
        print("%.2f\t%s" % (security, fmt_time(result["exec_time"])), end="\t")
      else:
        print("-\t%s" % fmt_time(result["exec_time"]), end="\t")
  # resources
  res = p["resources"]
  print("%s\t%s\t%s" % (fmt_time(res["wall-time"]), fmt_time(res["all"].ru_utime), sizeof_fmt(res["all"].ru_maxrss*1024)))