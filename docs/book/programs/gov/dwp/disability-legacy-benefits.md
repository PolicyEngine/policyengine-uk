# DLA and Severe Disablement Allowance

PolicyEngine UK models two **legacy** DWP disability benefits alongside
the current PIP (covered in [its own page](./PIP.ipynb)):

- **Disability Living Allowance (DLA)** — closed to new working-age
  claims in April 2013 but still paid to existing recipients and to
  children under 16.
- **Severe Disablement Allowance (SDA)** — closed to new claims in
  April 2001 and replaced by Incapacity Benefit / ESA / Universal Credit;
  legacy recipients continue to receive it.

Both are non-means-tested and are added directly into the
`household_benefits` aggregate (via the `dla` and `sda` variables in its
`adds` list).

## Disability Living Allowance

DLA has two independent components, each with its own band structure:

| Component | Bands | Variable | Parameter file |
|-----------|-------|----------|----------------|
| Mobility (`dla_m`) | Higher / Lower / None | `dla_m` | `gov/dwp/dla/mobility/{higher,lower}.yaml` |
| Self-care (`dla_sc`) | Higher / Middle / Lower / None | `dla_sc` | `gov/dwp/dla/self_care/{higher,middle,lower}.yaml` |

A claimant's band on each component is taken from the dataset inputs
`dla_m_category` and `dla_sc_category` (each an enum on `Person`). For
each band the formula multiplies the published **weekly** rate by
`WEEKS_IN_YEAR` to produce an annual amount; the combined award is

```python
dla = dla_sc + dla_m
```

i.e. a recipient on the higher mobility rate and the higher self-care
rate stacks both, producing the maximum DLA award.

### Eligibility (informational)

PolicyEngine doesn't re-derive eligibility for DLA because the dataset
records categorical band assignments rather than the underlying
self-care / mobility activity scores. New claims have been routed to
PIP for working-age claimants since April 2013, so the population that
remains on DLA is overwhelmingly:

- children under 16 (DLA continues to be available),
- adults who were on DLA on 8 April 2013 and have not yet been migrated
  to PIP at reassessment.

Migration to PIP is handled by the calibration step in
`policyengine-uk-data`, not by a re-derivation here.

## Severe Disablement Allowance

SDA is a single weekly flat-rate payment, exposed as the variable `sda`.
Eligibility is treated as binary and read straight from the dataset
input `sda_reported`:

```python
sda = (sda_reported > 0) * gov.dwp.sda.maximum * WEEKS_IN_YEAR
```

The model assumes recipients are entitled to the **maximum** age-related
addition. This is a deliberate simplification: SDA was closed to new
claims in 2001 and the remaining caseload is small and old enough that
nearly all recipients qualify for the highest age-related addition.

## References

- DLA primary statute: [Social Security Contributions and Benefits Act 1992 s. 71](https://www.legislation.gov.uk/ukpga/1992/4/section/71).
- DLA closure to new working-age claims: [Welfare Reform Act 2012 Part 4](https://www.legislation.gov.uk/ukpga/2012/5/part/4) and [The Personal Independence Payment (Transitional Provisions) Regulations 2013 (SI 2013/387)](https://www.legislation.gov.uk/uksi/2013/387/contents).
- DWP, [Disability Living Allowance: detailed information](https://www.gov.uk/disability-living-allowance).
- SDA primary statute: [Social Security Contributions and Benefits Act 1992 s. 68](https://www.legislation.gov.uk/ukpga/1992/4/section/68) (since repealed for new claims).
- SDA closure to new claims: [The Welfare Reform and Pensions Act 1999 s. 65](https://www.legislation.gov.uk/ukpga/1999/30/section/65).
- DWP, [DLA and SDA caseload statistics](https://www.gov.uk/government/collections/disability-living-allowance-statistics) used by `policyengine-uk-data` for calibration.
