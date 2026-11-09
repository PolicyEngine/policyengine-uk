# Historical residential Stamp Duty Land Tax

Ordinary, non-relieved residential purchases use a percentage of the whole
purchase price from 1 December 2003 through 3 December 2014. The rate for
the price band applies to the whole consideration. Each upper limit stays in
the lower band: a £250,000 purchase in 2014 owes £2,500, while a £300,000
purchase owes £9,000. From 4 December 2014 the model charges marginal slices;
the same £300,000 purchase then owes £5,000.

The dated ordinary schedule includes the £175,000 nil-rate threshold from
3 September 2008 through 31 December 2009, the 5% band above £1 million
from 6 April 2011, and the 7% band above £2 million from 22 March 2012.
Main and additional purchases use the same ordinary rates before the
additional-dwelling higher rates begin on 1 April 2016.

The model accepts annual purchase amounts, not individual transaction dates.
Annual labels before 2015 read the parameters on 1 January. From 2015 onward
the existing fiscal-year conversion samples 30 April. Thus annual 2014 uses
the slab regime; raw dated parameter tests separately cover 3 and 4 December.
Annual 2003 precedes SDLT's 1 December commencement and returns zero for
this residential SDLT component. This does not calculate predecessor stamp
duty or establish complete historical UK tax coverage.

The model's first-time-buyer relief covers Schedule 6ZA from 22 November
2017. The separate relief for qualifying purchases from 25 March 2010 through
24 March 2012 remains unmodelled. The ordinary historical rates do not cover
that relief, disadvantaged-area relief, linked transactions, contractual
transitional elections, or distinct corporate, non-resident and short-lease
rules. Regional liability gates and lease-rent calculations are unchanged.
The program registry's verified-year range is unchanged.

Sources: [HMRC's historical SDLT tables](https://www.gov.uk/government/publications/rates-and-allowances-stamp-duty-land-tax),
[Finance Act 2003 s. 55 as at 3 December 2014](https://www.legislation.gov.uk/ukpga/2003/14/section/55/2014-12-03),
[Finance Act 2003 Schedule 19](https://www.legislation.gov.uk/ukpga/2003/14/schedule/19/enacted),
[Stamp Duty Land Tax Act 2015 s. 2](https://www.legislation.gov.uk/ukpga/2015/1/section/2/enacted),
and [Finance Act 2010 s. 6](https://www.legislation.gov.uk/ukpga/2010/13/section/6/enacted).
