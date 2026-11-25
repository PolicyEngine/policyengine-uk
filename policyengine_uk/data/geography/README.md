# Council regions

`local_authority_regions.csv` maps every existing `LocalAuthority` enum key to a
model `Region` key. It combines these Office for National Statistics lookups:

- [Ward to local authority district to CTYUA to RGN to CTRY, May 2026](https://www.data.gov.uk/dataset/45aa6dad-4337-4947-9ad0-0a48a8b6fa35/ward-to-local-authority-district-to-ctyua-to-rgn-to-ctry-may-2026-lookup-in-the-uk),
  ArcGIS item `79e0950fa93446b996d0f3f95537ab6d`, geography date 7 May 2026.
- [Ward to local authority district to CTY to RGN to CTRY, December 2020 V2](https://www.data.gov.uk/dataset/f13d7a3d-5ad1-49dd-8ea4-8169e07a5704/ward-to-local-authority-district-to-cty-to-rgn-to-ctry-december-2020-lookup-in-the-uk-v2),
  ArcGIS item `87a9e5a70982411790319c0eaad61351`, geography date 31 December 2020.

Current rows take precedence. The historical lookup supplies 24 council names
that remain in the model's enum; six current unitary names appear only in the
2026 lookup. The union covers all 385 enum labels exactly, without aliases or
fuzzy matching. ONS leaves the English region field empty for devolved nations;
those rows use their stated country as the model region. Yorkshire and The
Humber maps to `YORKSHIRE`.

Source: Office for National Statistics licensed under the Open Government
Licence v.3.0. The [ONS geography licence](https://www.ons.gov.uk/methodology/geography/licences)
covers these non-postcode lookups.

The raw distinct LAD/name/region/country projections used for this mapping have
SHA-256 `bbd0a780e43a668a319913f8abd9ca0de8c885952f4d2f2a727672f6c3e3d83d`
(2026) and `da160154684019482f73e84b624d7f218b0fcc185fa357d8266d386b804526fa`
(2020 V2). The CSV's `source_year` records the chosen vintage for each row.
When updating it, check every enum label against the official names, retain
historical members, and rerun the complete mapping regression. Council names
and region assignments are geography data; this table does not change the
model's council boundaries by simulation year or map councils to rental areas.
