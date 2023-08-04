import os
from sqlmodel import Session
from fastapi import FastAPI, HTTPException
from models import Buildings
from services import engine, create_db_and_tables
import pandas as pd
from fastapi.responses import HTMLResponse, FileResponse
from fastapi import Request
from fastapi import File, UploadFile
import plotly.express as px
import plotly.io as pio
import plotly.graph_objs as go
import base64
import numpy as np
import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import KNNImputer
from sklearn.preprocessing import PowerTransformer
from category_encoders.glmm import GLMMEncoder

# Create an instance of FastAPI
app = FastAPI()


# Use a callback to trigger the creation of tables if they don't exist yet
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/add-building/")
async def add_building(building: Buildings):
    with Session(engine) as session:
        exist = session.query(Buildings).filter(
            Buildings.OSEBuildingID == building.OSEBuildingID).first()
        if exist:
            raise HTTPException(
                status_code=400, detail="Building already exists")

     
        session.add(building)
        session.commit()
        session.refresh(building)

        return building


@app.get("/")
async def root(request: Request):
    page_title = "Seattle - Building Energy Efficiency"
    dashboard_button_text = "Dashboard"
    dashboard_button_url = request.url_for("get_dashboard")
    predictions_button_text = "Prédictions"
    predictions_button_url = request.url_for("get_predictions")
    recommendations_button_text = "Recommandations"
    recommendations_button_url = request.url_for("get_recommendations")
    
    with open("images/seattle-8027337_1280.jpg", "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode()

    content = f"""
    <html>
        <head>
            <title>{page_title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: gray;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    text-align: center;
                    padding-top: 50px;
                }}
                .button {{
                    display: inline-block;
                    border-radius: 8px;
                    background-color: #636EFA;
                    color: #FFFFFF;
                    padding: 12px 20px;
                    margin: 20px;
                    text-align: center;
                    text-decoration: none;
                    font-size: 24px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }}
                .button:hover {{
                    background-color: #EF553B;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{page_title}</h1>
                <a href="{dashboard_button_url}" class="button">{dashboard_button_text}</a>
                <br>
                <img src="data:image/jpg;base64,{encoded_image}" width="800" height="500">
                <a href="{predictions_button_url}" class="button">{predictions_button_text}</a>
                <br>
                <a href="{recommendations_button_url}" class="button">{recommendations_button_text}</a>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=content)
    

@app.get("/predictions/")
async def get_predictions(request: Request):
    page_title = "Emissions CO2"
    upload_button_text = "Comparaison"
    content = f"""
    <html>
        <head>
            <title>{page_title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #F7F7F7;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    text-align: center;
                    padding-top: 50px;
                }}
                .button {{
                    display: inline-block;
                    border-radius: 8px;
                    background-color: #636EFA;
                    color: #FFFFFF;
                    padding: 12px 20px;
                    margin: 20px;
                    text-align: center;
                    text-decoration: none;
                    font-size: 24px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }}
                .button:hover {{
                    background-color: #EF553B;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{page_title}</h1>
                <p>Upload a CSV file with building data.</p>
                <form action="/predict/" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" accept=".csv">
                    <br>
                    <br>
                    <button type="submit" class="button">{upload_button_text}</button>
                </form>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=content)

@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    # Import CSV file into a Pandas dataframe
    df = pd.read_csv(file.file, delimiter=';')
    
    # Put column names in lowercase
    df.columns = map(str.lower, df.columns)

    # Fix the case and replace duplicates
    df['neighborhood'] = df['neighborhood'].str.upper()
    df['neighborhood'] = df['neighborhood'].str.replace('DELRIDGE NEIGHBORHOODS','DELRIDGE')

    # Fix 'energystarscore'
    df['energystarscore'] = df['energystarscore'].replace("NULL", None)


    # Impute 'zipcode' missing values from 'latitude' and 'longitude'
    location = ['zipcode', 'latitude', 'longitude']
    dfl = df[location]
    dfl = pd.DataFrame(data=KNNImputer(n_neighbors=10).fit_transform(dfl), index=df.index, columns=location)
    df = df.drop(columns=location).join(dfl)

    """#x.Feature Engineering"""

    # Derive the buildings age from 'yearbuilt'
    current_year = datetime.datetime.now().year
    df['age'] = df['yearbuilt'].apply(lambda x: current_year - x)
    df.drop(['yearbuilt'], axis=1, inplace=True)


    # Create new columns for the types of energy consumption (steam/electricity/gaz)df['numberofbuildings'] = df['numberofbuildings'].astype('int64')
    def energy_usage(cell):
        if cell > 0:
          return True
        else:
          return False
    df['steamuse_kbtu'] = df['steamuse(kbtu)'].apply(energy_usage)
    df['electricity_kbtu'] = df['electricity(kbtu)'].apply(energy_usage)
    df['naturalgas_kbtu'] = df['naturalgas(kbtu)'].apply(energy_usage)
    df.rename(columns={'steamuse_kbtu': 'steam'}, inplace=True)
    df.rename(columns={'electricity_kbtu': 'electricity'}, inplace=True)
    df.rename(columns={'naturalgas_kbtu': 'naturalgas'}, inplace=True)

    df.rename(columns={'siteeui(kbtu/sf)': 'siteeui_kbtu_sf'}, inplace=True)
    df.rename(columns={'siteeuiwn(kbtu/sf)': 'siteeuiwn_kbtu_sf'}, inplace=True)
    df.rename(columns={'sourceeui(kbtu/sf)': 'sourceeui_kbtu_sf'}, inplace=True)
    df.rename(columns={'sourceeuiwn(kbtu/sf)': 'sourceeuiwn_kbtu_sf'}, inplace=True)
    df.rename(columns={'siteenergyuse(kbtu)': 'siteenergyuse_kbtu'}, inplace=True)
    df.rename(columns={'siteenergyusewn(kbtu)': 'siteenergyusewn_kbtu'}, inplace=True)
    df.rename(columns={'propertygfabuilding(s)': 'propertygfabuilding_s'}, inplace=True)

    
    """#x.Target engineering

    'sourceeuiwn_kbtu_sf', 'sourceeui_kbtu_sf', 'siteeuiwn_kbtu_sf', 'siteeui_kbtu_sf', 'siteenergyusewn_kbtu', 'siteenergyuse_kbtu', 'totalghgemissions'
    """

    df['source_site'] = df['sourceeuiwn_kbtu_sf'] / df['siteeuiwn_kbtu_sf']

    # Now that there are less missing values, change the feature types
    df['zipcode'] = df['zipcode'].astype('object')
    df['councildistrictcode'] = df['councildistrictcode'].astype('object')
    df['numberofbuildings'] = df['numberofbuildings'].astype('int64')    

    # Load the trained model
    from joblib import load
    loaded_model = load('eda_predictions/model.joblib')
    
    # Make predictions

    # Fix dtype changes after CSV exporting
    df['zipcode'] = df['zipcode'].astype('object')
    df['councildistrictcode'] = df['councildistrictcode'].astype('object')
    df['energystarscore'] = df['energystarscore'].astype('object')
    # Turn the boolean columns into categorical for target encoding
    for column in df.select_dtypes(include=['bool']).columns:
      df[column] = df[column].astype('object')

    """#4.Gestion des targets multiples

    Scikit-learn propose deux solutions :
    - MultiOutputRegressor si les variables sont traitées de façon indépendante.
    - RegressorChain si elles sont dépendantes.

    https://scikit-learn.org/stable/modules/multiclass.html

    Il y a une corrélation élevée (0.873) entre la consommation énergétique et les émissions de CO2, donc on choisira la seconde option.

    Comme nous prédirons les émissions après la consommation, cela nous mène à créer une variable targets commençant par la colonne siteenergyuse_kbtu :
    """

    # Define the targets and features
    targets = ['source_site', 'sourceeuiwn_kbtu_sf', 'sourceeui_kbtu_sf', 'siteeuiwn_kbtu_sf', 'siteeui_kbtu_sf', 'siteenergyusewn_kbtu', 'siteenergyuse_kbtu', 'totalghgemissions']
    y = df[targets]
    X = df.drop(targets, axis=1)
    print(X.columns.tolist())

    """#5.Preprocessing des données

    L'EDA a montré que certaines variables étaient loin d'avoir une distribution gaussienne. Pour y remédier, le QuantileTransformer semble préférable au PowerTransformer parce qu'il est efficace quelle que soit la distribution de départ : https://scikit-learn.org/stable/modules/preprocessing.html#mapping-to-a-gaussian-distribution
    """

    # Apply QuantileTransformer to the target variables
    qt = PowerTransformer()
    y = qt.fit_transform(y)

    # Retrieve the transformed column corresponding to 'totalghgemissions'
    totalghg = pd.DataFrame(y[:, -1], columns=['totalghgemissions'])

    # Preprocess categorical features with a target encoder based on 'totalghgemissions'
    def target_encoder(X=None):
      X_cat = X.select_dtypes(include=['object'])
      X_num = X.select_dtypes(include=['int64', 'float64'])
      encoder = GLMMEncoder(verbose=2, drop_invariant=False, return_df=True, handle_missing='return_nan', randomized=True, binomial_target=False)
      X_cat_encoded = encoder.fit_transform(X_cat, totalghg)
      X = pd.concat([X_cat_encoded, X_num], axis=1)
      return X

    X = target_encoder(X)
    print(X.columns.tolist())
    y_pred = loaded_model.predict(X)
    y_pred = qt.inverse_transform(y_pred)
    comp = pd.concat([df['totalghgemissions'], pd.Series(y_pred[:, -1], name='predicted_ghg_emissions')], axis=1)

##############################################

    
    # column_num=['largestpropertyusetypegfa', 'age', 'numberofbuildings', 'numberoffloors']
    # column_cat=['steamuse', 'electricity', 'naturalgas', 'compliancestatus']
    # df = pd.concat([df[column_num], df[column_cat], df['totalghgemissions']], axis=1)
    # X_test = df.drop(columns='totalghgemissions')
    # y_pred = loaded_model.predict(X_test)
    # comp = pd.concat([df['totalghgemissions'], pd.Series(y_pred, name='predicted_ghg_emissions')], axis=1)
    
    # Display the resulting dataframe
    comp_html = comp.to_html(index=False)
    content = f"""
    <html>
        <head>
            <title>CO2 Emissions Predictions</title>
        </head>
        <body>
            <h1>CO2 Emissions Predictions</h1>
            <p>Predicted CO2 emissions:</p>
            {comp_html}
        </body>
    </html>
    """
    return HTMLResponse(content=content)

# Add a new endpoint to display the profiling report
@app.get("/dashboard/")
async def get_dashboard():
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eda/profiling_report.html")
    return FileResponse(file_path)


@app.get("/recommendations/")
async def get_recommendations():
    with open("eda/plots/neighborhood.html", "r") as f:
        neighborhood = f.read()

    with open("eda/plots/age.html", "r") as f:
        age = f.read()

    with open("eda/plots/estar.html", "r") as f:
        estar = f.read()

    content = f"{neighborhood}\n{age}\n{estar}"
    return HTMLResponse(content=content)
