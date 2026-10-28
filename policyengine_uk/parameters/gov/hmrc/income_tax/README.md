# Income Tax

## Dividend bands

[Income Tax Act 2007 s. 13](https://www.legislation.gov.uk/ukpga/2007/3/section/13)
ties the dividend rates to the corresponding UK taxable-income bands, including
when determining the dividend bands for a Scottish taxpayer.
[Section 16](https://www.legislation.gov.uk/ukpga/2007/3/section/16) places
dividends above other income. The dividend nil-rate amount uses band capacity;
it does not reduce income when determining the remaining capacity in each band.

The dated dividend scale records these basic-rate limits:

| Tax year beginning 6 April | Basic-rate limit | Authority |
| --- | ---: | --- |
| 2016 | £32,000 | [Finance (No. 2) Act 2015 s. 6](https://www.legislation.gov.uk/ukpga/2015/33/section/6/enacted) |
| 2017 | £33,500 | [Finance Act 2016 s. 2](https://www.legislation.gov.uk/ukpga/2016/24/section/2/enacted) |
| 2018 | £34,500 | [SI 2017/1184 art 2](https://www.legislation.gov.uk/uksi/2017/1184/article/2/made) |
| 2019 and 2020 | £37,500 | [Finance Act 2019 s. 5](https://www.legislation.gov.uk/ukpga/2019/1/section/5/enacted) |
| From 2021 | £37,700 | [SI 2021/111 art 2](https://www.legislation.gov.uk/uksi/2021/111/article/2/made) |

The additional-rate threshold falls from £150,000 to £125,140 from 6 April 2023
under [Finance Act 2023 s. 6](https://www.legislation.gov.uk/ukpga/2023/1/section/6/enacted).
These limits apply after allowances. For example, in 2025, £49,000 of pay uses
£36,430 of taxable band capacity after the £12,570 Personal Allowance. Of a
further £2,000 of dividends, £1,270 fits in the basic band, including the £500
dividend nil-rate amount. The charge is £770 × 8.75% + £730 × 33.75% = £313.75.

The threshold history does not certify the pre-2016 dividend-tax-credit regime
or all historical allowance calculations. The inherited 2016 Personal Allowance
is a separate issue tracked in [#2359](https://github.com/PolicyEngine/policyengine-uk/issues/2359):
the inherited amount was £10,600 while the statutory amount is £11,000. The 2016 regression
uses £160,000 of dividends, which naturally withdraws the full allowance under
either amount. It exercises the dividend bands without selecting an allowance
through an intermediate input. Dividend rates, allowance allocation, Gift Aid
extensions and the optional extra dividend bracket retain their existing
interfaces.

The existing fixed-order allowance allocation does not always implement the
most-beneficial allocation required by ITA 2007 s. 25(2) for mixed wages and
dividends. The 2017, 2021 and 2026 threshold regressions also use dividend-only
income with a naturally zero Personal Allowance. The selected 2018, 2019 and
2025 mixed-income cases have independently checked allowance allocations;
they do not certify the allocation formula for other situations.
