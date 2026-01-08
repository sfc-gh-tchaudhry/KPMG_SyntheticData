#!/usr/bin/env python3
"""
Vehicle Telematics Data Generator

Generates realistic vehicle telematics data for 500 vehicles traveling
from San Francisco to Los Angeles along Highway 5 over a 1-hour period.

Output: Individual JSON files, one telematics entry per file.
"""

import json
import random
import string
import os
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
NUM_VEHICLES = 500
DURATION_HOURS = 1
INTERVAL_MINUTES = 5
OUTPUT_DIR = Path("json")
VIN_FILE = "vins.txt"

# Route waypoints along I-5 from San Francisco to Los Angeles
# Format: (latitude, longitude, mile_marker)
ROUTE_WAYPOINTS = [
    (37.7749, -122.4194, 0),      # San Francisco
    (37.7396, -121.9000, 30),     # Dublin/Pleasanton area
    (37.7400, -121.4200, 60),     # Tracy
    (37.9577, -121.2908, 80),     # Stockton
    (37.6391, -120.9969, 110),    # Modesto
    (37.3022, -120.4830, 150),    # Merced
    (36.7468, -119.7726, 200),    # Fresno
    (36.3302, -119.2921, 240),    # Visalia
    (35.3733, -119.0187, 290),    # Bakersfield
    (34.9400, -118.8500, 330),    # Grapevine/Tejon Pass
    (34.3917, -118.5426, 360),    # Santa Clarita
    (34.0522, -118.2437, 380),    # Los Angeles
]

# VIN generation helpers (simplified but realistic format)
VIN_CHARS = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"  # No I, O, Q
VIN_DIGITS = "0123456789"


def generate_vin():
    """Generate a realistic-looking VIN (17 characters)."""
    # World Manufacturer Identifier (first 3 chars)
    wmi_options = ["1FA", "1FT", "1FM", "1FD", "2FA", "3FA", "1G1", "1GC", "1GT", 
                   "2G1", "3G1", "JN1", "JM1", "WBA", "WDB", "WAU", "5YJ"]
    wmi = random.choice(wmi_options)
    
    # Vehicle Descriptor Section (chars 4-9)
    vds = ''.join(random.choices(VIN_CHARS, k=5))
    check_digit = random.choice(VIN_DIGITS + "X")
    
    # Vehicle Identifier Section (chars 10-17)
    model_year = random.choice("LMNPRSTVWXY123456789")  # 2020-2029
    plant_code = random.choice(VIN_CHARS)
    sequential = ''.join(random.choices(VIN_DIGITS, k=6))
    
    return f"{wmi}{vds}{check_digit}{model_year}{plant_code}{sequential}"


def generate_unique_vins(count):
    """Generate a set of unique VINs."""
    vins = set()
    while len(vins) < count:
        vins.add(generate_vin())
    return sorted(list(vins))


def interpolate_position(progress, waypoints):
    """
    Interpolate position along the route based on progress (0.0 to 1.0).
    Adds some realistic lateral variation to simulate lane changes and curves.
    """
    total_distance = waypoints[-1][2]
    current_mile = progress * total_distance
    
    # Find the two waypoints we're between
    prev_wp = waypoints[0]
    next_wp = waypoints[1]
    
    for i, wp in enumerate(waypoints[:-1]):
        if wp[2] <= current_mile <= waypoints[i + 1][2]:
            prev_wp = wp
            next_wp = waypoints[i + 1]
            break
    
    # Interpolate between waypoints
    if next_wp[2] == prev_wp[2]:
        segment_progress = 0
    else:
        segment_progress = (current_mile - prev_wp[2]) / (next_wp[2] - prev_wp[2])
    
    lat = prev_wp[0] + (next_wp[0] - prev_wp[0]) * segment_progress
    lon = prev_wp[1] + (next_wp[1] - prev_wp[1]) * segment_progress
    
    # Add small random variation (lane changes, curves, GPS noise)
    lat += random.gauss(0, 0.002)
    lon += random.gauss(0, 0.002)
    
    return round(lat, 6), round(lon, 6)


