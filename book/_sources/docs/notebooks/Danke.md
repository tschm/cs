# Danke

## Conclusions

* Applying two moving averages gives a somewhat promising start (CTA 1.0)
* All positions should be scaled by the inverse price volatility (CTA 2.0)
* Using adjusted prices and scaled signals helps to address data problems
  and opens the door for statistics (CTA 3.0)
* Asset allocation can be done both in cash and risk space.
  Risk wins (Risk vs. Cash)
* The common univariate systems are closely related to diagonal Markowitz (CTA 4.0)
* Ignoring cross correlations is a bad idea (CTA 5.0)
* The smart combination of univariate trading systems is extremely helpful to
  boost returns.

## What you have not seen

* In practice you hardly can rely on the analytic solution of convex problems.
  Need solvers such as Mosek (and cvxpy).
* We optimized the expected return (in risk space). In practice it's a good idea
  to apply regularization here (Ridge, Lasso, Elastic Nets) and introduce some
  mock trading costs to tame the trading activity. A typical Markowitz system
  will trade far less than the univariate system.
* Applying Lasso/Elastic Nets regularization opens the door for sparse updates.
* The construction of more powerful signals is about the smart combination of
  standard signals by using convex programming (Index-Tracking).
* We treated all underlying markets the same, e.g. did not distinguish capacity
  or measure market share
* We did not address the problem of low volatilities, e.g. the system will
  operate with often huge positions (lack of volatility in interest rates).
  Constraints on the leverage help here...
