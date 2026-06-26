# DAX Measure Dictionary

Create a dedicated `_Measures` table and place all measures there. The fact grain is one source campaign observation; `campaign_record_id` is technical and must never be presented as a customer ID.

## Core KPIs

```DAX
Campaign Observations =
COUNTROWS ( fact_campaign_contact )

Successful Subscriptions =
SUM ( fact_campaign_contact[conversion_flag] )

Deposit Conversion Rate =
DIVIDE ( [Successful Subscriptions], [Campaign Observations] )

Average Campaign Contacts =
AVERAGE ( fact_campaign_contact[current_campaign_contacts] )

Median Campaign Contacts =
MEDIAN ( fact_campaign_contact[current_campaign_contacts] )

Previously Contacted Observations =
SUM ( fact_campaign_contact[previously_contacted_flag] )

Previously Contacted Rate =
DIVIDE ( [Previously Contacted Observations], [Campaign Observations] )

Previous Campaign Success Observations =
SUM ( fact_campaign_contact[previous_campaign_success_flag] )

Previous Campaign Success Rate =
DIVIDE ( [Previous Campaign Success Observations], [Campaign Observations] )
```

## Channel and Timing

```DAX
Cellular Conversion Rate =
CALCULATE ( [Deposit Conversion Rate], dim_contact[contact_channel] = "cellular" )

Telephone Conversion Rate =
CALCULATE ( [Deposit Conversion Rate], dim_contact[contact_channel] = "telephone" )

Conversion vs Overall (pp) =
VAR OverallRate = CALCULATE ( [Deposit Conversion Rate], REMOVEFILTERS ( dim_contact ) )
RETURN [Deposit Conversion Rate] - OverallRate
```

Sort `dim_contact[contact_month]` by `dim_contact[month_sort]` and `dim_contact[contact_weekday]` by `dim_contact[weekday_sort]`.

## Operational Propensity Scoring

These measures use final-model scores across the historical portfolio. They support ranking and capacity scenarios; they are **not unbiased evaluation measures**.

```DAX
High-Propensity Observation Count =
CALCULATE (
    [Campaign Observations],
    fact_campaign_contact[recommended_contact_flag] = 1
)

Top-Decile Observations =
CALCULATE (
    [Campaign Observations],
    fact_campaign_contact[propensity_decile] = 1
)

Operational Top-Decile Conversion Rate =
CALCULATE (
    [Deposit Conversion Rate],
    fact_campaign_contact[propensity_decile] = 1
)

Operational Conversion Rate All Deciles =
CALCULATE (
    [Deposit Conversion Rate],
    REMOVEFILTERS ( fact_campaign_contact[propensity_decile] )
)

Operational Top-Decile Concentration =
DIVIDE ( [Operational Top-Decile Conversion Rate], [Operational Conversion Rate All Deciles] )

Average Propensity Score =
AVERAGE ( fact_campaign_contact[propensity_score] )
```

## Locked-Test Evaluation

Use these measures for model-evaluation visuals and lift claims. `model_evaluation_decile` is intentionally disconnected from descriptive slicers.

```DAX
Locked Test Observations =
SUM ( model_evaluation_decile[observations] )

Locked Test Subscriptions =
SUM ( model_evaluation_decile[subscriptions] )

Locked Test Decile Conversion Rate =
DIVIDE ( [Locked Test Subscriptions], [Locked Test Observations] )

Locked Test Overall Conversion Rate =
CALCULATE (
    [Locked Test Decile Conversion Rate],
    REMOVEFILTERS ( model_evaluation_decile[locked_test_decile] )
)

Locked Test Top-Decile Conversion Rate =
CALCULATE (
    [Locked Test Decile Conversion Rate],
    model_evaluation_decile[locked_test_decile] = 1
)

Locked Test Top-Decile Lift =
DIVIDE ( [Locked Test Top-Decile Conversion Rate], [Locked Test Overall Conversion Rate] )
```

## Configurable Threshold

Create a disconnected what-if table:

```DAX

## New Table
Threshold Parameter = GENERATESERIES ( 0.05, 0.80, 0.01 )

## New Measure
Selected Threshold =
SELECTEDVALUE ( 'Threshold Parameter'[Value], 0.15 )

Scenario Target Observations =
VAR Cutoff = [Selected Threshold]
RETURN
    CALCULATE (
        [Campaign Observations],
        FILTER (
            fact_campaign_contact,
            fact_campaign_contact[propensity_score] >= Cutoff
        )
    )

Scenario Observed Conversion Rate =
VAR Cutoff = [Selected Threshold]
RETURN
    CALCULATE (
        [Deposit Conversion Rate],
        FILTER (
            fact_campaign_contact,
            fact_campaign_contact[propensity_score] >= Cutoff
        )
    )
```

These are targeting scenarios, not projected incremental conversions or financial benefits.

## Dynamic Titles

```DAX
Profile Page Title =
"Customer Profile Intelligence | " &
COALESCE ( SELECTEDVALUE ( dim_contact[contact_channel] ), "All channels" )

Propensity Page Title =
"Propensity Decision Support | Threshold " & FORMAT ( [Selected Threshold], "0%" )
```
