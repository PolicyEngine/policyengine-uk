---
title: "PolicyEngine UK: An Open-Source Microsimulation Model of the UK Tax-Benefit System"
tags:
  - Python
  - microsimulation
  - tax
  - benefit
  - distributional analysis
authors:
  - name: Max Ghenis
    orcid: 0000-0000-0000-0000
    affiliation: 1
  - name: Nikhil Woodruff
    orcid: 0000-0000-0000-0000
    affiliation: 1
  - name: Vahid Ahmadi
    orcid: 0000-0000-0000-0000
    affiliation: 1
    corresponding: true
affiliations:
  - name: PolicyEngine
    index: 1
date: 19 March 2026
bibliography: paper.bib
---

# Summary

PolicyEngine UK is an open-source microsimulation model of the United Kingdom's tax-benefit system, implemented in Python. It calculates variable values over UK entities from given policy parameters and structures, supporting two primary uses: computing statistics under current tax and benefit law, and simulating the effects of potential legislative changes. The model covers over 37 programmes administered by UK government agencies including HM Revenue & Customs (HMRC), the Department for Work and Pensions (DWP), the Department for Education (DfE), Revenue Scotland, and Social Security Scotland. PolicyEngine UK supports both individual household simulations via the `Simulation` class and population-wide microsimulations via the `Microsimulation` class, which incorporates survey weights from the Enhanced Family Resources Survey, prepared and published in the companion `policyengine-uk-data` repository [@pe_uk_data], to generate population-level estimates.

# Statement of Need

Tax-benefit microsimulation models are essential tools for evaluating the distributional impacts of fiscal policy. Governments, think tanks, and researchers rely on such models to estimate how policy reforms affect household incomes, poverty rates, and government budgets. In the UK, existing microsimulation models such as UKMOD [@sutherland2014euromod] and the IPPR Tax-Benefit Model are either restricted-access or proprietary, limiting transparency and reproducibility in policy analysis.

PolicyEngine UK addresses this gap by providing a fully open-source, publicly accessible microsimulation model. Researchers can install the package with `pip install policyengine-uk`, supply their own microdata, and compute the impact of current law or hypothetical policy reforms on any household or the full UK population. The `Simulation` class supports individual household analysis, while the `Microsimulation` class enables population-level aggregate analysis using Enhanced FRS datasets from the `policyengine-uk-data` repository [@pe_uk_data] with calibrated weights. The model's open development on GitHub enables external validation, community contributions, and reproducible policy analysis.

# State of the Field

The primary UK microsimulation models include UKMOD, maintained by the Centre for Microsimulation and Policy Analysis at the Institute for Social and Economic Research (ISER), University of Essex, as part of the EUROMOD family [@sutherland2014euromod], and models maintained internally by HM Treasury and the Institute for Fiscal Studies. OpenFisca [@openfisca] pioneered the open-source approach to tax-benefit microsimulation in France. PolicyEngine UK originated as OpenFisca UK and builds on this foundation through the PolicyEngine Core framework [@policyengine_core]. The UKMOD team's published model descriptions accelerated the early development of the model.

PolicyEngine UK differentiates itself in several ways:

