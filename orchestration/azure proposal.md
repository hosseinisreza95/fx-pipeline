# Azure Deployment Proposal

## Overview

In a production Azure environment, this pipeline runs daily using
**Azure Data Factory (ADF)** for orchestration, **Azure Container Instance (ACI)**
for execution, and **Azure SQL Database** as the warehouse backend.

---

## Architecture

```
frankfurter.app API
        ↓
Azure Data Factory (daily trigger, 6:00 AM UTC)
        ↓
Azure Container Instance (runs Docker image)
        ↓
Azure SQL Database (replaces SQLite in production)
        ↓
Power BI / reporting layer
```

---

## Docker Image Flow

```
Local Development
      ↓
docker build -t fx-pipeline .
      ↓
Azure Container Registry (stores the image)
      ↓
Azure Container Instance (runs the image daily)
```

---

## Components

### 1. Azure Container Registry (ACR)

Stores the Docker image:

```bash
# push image to ACR
az acr build --registry fxpipelineacr --image fx-pipeline:latest .
```

### 2. Azure Data Factory Pipeline

Triggers the container daily:

```json
{
  "name": "fx-pipeline-daily",
  "properties": {
    "activities": [
      {
        "name": "RunFXPipeline",
        "type": "ExecutePipeline",
        "typeProperties": {
          "pipeline": {
            "referenceName": "fx-pipeline-container",
            "type": "PipelineReference"
          },
          "parameters": {
            "mode": "daily"
          }
        }
      }
    ],
    "triggers": [
      {
        "name": "DailyTrigger",
        "type": "ScheduleTrigger",
        "typeProperties": {
          "recurrence": {
            "frequency": "Day",
            "interval": 1,
            "startTime": "2024-01-01T06:00:00Z",
            "timeZone": "UTC"
          }
        }
      }
    ]
  }
}
```

### 3. Infrastructure as Code (Bicep)

```bicep
// main.bicep — provisions ACR, ADF, and SQL Database

param location string = 'westeurope'
param projectName string = 'fx-pipeline'

// Azure Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: '${projectName}acr'
  location: location
  sku: {
    name: 'Basic'
  }
}

// Azure Data Factory
resource dataFactory 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: '${projectName}-adf'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
}

// Azure SQL Database
resource sqlServer 'Microsoft.Sql/servers@2021-11-01' = {
  name: '${projectName}-sql'
  location: location
  properties: {
    administratorLogin: 'sqladmin'
    administratorLoginPassword: 'REPLACE_WITH_SECRET'
  }
}

resource sqlDatabase 'Microsoft.Sql/servers/databases@2021-11-01' = {
  parent: sqlServer
  name: 'fx_dwh'
  location: location
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
}
```

---

## Key Decisions

| Decision | Choice | Reason |
|---|---|---|
| Orchestrator | Azure Data Factory | Native Azure, no extra infra |
| Runner | Azure Container Instance | Runs Docker image, serverless |
| Image registry | Azure Container Registry | Native integration with ACI |
| Schedule | Daily 6:00 AM UTC | Markets closed, fresh data available |
| Database | Azure SQL | Production-grade, easy to join with other DWH tables |
| Retries | 3 retries, 30s delay | API occasionally unavailable |
| Monitoring | ADF built-in alerts | Email on failure |

---

## Local Alternative (Prefect + Docker)

For local or non-Azure environments:

```bash
# build image
docker build -t fx-pipeline .

# run daily
docker run -v ${PWD}/db:/app/db fx-pipeline

# schedule with Prefect
prefect deployment build orchestration/prefect_flow.py:fx_pipeline_flow \
  --name fx-daily \
  --cron "0 6 * * *"

prefect deployment apply fx_pipeline_flow-deployment.yaml
prefect agent start -q default
```