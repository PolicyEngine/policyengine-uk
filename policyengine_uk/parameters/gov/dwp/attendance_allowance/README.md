# Attendance Allowance

**Policy start year**: 1971. Originally introduced by the
[National Insurance (Old Persons' and Widows' Pensions and Attendance
Allowance) Act 1970][nipowpaa-1970] and made operational by the
[National Insurance (Attendance Allowance) Regulations 1971][naar-1971].

PolicyEngine UK populates `higher.yaml` and `lower.yaml` from
2015-04-01 onwards (the first year tracked in the parameter tree). For
periods before 2015 the parameter resolver returns the 2015 value —
`Microsimulation` queries on those years would compute against a value
the policy didn't actually take. Back-cast simulations needing the
1971–2014 window should backfill rates from the DWP *Abstract of
Statistics on Benefit Rates*.

Current statutory basis: [Social Security Contributions and Benefits
Act 1992 s. 64][sscba-64] and the [Social Security (Attendance
Allowance) Regulations 1991][saa-1991] (SI 1991/2740).

[nipowpaa-1970]: https://www.legislation.gov.uk/ukpga/1970/51/contents
[naar-1971]: https://www.legislation.gov.uk/uksi/1971/621
[sscba-64]: https://www.legislation.gov.uk/ukpga/1992/4/section/64
[saa-1991]: https://www.legislation.gov.uk/uksi/1991/2740
