import requests
import sys

def open_shelf():
    # Replace with the IP address or hostname of your ESP32
    esp32_url = "http://10.42.0.166"  # Use the mDNS hostname

    # Endpoint to switch the relay
    relay_endpoint = "/switch_relay"

    try:
        response = requests.get(esp32_url + relay_endpoint)
        if response.status_code == 200:
            print(f"Shelf opened successfully")
        else:
            print(f"Failed to open shelf. HTTP Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "open_shelf":
        open_shelf()