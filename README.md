# Email-Recommendations-AI-Engine

## Overview

This project develops an AI-powered recommendation engine for email marketing optimization. It leverages historical and real-time data to automate offer selection, identify unsent files, and deliver performance insights across sponsors, categories, ISPs, and campaigns. The backend is implemented in Python with AI algorithms, and the frontend features a Streamlit-based interactive, multi-page dashboard.

The engine empowers marketers to accelerate data-driven decisions, boosting CTR, revenue, and targeting precision while minimizing manual analysis efforts.

## Business Objectives

- Automate identification of not sent files for campaigns.
- Provide sponsor-wise and category-wise recommendations of best-performing offers.
- Allow deep-dives into ISP, sponsor, and category performance.
- Enable visual tracking of campaign, mailer, and server performance.
- Improve campaign CTR, revenue, and targeting accuracy.
- Reduce manual analysis time by providing a one-stop recommendation system.

## Scope

### In-Scope
- Python-based AI recommendation engine.
- Streamlit-based multi-page UI for navigation.
- Integration of sponsor, live, and master data tables.
- Filters available across all modules: ISP, Sponsor, Category, Date, Campaign Name, Data File.
- Visualizations: Line charts, bar charts, tables, pie/donut charts.
- Daily recommendation page with suppression logic.

### Out-of-Scope
- Actual email delivery system (handled externally by ESP).
- Advanced personalization at individual customer level (phase-2 scope).
- Mobile application UI (initial scope is Streamlit web app).

## Functional Requirements

### Navigation (Main Pages → Sub Pages)

1. **Daily Recommendation (Core System)**  
   AI-driven recommendations for daily campaigns.  
   Incorporates suppression logic to filter offers/files.  
   Output in ranked table format with offer/file details.

2. **Not Sent File Extraction**  
   Search box: Enter campaign name → Extract files not sent for that campaign.  
   Output table: List of unsent files with filters applied.  
   Filters: ISP, Sponsor, Category, Date, Campaign Name, Data File.

3. **Sponsor & Category Wise Best File/Offer**  
   Select sponsor and/or category from slicers.  
   Show best-performing files and offers.  
   Works for sponsor only, category only, or both combined.  
   Filters: ISP, Sponsor, Category, Date, Campaign Name, Data File.

4. **Data View (Sponsor Table, Live Table, Master Data File)**  
   Display the three core data sources in visual table format.  
   Filters: ISP, Sponsor, Category, Date, Campaign Name, Data File.

5. **Top Offers by ISP, Sponsor & Category**  
   Ranking of offers by ISP, Sponsor, and Category.  
   Output as table + bar chart.  
   Filters: ISP, Sponsor, Category, Date, Campaign Name, Data File.

6. **File Wise Top Offer**  
   Show top offers linked to individual data files.  
   Drill-down by ISP, sponsor, and category.  
   Filters: ISP, Sponsor, Category, Date, Campaign Name, Data File.

7. **Season Wise Category Performance**  
   Seasonal trends of category performance.  
   Line/Bar chart for seasonal patterns.  
   Filters: ISP, Sponsor, Category, Date, Campaign Name, Data File.

8. **Mailer Performance (Visualization)**  
   Mailer performance metrics (CTR, Open Rate, Revenue).  
   Display via bar/line charts.  
   Filters: ISP, Sponsor, Category, Date.

9. **Server Performance**  
   Server-wise campaign performance visualization.  
   Trend charts for performance by server.  
   Filters: ISP, Sponsor, Category, Date.

10. **Sponsor, File & Offer Performance Visualization**  
    Trend-wise performance breakdown.  
    Visuals: Line chart, Bar graph, Table, Pie/Donut chart.  
    Filters: ISP, Sponsor, Category, Date, Campaign Name, Data File.

## Non-Functional Requirements

- **Performance**: Queries and recommendations to run in ≤ 5 seconds for datasets up to 100K rows.
- **Scalability**: Ability to process larger datasets (1M+ rows) without major redesign.
- **Usability**: Simple Streamlit navigation with sidebar for filters.
- **Security**: Local or secured server deployment; no external exposure of raw data.
- **Maintainability**: Modular Python backend for easy extension of new features.

## Data Sources

- **Sponsor Table**: Details of sponsors and associated offers.
- **Live Table**: Campaign performance data (sent volumes, CTR, revenue, etc.).
- **Master Data File**: Complete dataset with ISP, category, sponsor, and file-level details.

## Assumptions

- Historical performance data is available and regularly updated.
- Suppression rules are clearly defined by business users.
- Users have access to clean datasets for sponsor, live, and master files.

## Risks & Dependencies

- **Risk**: Inconsistent or missing campaign data may reduce accuracy.
- **Risk**: Complex filtering may impact UI performance in Streamlit.
- **Dependency**: AI model performance depends on quality of historical data.

## Deliverables

- Streamlit UI with multi-page navigation.
- Python backend with AI recommendation engine.
- Visual dashboards for performance monitoring.
- Exportable reports (CSV/Excel).
- Documentation & user guide.

## Timeline (Tentative)

| Phase | Task                          | Duration  |
|-------|-------------------------------|-----------|
| 1     | Requirement Finalization      | 2 weeks  |
| 2     | Data Preparation & Cleaning   | 4 weeks  |
| 3     | Backend Development (AI + Python) | 5 weeks  |
| 4     | Streamlit UI Development      | 4 weeks  |
| 5     | Testing (Unit + UAT)          | 2 weeks  |
| 6     | Deployment & Handover         | 1–2 weeks|

## Success Metrics

- **Time Savings**: Achieve ≥60% reduction in manual effort for campaign analysis and offer selection.
- **Performance Uplift**: Increase campaign CTR by 20–25% compared to historical averages.
- **Decision Speed**: Recommendations and top-offer identification available in ≤3 seconds for datasets up to 100K rows.
- **Adoption Rate**: Achieve ≥85% active usage by the marketing team within the first 3 months post-deployment.
- **Data-Driven Planning**: At least 70% of new campaign drops use system recommendations within the first quarter.

## Getting Started

### Prerequisites
- Python 3.8+ with libraries: `streamlit`, `pandas`, `numpy`, `scikit-learn`, `plotly` (for visualizations).
- Access to data sources (Sponsor Table, Live Table, Master Data File).

### Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd email-recommendations-ai-engine
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure data paths in `config.py` (point to your Sponsor, Live, and Master data files).

### Running the Application
1. Launch the Streamlit app:
   ```
   streamlit run app.py
   ```
2. Open your browser to `http://localhost:8501`.
3. Use the sidebar for filters and navigate via the main menu.

### Development Setup
- Backend logic is in `/backend/` (AI recommendation engine).
- UI components in `/pages/` (multi-page Streamlit modules).
- Data processing scripts in `/data/`.

## Contributing
Contributions are welcome! Please fork the repo and submit a pull request for any features or bug fixes.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
For questions or feedback, reach out to the project lead at [email@example.com].