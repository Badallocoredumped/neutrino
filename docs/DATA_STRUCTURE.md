# data/DATA_SAMPLES.md

## Sample Data Files

This directory contains sample data files to demonstrate the structure and format of data processed by the Neutrino Energy Pipeline.

### Raw Data Samples

#### `sample_power_breakdown.jsonl`
- **Source**: Electricity Maps API - Power Breakdown endpoint
- **Description**: Turkey's electricity generation by source (wind, solar, coal, gas, etc.)
- **Format**: One JSON object per line
- **Sample frequency**: Hourly data points
- **Key fields**: `zone`, `datetime`, `powerConsumptionBreakdown`, `powerProductionBreakdown`

#### `sample_carbon_intensity.jsonl`
- **Source**: Electricity Maps API - Carbon Intensity endpoint  
- **Description**: Carbon intensity measurements for Turkey's grid
- **Format**: One JSON object per line
- **Key fields**: `zone`, `datetime`, `carbonIntensity`, `fossilFreePercentage`

### Transformed Data Samples

#### `sample_power_transformed.jsonl`
- **Description**: Processed power data with calculated fields
- **Transformations**: Added renewable/fossil percentages, totals, classifications

#### `sample_carbon_transformed.jsonl`
- **Description**: Processed carbon intensity data with enrichment
- **Transformations**: Added carbon level categories, time calculations

## Data Volume
- **Production**: ~1,440 records per day (hourly collection)
- **Retention**: Raw and transformed data stored locally
- **Storage**: MongoDB (operational) + PostgreSQL (analytics)