def generate_vehicle_journey(vin, start_time, vehicle_seed):
    """Generate a complete journey for one vehicle."""
    random.seed(vehicle_seed)
    
    readings = []
    num_readings = (DURATION_HOURS * 60) // INTERVAL_MINUTES
    
    # Vehicle characteristics (vary by vehicle)
    base_speed = random.uniform(55, 75)  # Average highway speed
    fuel_start = random.uniform(70, 100)  # Starting fuel level
    fuel_consumption_rate = random.uniform(0.08, 0.15)  # % per reading at cruise
    
    # Tire pressures (baseline for this vehicle)
    tire_baseline = {
        "front_left": random.uniform(32, 35),
        "front_right": random.uniform(32, 35),
        "rear_left": random.uniform(32, 35),
        "rear_right": random.uniform(32, 35),
    }
    
    # Journey timing
    # Some vehicles start early, some late, some make stops
    journey_start_offset = random.randint(0, 30)  # Minutes into the 12h window
    trip_duration_hours = random.uniform(5.5, 10)  # Time to complete trip
    
    # Rest stops (0-3 stops of 15-45 minutes each) - only for longer journeys
    if num_readings > 60:  # Only add stops for journeys longer than 5 hours
        num_stops = random.randint(0, 3)
        stop_times = sorted([random.randint(30, num_readings - 30) for _ in range(num_stops)])
        stop_durations = [random.randint(3, 9) for _ in range(num_stops)]
    else:
        num_stops = 0
        stop_times = []
        stop_durations = []
    
    current_fuel = fuel_start
    current_progress = 0  # 0.0 to 1.0
    in_stop = False
    stop_remaining = 0
    stop_idx = 0
    
    for i in range(num_readings):
        timestamp = start_time + timedelta(minutes=i * INTERVAL_MINUTES)
        
        # Check if entering a rest stop
        if stop_idx < num_stops and i >= stop_times[stop_idx] and not in_stop:
            in_stop = True
            stop_remaining = stop_durations[stop_idx]
            stop_idx += 1
        
        # During a stop
        if in_stop:
            speed = 0
            stop_remaining -= 1
            if stop_remaining <= 0:
                in_stop = False
                # Refuel during stop
                current_fuel = min(100, current_fuel + random.uniform(20, 40))
        else:
            # Moving
            # Speed varies with traffic, terrain, etc.
            if current_progress < 0.1:  # Leaving SF - slower, city traffic
                speed = base_speed * random.uniform(0.4, 0.7)
            elif 0.8 < current_progress < 0.9:  # Grapevine - slower due to grade
                speed = base_speed * random.uniform(0.7, 0.85)
            elif current_progress > 0.95:  # Approaching LA - traffic
                speed = base_speed * random.uniform(0.3, 0.6)
            else:  # Open highway
                speed = base_speed * random.uniform(0.85, 1.15)
            
            # Progress along route
            progress_per_reading = (INTERVAL_MINUTES / 60) / trip_duration_hours
            current_progress = min(1.0, current_progress + progress_per_reading * (speed / base_speed))
            
            # Fuel consumption
            fuel_consumed = fuel_consumption_rate * (speed / 65)
            current_fuel = max(5, current_fuel - fuel_consumed)
        
        # Get position
        lat, lon = interpolate_position(current_progress, ROUTE_WAYPOINTS)
        
        # Engine temperature (varies with speed and ambient conditions)
        if speed == 0:
            engine_temp = random.uniform(175, 195)  # Idling or stopped
        else:
            engine_temp = random.uniform(195, 220)  # Normal operating range
        
        # Tire pressures (slight variations with temperature/driving)
        tire_pressure = {
            k: round(v + random.gauss(0, 0.5) + (speed / 100), 2)
            for k, v in tire_baseline.items()
        }
        
        reading = {
            "engine_temp_f": round(engine_temp, 2),
            "fuel_level_pct": round(current_fuel, 2),
            "location": {
                "latitude": lat,
                "longitude": lon
            },
            "speed_mph": round(speed, 2),
            "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "tire_pressure_psi": tire_pressure,
            "vin": vin
        }
        
        readings.append(reading)
    
    return readings


def main():
    print("=" * 60)
    print("Vehicle Telematics Data Generator")
    print("=" * 60)
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"\n✓ Created output directory: {OUTPUT_DIR}")
    
    # Generate VINs
    print(f"\nGenerating {NUM_VEHICLES} unique VINs...")
    vins = generate_unique_vins(NUM_VEHICLES)
    
    # Save VINs to file
    with open(VIN_FILE, 'w') as f:
        for vin in vins:
            f.write(vin + '\n')
    print(f"✓ Saved VINs to: {VIN_FILE}")
    
    # Calculate totals
    readings_per_vehicle = (DURATION_HOURS * 60) // INTERVAL_MINUTES
    total_readings = NUM_VEHICLES * readings_per_vehicle
    
    print(f"\nGenerating {total_readings:,} telematics readings...")
    print(f"  - {NUM_VEHICLES} vehicles")
    print(f"  - {readings_per_vehicle} readings per vehicle")
    print(f"  - {INTERVAL_MINUTES} minute intervals over {DURATION_HOURS} hour(s)")
    print(f"  - Output: {total_readings} individual JSON files")
    
    # Start time for the data
    start_time = datetime(2025, 10, 31, 6, 0, 0)  # 6:00 AM
    
    # Collect all readings
    all_readings = []
    for idx, vin in enumerate(vins):
        # Use VIN hash as seed for reproducibility
        vehicle_seed = hash(vin) % (2**32)
        readings = generate_vehicle_journey(vin, start_time, vehicle_seed)
        all_readings.extend(readings)
        
        # Progress update
        if (idx + 1) % 100 == 0 or idx == 0:
            print(f"  Generated data for {idx + 1}/{NUM_VEHICLES} vehicles...")
    
    print(f"\n✓ Generated {len(all_readings):,} total readings")
    
    # Create individual JSON files (one entry per file)
    print(f"\nCreating individual JSON files...")
    file_count = 0
    
    for reading in all_readings:
        vin = reading["vin"]
        ts = reading["timestamp"].replace(":", "-").replace(".", "-")
        json_filename = OUTPUT_DIR / f"{vin}_{ts}.json"
        
        with open(json_filename, 'w') as f:
            json.dump(reading, f, indent=2)
        
        file_count += 1
        if file_count % 1000 == 0:
            print(f"  Created {file_count} files...")
    
    print(f"\n✓ Created {file_count} JSON files in: {OUTPUT_DIR}/")
    
    # Show summary
    print("\nSample files:")
    sample_files = sorted(OUTPUT_DIR.glob("*.json"))[:5]
    for f in sample_files:
        size_bytes = f.stat().st_size
        print(f"  - {f.name} ({size_bytes} bytes)")
    
    print("\n" + "=" * 60)
    print("Generation complete!")
    print(f"Total: {file_count} JSON files (1 entry per file)")
    print("=" * 60)


if __name__ == "__main__":
    main()
