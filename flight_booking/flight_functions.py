from django.utils.crypto import get_random_string
import json
import requests
from flight_dispatch.models import Flight
from .models import FlightBooking
from passengers.models import PassengerBooking


def generate_unique_flight_number():
    """
    Generates a unique flight number and ensures it does not already exist in both
    Flight and FlightBooking models.
    """
    while True:
        # Generate a potential flight number
        flight_number = 'EAWFL-' + get_random_string(length=4, allowed_chars='1234567890') + get_random_string(length=2,
                                                                                                               allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ')

        # Check if this flight number already exists in the Flight or FlightBooking models
        flight_exists = Flight.objects.filter(flight_number=flight_number).exists()
        booking_exists = FlightBooking.objects.filter(flight_booking_number=flight_number).exists()

        if not flight_exists and not booking_exists:
            # If it doesn't exist in both, return this unique flight number
            return flight_number


def generate_unique_flight_leg_reference():
    """
    Generates a unique flight leg reference number and ensures it does not already exist in both
    Flight and FlightBooking models.
    """
    while True:
        # Generate a potential flight number
        flight_leg_reference = 'FLIDEAW-' + get_random_string(length=4, allowed_chars='1234567890') + get_random_string(
            length=2, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ')

        # Check if this flight number already exists in the Flight or FlightBooking models
        flight_exists = Flight.objects.filter(flight_leg_reference=flight_leg_reference).exists()
        booking_exists = FlightBooking.objects.filter(flight_tracking_id=flight_leg_reference).exists()

        if not flight_exists and not booking_exists:
            # If it doesn't exist in both, return this unique flight number
            return flight_leg_reference


def generate_unique_passenger_booking_reference():
    """
    Generates a unique flight leg reference number and ensures it does not already exist in both
    Flight and FlightBooking models.
    """
    while True:
        # Generate a potential flight number
        passenger_booking_reference = 'PBEAW-' + get_random_string(length=6, allowed_chars='1234567890') + get_random_string(
            length=3, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ')

        # Check if this flight number already exists in the Flight or FlightBooking models
        passenger_booking_exists = PassengerBooking.objects.filter(flight_leg_reference=passenger_booking_reference).exists()

        if not passenger_booking_exists:
            # If it doesn't exist in both, return this unique flight number
            return passenger_booking_reference


#avipages fligth calcualtor:

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