# Azure Deployment Proposal

> **Note:** This project is currently deployed on GCP (see README for live deployment details).
> This document describes how the same pipeline could be deployed on Azure.

---

## Overview

In a production Azure environment, this pipeline would run daily using
**Azure Data Factory (ADF)** for orchestration, **Azure Container Instance (ACI)**
for execution, and **Azure SQL Database** as the warehouse backend.

---

## Architecture

```
frankfurter.app API
        ↓
Azure Data Factory (daily trigger, 17:00 CET)
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

```bash
az acr build --registry fxpipelineacr --image fx-pipeline:latest .
```

### 2. Azure Data Factory Pipeline

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
            "startTime": "2024-01-01T16:00:00Z",
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
| Schedule | Daily 16:00 UTC (17:00 CET) | 1 hour after ECB publishes rates |
| Database | Azure SQL | Production-grade, easy to join with other DWH tables |
| Retries | 3 retries, 30s delay | API occasionally unavailable |
| Monitoring | ADF built-in alerts | Email on failure |

---

## GCP vs Azure Comparison

| | GCP (deployed) | Azure (proposal) |
|---|---|---|
| Orchestration | Cloud Scheduler | Azure Data Factory |
| Runner | Cloud Run Job | Azure Container Instance |
| Image registry | Artifact Registry | Azure Container Registry |
| Database | BigQuery | Azure SQL Database |
| Dashboard | Looker Studio | Power BI |
| IaC | gcloud CLI | Bicep |