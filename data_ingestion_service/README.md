# Data Ingestion Service

## Overview

The Data Ingestion Service is responsible for connecting to ERP platforms (primarily NetSuite), extracting data, profiling it, and storing both the data and its metadata in a structured repository. This service is a critical component in our data pipeline, enabling downstream AI processing and analytics.

## Architecture

### High-Level Components
```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │     │                   │
│   Data Sources    │────▶│  Data Ingestion   │────▶│   Data Storage    │
│  (NetSuite, etc.) │     │     Service       │     │  & Metadata Repo  │
│                   │     │                   │     │                   │
└───────────────────┘     └───────────────────┘     └───────────────────┘
          │                                                   ▲
          │                                                   │
          ▼                                                   │
┌───────────────────┐     ┌───────────────────┐               │
│                   │     │                   │               │
│     Event Bus     │────▶│   AI Processing   │───────────────┘
│ (Kafka/Event Hub) │     │     Service       │
│                   │     │                   │
└───────────────────┘     └───────────────────┘
```

### Core Components

1. **Source Connectors**
   - NetSuite SuiteTalk API Connector
   - Database Connectors (JDBC/ODBC)
   - File System Connectors (for CSV, JSON, etc.)

2. **Metadata Repository**
   - Hierarchical structure (Data Source → Schema → Table → Column)
   - Profile statistics storage
   - Data lineage tracking
   - Optimized indexing for query performance

3. **Data Processing Engine**
   - Data extraction orchestration
   - Schema inference and discovery
   - Incremental change tracking (CDC)
   - Batch processing framework
   - Resilient processing with retry mechanisms

4. **Data Profiling Engine**
   - Statistical analysis
   - Pattern recognition
   - Anomaly detection
   - Data quality validation

5. **API Layer**
   - REST APIs for metadata access
   - GraphQL for flexible queries
   - Authentication and authorization
   - Webhooks for integration with other services

6. **Event System**
   - Event Hub integration
   - Standardized event schemas
   - Reliable event publishing

7. **Monitoring & Logging**
   - Operational metrics collection
   - Structured logging system
   - Alerting for critical issues
   - Data lineage visualization

## Data Flow Process

1. **Discovery & Connection**
   - Register data source with credentials
   - Test connection and permissions
   - Cache connection metadata

2. **Metadata Extraction**
   - Discover available schemas
   - Enumerate tables and views
   - Extract column definitions and constraints
   - Store metadata in repository

3. **Data Profiling**
   - Sample data for profiling
   - Generate statistics (min, max, avg, null count, cardinality)
   - Detect data types and patterns
   - Identify potential primary/foreign keys
   - Detect anomalies in data

4. **Incremental Processing**
   - Track changes in source systems
   - Process only new or modified data
   - Maintain change history
   - Handle large datasets efficiently

5. **Event Publication**
   - Publish metadata change events
   - Trigger downstream processing
   - Ensure reliable delivery

## Technical Implementation

### Azure Components

- **Azure Functions**: For on-demand processing and scheduled crawling
- **Azure Data Factory**: For orchestration of data movement
- **Azure SQL Database**: For metadata repository
- **Azure Blob Storage**: For data lake storage
- **Azure Event Hub**: For event-driven processing
- **Azure Key Vault**: For secure credential storage
- **Azure Kubernetes Service**: For hosting the service components
- **Azure Monitor/Application Insights**: For monitoring and alerting

### Tech Stack

- **Languages**: Python, TypeScript
- **Frameworks**: FastAPI, SQLAlchemy
- **Data Processing**: Apache Spark, Pandas
- **CI/CD**: Azure DevOps, GitHub Actions
- **Containerization**: Docker, Kubernetes

### Data Model for Metadata Repository

```
DataSource
└── Schema
└── Table
└── Column
└── ProfileStats
```

- **DataSource**: Contains connection information, credentials reference, refresh schedule
- **Schema**: Logical grouping of tables
- **Table**: Metadata about each table (row count, last update time)
- **Column**: Data type, constraints, sample values
- **ProfileStats**: Statistical information about column data

## Best Practices

1. **Security**
   - Store credentials in Azure Key Vault
   - Use managed identities for service authentication
   - Implement column-level access control
   - Encrypt sensitive data

2. **Performance**
   - Use incremental processing where possible
   - Implement parallel processing for large datasets
   - Cache frequently accessed metadata
   - Use appropriate indexing in the metadata repository

3. **Reliability**
   - Implement retry logic for transient failures
   - Design for idempotent operations
   - Use circuit breakers for dependent services
   - Maintain audit logs for troubleshooting

4. **Scalability**
   - Containerize components for horizontal scaling
   - Use message queues to manage load spikes
   - Implement backpressure mechanisms
   - Design for multi-region deployment

5. **Monitoring**
   - Track data freshness metrics
   - Monitor data quality metrics
   - Alert on pipeline failures
   - Visualize data lineage

## Development Guidelines

1. **Code Organization**
   - Separate connectors by data source type
   - Use dependency injection for components
   - Follow the repository pattern for data access

2. **Testing Strategy**
   - Unit tests for business logic
   - Integration tests with mock data sources
   - End-to-end tests for critical paths
   - Performance tests for data processing

3. **CI/CD Pipeline**
   - Automated build and test
   - Infrastructure as code for deployment
   - Blue/green deployment strategy
   - Feature flags for gradual rollout

4. **Documentation**
   - API documentation with Swagger/OpenAPI
   - Architecture decision records
   - Runbooks for operations
   - User guides for data teams

## Integration Points

1. **Upstream Systems**
   - NetSuite SuiteTalk API integration
   - Database connection pooling
   - File system watchers

2. **Downstream Systems**
   - Event publication to AI Processing Service
   - Metadata API for frontend consumption
   - Export capabilities for reporting tools

## Implementation Roadmap

See the detailed implementation plan in [task_flow.md](./task_flow.md) which outlines the phased approach:

### Phase 1: Foundation
- Project initialization and infrastructure setup
- Core NetSuite connector with basic authentication
- Initial metadata repository schema
- Basic data extraction capabilities

### Phase 2: Core Functionality
- Complete NetSuite connector with advanced features
- Full metadata repository implementation
- Incremental data processing
- Basic data profiling capabilities

### Phase 3: Advanced Features
- Advanced data profiling and quality checks
- Event system implementation
- API layer deployment
- Security hardening

### Phase 4: Finalization
- Comprehensive monitoring and logging
- Performance optimization
- Documentation completion
- User training and handover

## Resources

- [NetSuite SuiteTalk Schema Documentation](https://www.netsuite.com/help/helpcenter/en_US/srbrowser/Browser2016_1/schema/record/account.html)
- [Azure Data Factory Documentation](https://docs.microsoft.com/en-us/azure/data-factory/)
- [Data Catalog Best Practices](https://docs.microsoft.com/en-us/azure/purview/overview)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
