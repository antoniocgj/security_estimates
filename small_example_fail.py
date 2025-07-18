from estimator.estimator.lwe import Parameters, estimate, primal_usvp, dual, primal_bdd, mitm, primal_hybrid, Estimate
from estimator.estimator.lwe_dual import dual_hybrid as dual_Alb17
from estimator.estimator.nd import DiscreteGaussian as dg
from estimator.estimator.nd import SparseTernary as st
from functools import partial
CHHS19_mitm = partial(dual_Alb17, mitm_optimization=True)

p = Parameters(32768, 79228162514264337593543950336, st(16, n=32768, m=16), dg(3.2))

print(primal_bdd(p)) # ValueError: Incorrect bounds 32768 > 13290.