- **Fully open-source and pip-installable**: users can install and run the model without institutional access or licence fees.
- **Comprehensive programme coverage**: 37 modelled programmes spanning income tax, National Insurance, Universal Credit, Child Benefit, Council Tax, and devolved policies in Scotland and Wales.
- **Integration with the PolicyEngine web application**: the model powers an interactive web interface at [policyengine.org](https://policyengine.org) that allows non-technical users to explore policy reforms.
- **Programmatic reform and scenario API**: users can define hypothetical policy reforms as simple parameter dictionaries, compose multiple scenarios with the `+` operator, or implement structural changes via simulation modifiers — and evaluate their impact on any household or the full population.
- **Labour supply dynamics**: a behavioural response module implements the Office for Budget Responsibility's labour supply elasticity framework, modelling both intensive margin (hours adjustment) and extensive margin (participation) responses to policy changes.
- **Enhanced microdata**: the model supports dataset fusion and calibration to align survey microdata with administrative totals across multiple dimensions.

# Software Design

PolicyEngine UK is built on the PolicyEngine Core framework, which extends the OpenFisca microsimulation engine. The model is organised into three main components:

**Parameters** define the rates, thresholds, and other numeric values of the tax-benefit system. These are stored as YAML files organised by government department (e.g., `parameters/gov/hmrc/` for HMRC policies) and indexed by time period, enabling the model to represent legislative changes over time. Parameters are addressed via hierarchical paths such as `gov.hmrc.income_tax.rates.uk[0].rate` for the basic income tax rate or `gov.dwp.universal_credit.standard_allowance.single.OVER_25` for Universal Credit allowances.

**Variables** define the formulas that compute tax liabilities, benefit entitlements, and other derived quantities. Each variable is implemented as a Python class that specifies its computation logic, the entity it applies to (person, benefit unit, or household), and its time period. The model contains over 700 variable definitions covering the full scope of the UK tax-benefit system.

**Reforms and Scenarios** allow users to modify parameters or variable formulas to represent hypothetical policy changes. Simple reforms can be expressed as dictionaries mapping parameter paths to new values, while the `Scenario` class supports composable reforms, time-varying parameters for phased implementation across multiple years, and simulation modifiers for complex structural changes such as repealing the two-child benefit limit. Scenarios apply policy changes without modifying the original simulation, enabling straightforward baseline-versus-reform comparison.

The model supports two input modes. The `Simulation` class accepts programmatically defined household situations — specifying ages, incomes, housing costs, and household composition — for individual-level analysis. The `Microsimulation` class loads population-level survey microdata from the `policyengine-uk-data` repository [@pe_uk_data] with calibrated weights, enabling computation of aggregate statistics including poverty rates, inequality metrics, and budgetary impacts. Revenue impacts are computed via the accounting identity: when household net income decreases under a reform, government revenue increases by the equivalent amount.

The dynamics module extends the static microsimulation with labour supply behavioural responses. It applies group-specific substitution and income elasticities based on OBR estimates, computing individual-level employment income adjustments and aggregate full-time equivalent (FTE) employment changes.

All code examples in the documentation are automatically re-executed with each new release to ensure correctness.

# Research Impact Statement

PolicyEngine UK has demonstrated research impact across government, academia, and policy research.

**Government adoption.** In 2025–2026, co-author Nikhil Woodruff served as an Innovation Fellow with 10DS — the data science team at 10 Downing Street — adapting PolicyEngine UK for government use [@ghenis2026no10]. The 10DS team built `10ds-microsim` on top of PolicyEngine UK to rapidly estimate the impacts of policy reforms on living standards, local area incomes, and distributional outcomes. HM Treasury has also formally documented PolicyEngine UK in the UK Algorithmic Transparency Recording Standard, describing it as a model their Personal Tax, Welfare and Pensions team is exploring for "advising policymakers on the impact of tax and welfare measures on households" [@hmt2024atrs].

**Parliamentary citation.** In February 2026, Baroness Altmann referenced PolicyEngine and its interactive dashboard during House of Lords Grand Committee debate on the National Insurance Contributions (Employer Pensions Contributions) Bill, noting that Commons Library research using PolicyEngine provided "a useful picture of the distributional effects of raising the contribution limit" across income deciles [@hansard2026nic].

**Academic research.** Youngman et al. [@youngman2026carbon] cite PolicyEngine UK's methodology in their agent-based macroeconomic model for the UK's Seventh Carbon Budget, developed at the Institute for New Economic Thinking at Oxford in partnership with the Department for Energy Security and Net Zero, noting that "the PolicyEngine microsimulation model addresses undersampling of rich households by using the Wealth and Assets Survey to impute additional wealth households into the Family Resources Survey."

**Policy research.** The National Institute of Economic and Social Research (NIESR) used PolicyEngine in their UK Living Standards Review 2025, acknowledging "the expertise and generosity of Nikhil Woodruff and Vahid Ahmadi in helping us maximise the benefits of using PolicyEngine" [@niesr2025living]. The Institute of Economic Affairs has published reports using PolicyEngine's microsimulation model to analyse employer National Insurance contributions [@woodruff2024nic] and the distributional impact of 2025–2026 tax changes on UK households [@woodruff2025tax].

# Acknowledgements

This work was supported by the Nuffield Foundation since September 2024 [@nuffield2024grant]. The Nuffield Foundation had no involvement in the design, development, or content of this software or paper.

We acknowledge contributions from all PolicyEngine UK contributors, and thank the OpenFisca community for the foundational microsimulation framework [@openfisca]. We acknowledge the UKMOD team at the Institute for Social and Economic Research (ISER), University of Essex, for their contributions to model descriptions [@sutherland2014euromod]. We also acknowledge the UK Data Service and the Department for Work and Pensions for providing access to the Family Resources Survey.

# AI Usage Disclosure

Generative AI tools (Claude by Anthropic, 2024–2026 [@claude2025]) were used to assist with code refactoring, test scaffolding, and drafting of this paper. All AI-assisted outputs were reviewed, edited, and validated by human authors, who made all core design decisions regarding software architecture, policy modelling, and parameter implementation. The authors remain fully responsible for the accuracy, originality, and correctness of all submitted materials.

# References
