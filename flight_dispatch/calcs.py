import json
import requests
def calculate_flight(departure, arrival):
    url = "https://frc.aviapages.com/api/flight_calculator/"

    payload = json.dumps({
      "departure_airport": departure,
      "arrival_airport": arrival,
      "aircraft": "BBJ / Boeing 737-700",
      "pax": 2,
      "airway_time": True,
      "airway_fuel": True,
      "airway_distance": True,
      "ifr_route": True
    })

    headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': 'Token dgEfoyGvYiAgsKcqm8w4OKiqRp5WeNcLI0Vh'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    api_response = json.loads(response.text)
    return api_response

print(calculate_flight("EVRA", "EGSS"))
