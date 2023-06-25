from sqlmodel import Session
from fastapi import FastAPI, HTTPException
from models import Buildings
from services import engine, create_db_and_tables
import pandas as pd
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi import File, UploadFile
import plotly.express as px
import plotly.io as pio
import plotly.graph_objs as go
import base64


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
    page_title = "Building Energy Efficiency in Seattle"
    dashboard_button_text = "Go to Dashboard"
    dashboard_button_url = request.url_for("get_dashboard")
    predictions_button_text = "Get Predictions"
    predictions_button_url = request.url_for("get_predictions")
    image_url = request.url_for("static", path="images/city-4558069_1280.jpg")
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
                <p>Welcome! Click the button below to access the dashboard.</p>
                <a href="{dashboard_button_url}" class="button">{dashboard_button_text}</a>
                <br>
                <img src="{image_url}">
                <p>Click the button below to get predictions.</p>
                <a href="{predictions_button_url}" class="button">{predictions_button_text}</a>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=content)

    
    
@app.get("/dashboard/")
async def get_dashboard():
    with Session(engine) as session:
        buildings = session.query(Buildings).all()
        df = pd.DataFrame([b.__dict__ for b in buildings])
        
        # Create histogram for buildingtype
        fig1 = px.histogram(df, x="buildingtype", color_discrete_sequence=['#636EFA'])
        fig1.update_layout(
            title="Distribution of Building Types",
            xaxis_title="Building Type",
            yaxis_title="Count",
            showlegend=False
        )
        
        # Create histogram for totalghgemissions
        fig2 = px.histogram(df, x="totalghgemissions", nbins=30, color_discrete_sequence=['#EF553B'])
        fig2.update_layout(
            title="Distribution of Total GHG Emissions (Metric Tons CO2e)",
            xaxis_title="Total GHG Emissions (Metric Tons CO2e)",
            yaxis_title="Count",
            showlegend=False,
            yaxis_type="log"
        )
        
        # Add a picture of Seattle at the top of the page
        image_filename = "images/seattle-8027337_1280.jpg"
        encoded_image = base64.b64encode(open(image_filename, 'rb').read()).decode()
        seattle_pic = f"data:image/jpg;base64,{encoded_image}"
        image_html = f'<div style="text-align:center;"><img src="{seattle_pic}" width="800" height="300"></div>'
        
        # Add a title and subtitle
        title_html = "<h1 style='text-align:center;'>Interactive Dashboard</h1>"
        subtitle_html = "<p style='text-align:center;'>Mouse over the graphs to display tips.</p>"
        
        # Combine the image, title, subtitle, and histograms in a single HTML response
        figs_html = f'<div>{image_html}</div><br><div>{title_html}</div><br><div>{subtitle_html}</div><br><div>{pio.to_html(fig1, full_html=False)}</div><br><div>{pio.to_html(fig2, full_html=False)}</div>'
        return HTMLResponse(content=figs_html)


@app.get("/predictions/")
async def get_predictions(request: Request):
    page_title = "CO2 Emissions Predictions"
    upload_button_text = "Upload CSV File"
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
    # Code to process the uploaded CSV file and make predictions goes here
    return {"message": "Todos: update models.py to add the necessary columns with proper types, create several more Plotly charts for the dashboard & build a model with fastai."}
