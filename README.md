# Market Model Design

## Actors
### Providers
  * resource limit (R)
  * computational unit (CU)
    * core GHZ   
    * unit time
    * e.g., 1 CU = (1 GHZ / 1 hour)
  * lease type (on-demand, 1 year, 3 year)
  * lease duration (D) = {0, 360, 1080}
  * lease downpayment (DP)
  * lease cost per CU (A)
  * reseller marker exchange (EX)
### Consumers
  * predicted amount of work (Wp)
  * actual amount of work (Wa)
    * unknown to consumer until completion
  * % of error between Wp and Wa
  * arrival time
  * project deadline
  * budget 

## Assumptions
  * consumer jobs are sequential "batch" computation (cannot be parallelized)
  * providers R >> total amount jobs (no scarcity)

## Questions
### Basics
  * what is the providers income gained by on-demand vs reserve instance
  * what is the providers income with the marketplace (+ a % cut of sales)
  * how much computation potential goes unused without a marketplace
  * 
### What Ifs
  * provider buys (back) from the marketplace
  * providers offers refunds
  * provider offers smaller leases (e.g., monthly, weekly)
  * provider offer finer grained CU  (e.g., minute, second)
  * consumer has unknown/dynamic requirements 
    * i.e., a website either will get 1M hits or almost nothing
  * 3rd party market w/ exchange rates between providers 
