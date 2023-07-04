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
    
    # Preprocess the data
    df['numberofbuildings'].replace(0, 1, inplace=True)
    df['numberoffloors'].replace(0, 1, inplace=True)
    df['compliancestatus'].replace('Error - Correct Default Data', np.nan, inplace=True)
    df['compliancestatus'].replace('Missing Data', np.nan, inplace=True)
    
    # Energy usage
    def energy_usage(cell):
        if cell > 0:
            return True
        else:
            return False
    df['steamuse_kbtu'] = df['steamuse(kbtu)'].apply(energy_usage)
    df['electricity_kbtu'] = df['electricity(kbtu)'].apply(energy_usage)
    df['naturalgas_kbtu'] = df['naturalgas(kbtu)'].apply(energy_usage)
    df.rename(columns={'steamuse_kbtu': 'steamuse'}, inplace=True)
    df.rename(columns={'electricity_kbtu': 'electricity'}, inplace=True)
    df.rename(columns={'naturalgas_kbtu': 'naturalgas'}, inplace=True)
    
    # Age
    current_year = datetime.datetime.now().year
    df['age'] = df['yearbuilt'].apply(lambda x: current_year - x)
    
    # Load the trained model
    from joblib import load
    loaded_model = load('randomforest_model.joblib')
    
    # Make predictions
    column_num=['largestpropertyusetypegfa', 'age', 'numberofbuildings', 'numberoffloors']
    column_cat=['steamuse', 'electricity', 'naturalgas', 'compliancestatus']
    df = pd.concat([df[column_num], df[column_cat], df['totalghgemissions']], axis=1)
    X_test = df.drop(columns='totalghgemissions')
    y_pred = loaded_model.predict(X_test)
    comp = pd.concat([df['totalghgemissions'], pd.Series(y_pred, name='predicted_ghg_emissions')], axis=1)
    
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
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "your_report.html")
    return FileResponse(file_path)


@app.get("/recommendations/")
async def get_recommendations():
    with open("neighborhood.html", "r") as f:
        neighborhood = f.read()

    with open("age.html", "r") as f:
        age = f.read()

    with open("estar.html", "r") as f:
        estar = f.read()

    content = f"{neighborhood}\n{age}\n{estar}"
    return HTMLResponse(content=content)
