# Tasks & Feature Requests

## Feature Requests

### YNAB Integration (Admin-Only)
- **Description**: Integration with YNAB (You Need A Budget) API to enable financial data queries and insights
- **Requirements**:
  - Admin-guarded endpoint (requires `lldap_admin` group)
  - YNAB API token configuration in environment variables
  - Sync budget data, transactions, and categories
  - Store YNAB data for RAG queries
- **Endpoints**:
  - `POST /api/admin/ynab/sync` - Trigger YNAB data sync
  - `GET /api/admin/ynab/status` - Check sync status and last update
  - `GET /api/admin/ynab/budgets` - List available budgets
- **Implementation Notes**:
  - Use YNAB API v1 (https://api.youneedabudget.com/v1)
  - Consider rate limiting (200 requests per hour)
  - Store transaction data in PostgreSQL with appropriate indexing
  - Index transaction descriptions and categories in ChromaDB for RAG queries

### Money Insights
- **Description**: AI-powered financial insights and analysis based on YNAB data
- **Features**:
  - Spending pattern analysis
  - Budget vs. actual comparisons
  - Category-based spending trends
  - Anomaly detection (unusual transactions)
  - Natural language queries like "How much did I spend on groceries last month?"
  - Month-over-month and year-over-year comparisons
- **Implementation Notes**:
  - Leverage existing LangChain agent architecture
  - Add custom tools for financial calculations
  - Use LLM to generate insights and summaries
  - Create visualizations or data exports for frontend display

## Backlog

- [ ] YNAB API client module
- [ ] YNAB data models (Budget, Transaction, Category, Account)
- [ ] Database schema for financial data
- [ ] YNAB sync background job/scheduler
- [ ] Financial insights LangChain tools
- [ ] Admin UI for YNAB configuration
- [ ] Frontend components for money insights display

## Technical Debt

_To be added_

## Bugs

_To be added_
