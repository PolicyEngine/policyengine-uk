# Constant Attendance Allowance

**Policy start year**: 1948. Introduced under the
[National Insurance (Industrial Injuries) Act 1946][niia-1946] as one
of the supplements to the Industrial Injuries Disablement benefit
package, payable from 5 July 1948 (the appointed day for the post-war
social security reforms).

PolicyEngine UK populates the per-day-rate parameters
(`full_day_rate`, `intermediate_rate`, `part_day_rate`,
`exceptional_rate`) from 2015-04-01 onwards. For periods before 2015
the parameter resolver returns the 2015 value — `Microsimulation`
queries on those years would compute against a value the policy didn't
actually take.

Current statutory basis: [Social Security Contributions and Benefits
Act 1992 s. 104][sscba-104] and the [Social Security (General Benefit)
Regulations 1982][gbr-1982] (SI 1982/1408).

[niia-1946]: https://www.legislation.gov.uk/ukpga/1946/62/contents
[sscba-104]: https://www.legislation.gov.uk/ukpga/1992/4/section/104
[gbr-1982]: https://www.legislation.gov.uk/uksi/1982/1408
