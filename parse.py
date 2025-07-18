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
if(TFHE_STYLE): print("N", "hw", "q", "ternary", sep="\t", end="\t")
else: print("N", "hw", "q", "sigma", sep="\t", end="\t")
print(*sec, sep="\t", end="\t")
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
  est = p["est"]
  for atk in sec:
    if(type(est) is dict and atk in est):
      if(PRINT_TIME): print(" %.2f (%s)" %(log2(est[atk]["rop"]), fmt_time(est[atk]["exec_time"])), end="\t")
      else: print("%.2f" %(log2(est[atk]["rop"])), end="\t")
    else:
      print("-", end="\t")
  res = p["resources"]
  print("%s\t%s\t%s" % (fmt_time(res["wall-time"]), fmt_time(res["all"].ru_utime), sizeof_fmt(res["all"].ru_maxrss*1024)))