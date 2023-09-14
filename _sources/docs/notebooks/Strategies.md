# Implement a hedge fund strategy in 10 lines

## A short history

* Summer 2017: Lunch with Cyrus Fazel (CEO, Swissborg)
* Motivation to implement a CTA strategy with less than 10 lines of code
* Published CTA 3.0 on [LinkedIn](https://www.linkedin.com/pulse/implement-cta-less-than-10-lines-code-thomas-schmelzer/)
* Today:
  * Attempt to help demystifying quantitative hedge funds and
    their level of sophistication.
  * Introduce convex optimization for CTAs.

## The underlying paper

Baz, Jamil and Granger, Nicolas M. and Harvey, Campbell R.
and Le Roux, Nicolas and Rattray, Sandy,
Dissecting Investment Strategies in the Cross Section
and Time Series (December 4, 2015).
Available at SSRN: <https://ssrn.com/abstract=2695101> or
<http://dx.doi.org/10.2139/ssrn.2695101>

## CTA - Commodity Trading Advisor

* Man AHL
* Winton Capital
* Aspect Capital
* BlueTrend (part of BlueCrest, today Systematica)
* Solaise Capital
* Ashenden Capital
* ...
* Barclays CTA Index

## Rules of the game

* Use 50 liquid futures (including *frozen* orange juice)
* Orange Juice future:

  * 150$ FPV (full point value)
  * 300 pts (September 2023)
  * 45000$ cashposition
  * 6000$ initial margin.

* Adjust them by ratio for rolling 3 days prior to expiry
* Rebalance daily without any delay
* Assume no transaction costs
* Assume fractional position sizes. All positions are given
  as target cash positions.
* We start every day with 100m USD AUM. We accumulate profits.
  We do not compound returns.
  We like our profits positive, homoscedastic and not too leptokurtic.

## Optimization

* We barely scratch the surface of the area.
* We use analytical solutions to convex problems.
* We use the [Seven Sins in Portfolio Optimisation](https://arxiv.org/abs/1310.3396)
  paper.

## Software

* We use the open source [TinyCTA](https://pypi.org/project/TinyCTA/) package.
* All material has been merged into a [JupyterBook](https://jupyterbook.org/en/stable/intro.html).
* Move to [Marimo](https://github.com/marimo-team/marimo) in preparation
* Binder may or may not work.

For brave souls:

```bash
git clone git@github.com:tschm/cs.git
cd cs
make jupyter
```
