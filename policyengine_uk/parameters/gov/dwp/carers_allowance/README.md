# Carer's Allowance

**Policy start year**: 1976. Introduced as **Invalid Care Allowance**
under [The Social Security (Invalid Care Allowance) Regulations 1976][icaa-regs]
(SI 1976/409), made under section 37 of the [Social Security Act 1975][ssa-1975].
Renamed **Carer's Allowance** in 2003.

PolicyEngine UK populates `rate.yaml` from 2015-04-01 onwards (the first
year tracked in the parameter tree). For periods before 2015 the
parameter resolver returns the 2015 value — `Microsimulation` queries
on those years would compute against a value the policy didn't actually
take. If back-cast simulations through the 1976–2014 window are needed,
the missing rates should be backfilled from the DWP *Abstract of
Statistics on Benefit Rates*.

Current statutory basis: [Social Security Contributions and Benefits
Act 1992 s. 70][sscba-70].

[icaa-regs]: https://www.legislation.gov.uk/uksi/1976/409
[ssa-1975]: https://www.legislation.gov.uk/ukpga/1975/14/contents
[sscba-70]: https://www.legislation.gov.uk/ukpga/1992/4/section/70
