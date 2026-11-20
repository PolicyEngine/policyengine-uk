# Savings starter rate

The annual starting-rate limit remains £5,000 through 2030–31 under Finance
Act 2026 section 9. From 2031–32, Income Tax Act 2007 section 21(3A) increases
the preceding rounded limit by the positive September CPI rise and rounds the
full amount upward to a multiple of £10. Zero or negative CPI leaves the
limit unchanged. `create_threshold_indexation.py` generates these annual
values through the economic-assumptions horizon; future CPI inputs are
forecasts or scenario assumptions. The pre-2015 parameter history is retained
without being verified by this prospective change.
