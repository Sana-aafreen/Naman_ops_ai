import pandas as pd
import os

data_dir = r"c:\Users\sumbu\OneDrive\Desktop\Ops AI\data"
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

file_path = os.path.join(data_dir, "namandarshan_data.xlsx")

# Sample Data
sheets = {
    "Pandits": pd.DataFrame([
        {"ID": 1, "Name": "Pandit Sharma", "Location": "Varanasi", "Available": "Yes", "Expertise": "Vedic Rituals"},
        {"ID": 2, "Name": "Pandit Tiwari", "Location": "Varanasi", "Available": "Yes", "Expertise": "Astrology"},
        {"ID": 3, "Name": "Pandit Jha", "Location": "Rishikesh", "Available": "No", "Expertise": "Yoga"},
        {"ID": 4, "Name": "Pandit Shukla", "Location": "Ayodhya", "Available": "Yes", "Expertise": "Ramayan Paath"},
        {"ID": 5, "Name": "Pandit Mishra", "Location": "Ayodhya", "Available": "Yes", "Expertise": "Saryu Aarti"}
    ]),
    "Hotels": pd.DataFrame([
        {"ID": 101, "HotelName": "Ganges View", "Location": "Varanasi", "Price": 2500, "Available": "Yes"},
        {"ID": 102, "HotelName": "Temple Stay", "Location": "Varanasi", "Price": 1500, "Available": "Yes"},
        {"ID": 103, "HotelName": "Rishikesh Retreat", "Location": "Rishikesh", "Price": 3000, "Available": "Yes"},
        {"ID": 104, "HotelName": "Sri Ram Residency", "Location": "Ayodhya", "Price": 3500, "Available": "Yes"},
        {"ID": 105, "HotelName": "Ayodhya Bhawan", "Location": "Ayodhya", "Price": 1200, "Available": "Yes"}
    ]),
    "Cabs": pd.DataFrame([
        {"ID": 501, "Driver": "Rahul", "Location": "Varanasi", "Vehicle": "Sedan", "Available": "Yes"},
        {"ID": 502, "Driver": "Amit", "Location": "Varanasi", "Vehicle": "SUV", "Available": "Yes"},
        {"ID": 503, "Driver": "Suresh", "Location": "Rishikesh", "Vehicle": "Sedan", "Available": "Yes"},
        {"ID": 504, "Driver": "Deepak", "Location": "Ayodhya", "Vehicle": "SUV", "Available": "Yes"}
    ]),
    "Temples": pd.DataFrame([
        {
            "ID": 1001, 
            "Name": "Ram Janmabhoomi Temple", 
            "Location": "Ayodhya", 
            "Deity": "Lord Ram", 
            "Opening": "6:30 AM", 
            "Closing": "10:00 PM",
            "URL": "https://namandarshan.com/temples/ram-janmabhoomi-temple"
        },
        {
            "ID": 1002, 
            "Name": "Kashi Vishwanath", 
            "Location": "Varanasi", 
            "Deity": "Lord Shiva", 
            "Opening": "3:00 AM", 
            "Closing": "11:00 PM"
        }
    ])
}

with pd.ExcelWriter(file_path) as writer:
    for sheet_name, df in sheets.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"Created {file_path}")
