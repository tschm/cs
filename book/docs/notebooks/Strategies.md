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

* Use 50 liquid futures (including frozen orange juice)
* Adjust them by ratio for rolling
* Rebalance daily without any delay
* Assume no transaction costs
* Assume fractional position sizes. All positions are given
  as target cash positions.

## Optimization

* We barely scratch the surface of the area.
* We use analytical solutions to convex problems.
* We use the [Seven Sins in Portfolio Optimisation](https://arxiv.org/abs/1310.3396)
  paper.
