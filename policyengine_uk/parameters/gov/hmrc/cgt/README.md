# Capital Gains Tax

The main rates (`basic_rate`, `higher_rate`, `additional_rate`) apply to gains other than those below; their 2024-25
values are day-weighted across the 30 October 2024 change. `annual_exempt_amount` is deducted once across all of a
person's gains, in the order most beneficial to the taxpayer (TCGA 1992 s. 1K(5)).

- `badr/`: rate and lifetime limit for gains qualifying for Business Asset Disposal Relief or Investors' Relief
  (TCGA 1992 s. 169N). These gains use the unused basic rate band before any other gains (TCGA 1992 s. 1I(4)-(6)).
- `residential_property/`: rates on UK residential property gains (TCGA 1992 ss. 1H-1I).
- `carried_interest/`: rates on carried interest gains (TCGA 1992 s. 1H; a flat 32% from 6 April 2025).

The `additional_rate` files in the two schedule folders equal the higher rate in law and exist only so reforms can
mirror the income tax additional-rate band, as the main `additional_rate` does.
