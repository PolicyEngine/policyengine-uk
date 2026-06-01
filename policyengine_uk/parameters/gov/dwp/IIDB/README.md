# Industrial Injuries Disablement Benefit

**Policy start year**: 1948. Originally **Industrial Injuries
Disablement Pension** under the [National Insurance (Industrial
Injuries) Act 1946][niia-1946], operative from 5 July 1948. Renamed
*Disablement Benefit* in 1986 and folded into the broader Industrial
Injuries Scheme.

PolicyEngine UK populates `maximum.yaml` from 2015-04-01 onwards. The
benefit is paid in 10 percent increments of the maximum rate
(`gov.dwp.IIDB.maximum`) reflecting the assessed disablement
percentage; the model treats the reported amount as derived from
`iidb_reported` rather than re-derived from a percentage. For periods
before 2015 the parameter resolver returns the 2015 value —
`Microsimulation` queries on those years would compute against a value
the policy didn't actually take.

Current statutory basis: [Social Security Contributions and Benefits
Act 1992 Part V][sscba-part-v] (in particular s. 103) and the [Social
Security (Industrial Injuries) (Prescribed Diseases) Regulations
1985][prescribed-diseases-1985] (SI 1985/967).

[niia-1946]: https://www.legislation.gov.uk/ukpga/1946/62/contents
[sscba-part-v]: https://www.legislation.gov.uk/ukpga/1992/4/part/V
[prescribed-diseases-1985]: https://www.legislation.gov.uk/uksi/1985/967
