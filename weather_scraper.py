import requests
from bs4 import BeautifulSoup
import re

def scrape_weather():
    url = "https://www.yr.no/en/forecast/daily-table/2-3882428/Chile/Regi%C3%B3n%20del%20Biob%C3%ADo/Provincia%20de%20Biob%C3%ADo/Los%20%C3%81ngeles"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # The structure based on inspection:
    # Each day seems to be in a list item or similar container.
    # We look for the date link which is a good anchor.
    
    daily_items = soup.find_all('li', class_='daily-weather-list-item')
    
    if not daily_items:
        print("Could not find 'daily-weather-list-item' list items.")
        return

    report_lines = []
    report_lines.append("# Weather Forecast for Los Ángeles, Chile")
    report_lines.append("")
    report_lines.append("| Date | Min Temp | Max Temp | Rain | Wind (Avg) |")
    report_lines.append("|---|---|---|---|---|")

    for item in daily_items:
        # Date
        date_elem = item.find('time')
        if date_elem:
            date_text = date_elem.get_text(strip=True)
        else:
            # Fallback
            date_link = item.find('a', class_='daily-weather-list-item__item-date')
            date_text = date_link.get_text(strip=True) if date_link else "Unknown"
        
        # Temperature
        max_temp_elem = item.find(class_='min-max-temperature__max')
        min_temp_elem = item.find(class_='min-max-temperature__min')
        
        max_temp = max_temp_elem.get_text(strip=True) if max_temp_elem else "?"
        min_temp = min_temp_elem.get_text(strip=True) if min_temp_elem else "?"

        # Rain
        rain_container = item.find(class_='daily-weather-list-item__precipitation')
        if rain_container:
            # Check if it says "no precipitation" in class or text
            if 'daily-weather-list-item__precipitation--no-precipitation' in rain_container.get('class', []):
                rain_text = "0 mm"
            else:
                # Extract value and unit
                # Structure: <span><span>0</span><abbr>mm</abbr></span>
                # Just get all text
                rain_text = rain_container.get_text(strip=True).replace("Precipitation", "").strip()
        else:
            rain_text = "?"

        # Wind
        wind_val_elem = item.find(class_='wind__value')
        wind_unit_elem = item.find(class_='wind__unit')
        
        if wind_val_elem:
            wind_val = wind_val_elem.get_text(strip=True)
            wind_unit = wind_unit_elem.get_text(strip=True) if wind_unit_elem else "m/s"
            wind_text = f"{wind_val} {wind_unit}"
        else:
            wind_text = "?"

        report_lines.append(f"| {date_text} | {min_temp} | {max_temp} | {rain_text} | {wind_text} |")

    report_content = "\n".join(report_lines)
    
    with open("weather_report.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print("Report generated: weather_report.md")
    print(report_content)

if __name__ == "__main__":
    scrape_weather()
