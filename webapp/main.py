import json
from os.path import dirname, abspath, join
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles


current_dir = dirname(abspath(__file__))
wellknown_path = join(current_dir, ".well-known")
historical_data = join(current_dir, "weather.json")

app = FastAPI()
app.mount("/.well-known", StaticFiles(directory=wellknown_path), name="static")


# load historical json data and serialize it:
with open(historical_data, "r") as f:
    data = json.load(f)

@app.get('/')
def root():
    """
    Allows to open the API documentation in the browser directly instead of
    requiring to open the /docs path.
    """
    return RedirectResponse(url='/docs', status_code=301)


@app.get('/countries')
def countries():
    """
    Returns a list of available countries.
    """
    return list(data.keys())

# Retornar ciudades de un país
@app.get('/countries/{country}')
def cities(country: str):
    """
    Returns a list of cities for a given country.
    """
    country = country.capitalize()
    msg = {}

    try:
        msg = {"error": "Country not found", "available_countries": list(data.keys())}
    except KeyError:
        msg = list(data[country].keys())
    
    return msg


# Retornar promedio mensual de una ciudad
@app.get('/countries/{country}/{city}')
def monthly_averages(country: str, city: str):
    """
    Returns the monthly averages for a given city in a country.
    """
    country = country.capitalize()
    city = city.capitalize()
    msg = {}

    try:
        msg = data[country][city]
    except KeyError as e:
        if str(e) == repr(country):
            msg = {"error": "Country not found", "available_countries": list(data.keys())}
        elif str(e) == repr(city):
            msg = {"error": "City not found", "available_cities": list(data[country].keys())}

    return msg


@app.get('/countries/{country}/{city}/{month}')
def monthly_average(country: str, city: str, month: str):
    """
    Returns the average temperature for a given city in a country for a specific month.
    """
    country = country.capitalize()
    city = city.capitalize()
    month = month.capitalize()
    msg = {}

    try:
        msg = data[country][city][month]
    except KeyError as e:
        if str(e) == repr(country):
            msg = {"error": "Country not found", "available_countries": list(data.keys())}
        elif str(e) == repr(city):
            msg = {"error": "City not found", "available_cities": list(data[country].keys())}
        elif str(e) == repr(month):
            msg = {"error": "Month not found", "available_months": list(data[country][city].keys())}

    return msg


# Generate the OpenAPI schema:
openapi_schema = app.openapi()
with open(join(wellknown_path, "openapi.json"), "w") as f:
    json.dump(openapi_schema, f)


# Test unitarios

def test_root_redirect():
    """
    Test case for root endpoint redirection.
    """
    response = client.get("/")
    assert response.status_code == 301
    assert response.url == "/docs"

def test_countries():
    """
    Test case for countries endpoint.
    """
    response = client.get("/countries")
    assert response.status_code == 200
    assert sorted(response.json()) == ["England", "France", "Germany", "Italy", "Peru", "Portugal", "Spain"]

def test_cities():
    """
    Test case for cities endpoint.
    """
    response = client.get("/countries/italy")
    assert response.status_code == 200
    assert sorted(response.json()) == ["Milan", "Rome", "Venice"]

def test_monthly_averages():
    """
    Test case for monthly_averages endpoint.
    """
    response = client.get("/countries/italy/rome")
    assert response.status_code == 200
    assert response.json() == {"January": 10, "February": 12, "March": 15}

def test_monthly_average():
    """
    Test case for monthly_average endpoint.
    """
    response = client.get("/countries/italy/rome/january")
    assert response.status_code == 200
    assert response.json() == 10

def test_country_not_found():
    """
    Test case for country not found scenario.
    """
    response = client.get("/countries/nonexistentcountry")
    assert response.status_code == 200
    assert response.json() == {"error": "Country not found", "available_countries": ["England", "France", "Germany", "Italy", "Peru", "Portugal", "Spain"]}

def test_city_not_found():
    """
    Test case for city not found scenario.
    """
    response = client.get("/countries/italy/nonexistentcity")
    assert response.status_code == 200
    assert response.json() == {"error": "City not found", "available_cities": ["Milan", "Rome", "Venice"]}

def test_month_not_found():
    """
    Test case for month not found scenario.
    """
    response = client.get("/countries/italy/rome/nonexistentmonth")
    assert response.status_code == 200
    assert response.json() == {"error": "Month not found", "available_months": ["January", "February", "March"]}
