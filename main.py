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
    
    with open("images/TexturesCom_LandscapesCityNight0038_1_S.jpg", "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode()

    content = f"""
    <html>
        <head>
            <title>{page_title}</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500&display=swap');
                
                body {{
                    font-family: 'Montserrat', sans-serif;
                    margin: 0;
                    padding: 0;
                    background: url(data:image/jpg;base64,{encoded_image}) no-repeat center center fixed;
                    background-size: cover;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    text-align: center;
                    padding-top: 50px;
                    background-color: rgba(255, 255, 255, 0.5);
                    border-radius: 8px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
                }}
                h1 {{
                    font-size: 48px;
                    color: #333333;
                    margin-bottom: 30px;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
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
                    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
                }}
                .button:hover {{
                    background-color: #EF553B;
                }}
                .image-container {{
                    margin-top: 50px;
                }}
                .image {{
                    display: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{page_title}</h1>
                <a href="{dashboard_button_url}" class="button">{dashboard_button_text}</a>
                <br>
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

    with open("images/TexturesCom_LandscapesCityNight0038_1_S.jpg", "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    content = f"""
    <html>
        <head>
            <title>{page_title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background: url(data:image/jpeg;base64,{encoded_image}) no-repeat center center fixed;
                    background-size: cover;
                }}
                .container {{
                    background-color: rgba(255, 255, 255, 0.7);
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    max-width: 800px;
                    margin: 0 auto;
                    text-align: center;
                    padding: 50px;
                }}
                h1 {{
                    font-size: 48px;
                    color: #333333;
                    margin-bottom: 30px;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                }}
                p {{
                    font-size: 24px;
                    color: #333333;
                    margin-bottom: 20px;
                }}
                form {{
                    margin-top: 20px;
                }}
                input[type="file"] {{
                    display: block;
                    margin: 0 auto;
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
                <p>Chargez un fichier CSV avec vos données</p>
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

    # Perform data formatting prior to predictions (see EDA file for details)
    current_year = datetime.datetime.now().year
    df['age'] = df['yearbuilt'].apply(lambda x: current_year - x)
    df.drop(['yearbuilt'], axis=1, inplace=True)

    df.rename(columns={'steamuse(kbtu)': 'steamuse_kbtu'}, inplace=True)
    df.rename(columns={'naturalgas(kbtu)': 'naturalgas_kbtu'}, inplace=True)
    df.rename(columns={'siteeui(kbtu/sf)': 'siteeui_kbtu_sf'}, inplace=True)
    df.rename(columns={'siteeuiwn(kbtu/sf)': 'siteeuiwn_kbtu_sf'}, inplace=True)
    df.rename(columns={'sourceeui(kbtu/sf)': 'sourceeui_kbtu_sf'}, inplace=True)
    df.rename(columns={'sourceeuiwn(kbtu/sf)': 'sourceeuiwn_kbtu_sf'}, inplace=True)
    df.rename(columns={'siteenergyuse(kbtu)': 'siteenergyuse_kbtu'}, inplace=True)
    df.rename(columns={'siteenergyusewn(kbtu)': 'siteenergyusewn_kbtu'}, inplace=True)

    def energy_usage(cell):
        if cell > 0:
          return 'Yes'
        else:
          return 'No'
    df['steamuse_kbtu'] = df['steamuse_kbtu'].apply(energy_usage)
    df['naturalgas_kbtu'] = df['naturalgas_kbtu'].apply(energy_usage)
    df.rename(columns={'steamuse_kbtu': 'steam'}, inplace=True)
    df.rename(columns={'naturalgas_kbtu': 'naturalgas'}, inplace=True)

    df['zipcode'] = df['zipcode'].astype('object')
    df['councildistrictcode'] = df['councildistrictcode'].astype('object')
    df['numberofbuildings'] = df['numberofbuildings'].astype('Int64')
    df['largestpropertyusetypegfa'] = df['largestpropertyusetypegfa'].astype('Int64')

    df['source_site'] = df['sourceeuiwn_kbtu_sf'] / df['siteeuiwn_kbtu_sf']

    df['source_wn'] = df['sourceeuiwn_kbtu_sf'] / df['sourceeui_kbtu_sf']

    df['site_wn'] = df['siteeuiwn_kbtu_sf'] / df['siteeui_kbtu_sf']

    targets = ['sourceeuiwn_kbtu_sf', 'source_wn', 'siteeuiwn_kbtu_sf', 'site_wn', 'source_site', 'siteenergyusewn_kbtu', 'siteenergyuse_kbtu', 'totalghgemissions']

    def transform_negatives(cell):
        if cell < 0:
          return 0
        else:
          return cell
    for target in targets:
        df[target] = df[target].apply(transform_negatives)

    df =df[['numberofbuildings',
     'propertygfatotal',
     'propertygfaparking',
     'age',
     'primarypropertytype',
     'councildistrictcode',
     'largestpropertyusetype',
     'steam',
     'naturalgas',
     'listofallpropertyusetypes',
     'source_site', 'sourceeuiwn_kbtu_sf', 'sourceeui_kbtu_sf', 'siteeuiwn_kbtu_sf', 'siteeui_kbtu_sf', 'siteenergyusewn_kbtu', 'siteenergyuse_kbtu', 'totalghgemissions']]


    # Define the targets and features
    targets = ['source_site', 'sourceeuiwn_kbtu_sf', 'sourceeui_kbtu_sf', 'siteeuiwn_kbtu_sf', 'siteeui_kbtu_sf', 'siteenergyusewn_kbtu', 'siteenergyuse_kbtu', 'totalghgemissions']
    y = df[targets]
    X = df.drop(targets, axis=1)
    
    # Load the trained model
    from joblib import load
    loaded_model = load('predictions/best_model.joblib')
    # Make predictions    
    y_pred = loaded_model.predict(X)
    # Round all values in y_pred to 2 decimal places
    y_pred = np.round(y_pred, decimals=2)

    # Create a simplified dataframe to compare the predictions side by side
    comp = pd.concat([df['totalghgemissions'], pd.Series(y_pred[:, -1], name='predicted_ghg_emissions')], axis=1)

    # Display the resulting dataframe
    comp_html = comp.to_html(index=False)

    with open("images/TexturesCom_LandscapesCityNight0038_1_S.jpg", "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    content = f"""
    <html>
        <head>
            <title>CO2 Emissions Prédictions</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500&display=swap');

                body {{
                    font-family: 'Montserrat', sans-serif;
                    margin: 0;
                    padding: 0;
                    background: url(data:image/jpeg;base64,{encoded_image}) no-repeat center center fixed;
                    background-size: cover;
                }}
                .container {{
                    background-color: rgba(255, 255, 255, 0.7);
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    padding: 20px;
                }}
                h1 {{
                    font-size: 48px;
                    color: #333333;
                    margin-bottom: 30px;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                    text-align: center;
                }}
                table {{
                    margin: 0 auto;
                    font-size: 18px;
                    width: 80%;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Prédictions Emissions CO2</h1>         
                <table>
                    {comp_html}
                </table>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=content)        

# Add a new endpoint to display the profiling report
@app.get("/dashboard/")
async def get_dashboard():
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eda/profiling_report.html")
    return FileResponse(file_path)

    content = f"""
    <html>
        <head>
            <title>Dashboard</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #808080;
                }}
            </style>
        </head>
        <body>
            <embed src="{file_path}" type="text/html" width="100%" height="100%"></embed>
        </body>
    </html>
    """
    return HTMLResponse(content=content)



@app.get("/recommendations/")
async def get_recommendations():
    with open("eda/plots/neighborhood.html", "r") as f:
        neighborhood = f.read()

    with open("eda/plots/age.html", "r") as f:
        age = f.read()

    with open("eda/plots/estar.html", "r") as f:
        estar = f.read()

    # Add space between HTML files
    html_content = f"""
    <html>
        <head>
            <title>Recommendations</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #808080;
                    margin: 0;
                    padding: 20px;
                }}
                .plot-container {{
                    background-color: #FFFFFF;
                    padding: 20px;
                    margin-bottom: 40px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
            </style>
        </head>
        <body>
            <div class="plot-container">
                {neighborhood}
            </div>
            <div class="plot-container">
                {age}
            </div>
            <div class="plot-container">
                {estar}
            </div>
        </body>
    </html>
    """

    return HTMLResponse(content=html_content, status_code=200)
