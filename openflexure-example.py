#!/usr/bin/env python3

import time
import datetime
import os
import re

# Enable serial interface
# Install picamzero with: sudo apt update && sudo apt install python3-picamzero
# Install pysangaboard with: sudo pip install --break-system-packages git+https://gitlab.com/filipayazi/pysangaboard.git@sangaboardv5
# This installs the branch of the pysangaboard library with support for illumination LEDs

def parse_time_value(time_str):
    """
    Parse a time string with units such as '5s', '1m', '2h' or compound strings like '1d 4h 30m'
    and return the total seconds.
    """
    pattern = r"^\s*((?P<days>\d+)\s*d)?\s*((?P<hours>\d+)\s*h)?\s*((?P<minutes>\d+)\s*m)?\s*((?P<seconds>\d+)\s*s)?\s*$"
    match = re.match(pattern, time_str.strip(), re.IGNORECASE)
    if not match:
        return None
    days = int(match.group('days')) if match.group('days') else 0
    hours = int(match.group('hours')) if match.group('hours') else 0
    minutes = int(match.group('minutes')) if match.group('minutes') else 0
    seconds = int(match.group('seconds')) if match.group('seconds') else 0
    return days * 86400 + hours * 3600 + minutes * 60 + seconds

def main():
    from sangaboard import Sangaboard
    from picamzero import Camera

    # Set up the camera and start preview
    cam = Camera()
    cam.start_preview()
    print("Camera preview started.")
    print()
    print("Interactive motor control:")
    print("  W/S: Move Y axis up/down")
    print("  A/D: Move X axis left/right")
    print("  Z/X: Move Z axis up/down")
    print()
    print("Press 'c' when ready to proceed to timelapse capture.")

    # Use Sangaboard as a context manager for proper setup and cleanup
    with Sangaboard() as sb:
        # Interactive control loop for motor movement
        while True:
            key = input("Enter command (W/A/S/D/Z/X or 'c' to capture): ").strip().lower()
            if key == 'w':
                sb.move_rel([0, 500, 0])
                print("Moved Y axis up by 500")
            elif key == 's':
                sb.move_rel([0, -500, 0])
                print("Moved Y axis down by 500")
            elif key == 'a':
                sb.move_rel([-500, 0, 0])
                print("Moved X axis left by 500")
            elif key == 'd':
                sb.move_rel([500, 0, 0])
                print("Moved X axis right by 500")
            elif key == 'z':
                sb.move_rel([0, 0, 500])
                print("Moved Z axis up by 500")
            elif key == 'x':
                sb.move_rel([0, 0, -500])
                print("Moved Z axis down by 500")
            elif key == 'c':
                print("Exiting interactive mode. Proceeding to timelapse setup.")
                break
            else:
                print("Unknown command. Please use W, A, S, D, Z, X or 'c'.")

        # Stop the camera preview before timelapse capture starts
        cam.stop_preview()
        print("Camera preview stopped.")

        # Get timelapse settings from the user
        duration_input = input("Enter timelapse duration (e.g., '1d 4h 30m', '30m'): ")
        total_duration = parse_time_value(duration_input)
        if total_duration is None or total_duration <= 0:
            print("Invalid duration format. Exiting.")
            return

        frequency_input = input("Enter capture frequency (e.g., '5s', '1m'): ")
        frequency = parse_time_value(frequency_input)
        if frequency is None or frequency <= 0:
            print("Invalid frequency. Exiting.")
            return

        # Create a folder for the timelapse images
        start_time = datetime.datetime.now()
        folder_name = start_time.strftime("%Y%m%d_%H%M%S")
        os.makedirs(folder_name, exist_ok=True)
        print(f"Images will be saved to folder: {folder_name}")

        # Start the timelapse capture loop
        end_time = start_time + datetime.timedelta(seconds=total_duration)
        print("Starting timelapse capture...")

        while datetime.datetime.now() < end_time:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(folder_name, f"{timestamp}.jpg")
            # Turn LED on at 0.33 illumination
            sb.illumination.cc_led = 0.33
            # Take a photo and save it to the filename
            cam.take_photo(filename)
            # Turn LED off immediately after capture
            sb.illumination.cc_led = 0.0
            print(f"Captured image: {filename}")
            time.sleep(frequency)

        print("Timelapse complete.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Program interrupted by user.")