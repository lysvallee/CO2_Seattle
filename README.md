# CO2 Seattle - Building Energy Benchmarking 🏙️🌍

## 1. Project Overview 🎯

This project is based on the data provided by the City of Seattle (https://data.seattle.gov/Built-Environment/Building-Energy-Benchmarking-Data-2015-Present/teqw-tu6e/about_data) with the following objectives:

- 🔬 Develop an application to predict energy consumption and CO2 emissions of buildings
- 🌱 Support a long-term strategy to reduce greenhouse gas emissions
- 📊 Analyze the current state of Seattle's CO2 emissions and energy consumption
- 🤖 Create a predictive tool for buildings without existing energy data

## 2. Technical Strategy and Challenges 🧠

Obtaining satisfactory predictions with this dataset was a complex challenge that required careful, strategic approach. Recognizing the limitations of computational resources, we developed a nuanced machine learning strategy:

### Feature Selection and Importance 🔍
- Utilized XGBoostRegressor with L1 regularization to rank feature importance
- Implemented a custom Recursive Feature Elimination (RFE) approach
- Focused on resource-efficient feature selection

### Data Preprocessing Techniques 🧪
- Explored various encoding methods (OneHotEncoder, Count Encoding, Target Encoding)
- Carefully managed categorical variables to avoid prediction contamination

### Error Metrics and Model Evaluation 📈
- Minimized Mean Absolute Error (MAE) for practical prediction accuracy
- Used Root Mean Square Error (RMSE) to understand outlier impact
- Maintained R² score for comparative analysis

### Key Insights 💡
- Natural gas emerged as the most significant emission contributor
- Discovered that building age and ENERGY STAR score have minimal predictive power

## 3. Project Structure 📂

```
.
├── eda/
│   └── CO2_EDA.ipynb           # Exploratory Data Analysis
├── predictions/
│   └── CO2_predictions.ipynb   # Prediction model notebook
├── images/
│   └── schéma_fonctionnel_seattle.png  # Functional diagram
├── main.py                     # FastAPI application
└── requirements.txt            # Project dependencies
```

## 4. Technical Stack 🛠️

- **Web Framework**: FastAPI
- **Machine Learning**: 
  - Scikit-learn
  - Scikit-optimize
  - XGBoost
- **Visualization**: 
  - Plotly
- **Deployment**: 
  - Docker
  - Azure Cloud Services

## 5. Installation and Usage 🚀

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/CO2_Seattle.git
   cd CO2_Seattle
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application
   ```bash
   uvicorn main:app --reload
   ```

**Access Points**:
- Dashboard: `/dashboard/`
- Predictions: `/predictions/`
- Recommendations: `/recommendations/`


*Note: This project is more geared toward data practitioners than holders of a PhD in Statistics. But if you consider yourself the God of Heteroscedasticity, you might enjoy seeing the sufferings of mere mortals! 🤓*
