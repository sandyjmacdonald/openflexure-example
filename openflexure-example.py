#!/usr/bin/env python3
import time
import datetime
import os
import re
import sys
import tty
import termios

LED_BRIGHTNESS = 0.33
MOTOR_INCREMENT = 500

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

def getch():
    """Capture a single key press without waiting for Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def main():
    from sangaboard import Sangaboard
    from picamzero import Camera

    # Use Sangaboard as a context manager for proper setup and cleanup
    with Sangaboard() as sb:
        # Turn LED on
        sb.illumination.cc_led = LED_BRIGHTNESS
        
        # Set up the camera and start preview
        cam = Camera()
        cam.start_preview()
        print("Camera preview started.\n")
        print("Interactive motor control:")
        print("  W/S: Move Y axis up/down")
        print("  A/D: Move X axis left/right")
        print("  Z/X: Move Z axis up/down")
        print("\nPress 'c' when ready to proceed to timelapse capture.")

        # Interactive control loop for motor movement using getch()
        while True:
            key = getch().lower()
            if key == 'w':
                sb.move_rel([0, MOTOR_INCREMENT, 0])
                print("Moved Y axis up by MOTOR_INCREMENT")
            elif key == 's':
                sb.move_rel([0, -MOTOR_INCREMENT, 0])
                print("Moved Y axis down by MOTOR_INCREMENT")
            elif key == 'a':
                sb.move_rel([-MOTOR_INCREMENT, 0, 0])
                print("Moved X axis left by MOTOR_INCREMENT")
            elif key == 'd':
                sb.move_rel([MOTOR_INCREMENT, 0, 0])
                print("Moved X axis right by MOTOR_INCREMENT")
            elif key == 'z':
                sb.move_rel([0, 0, MOTOR_INCREMENT])
                print("Moved Z axis up by MOTOR_INCREMENT")
            elif key == 'x':
                sb.move_rel([0, 0, -MOTOR_INCREMENT])
                print("Moved Z axis down by MOTOR_INCREMENT")
            elif key == 'c':
                print("Exiting interactive mode. Proceeding to timelapse setup.")
                break
            else:
                # Optionally, ignore unknown keys or print a message.
                print(f"Unknown command: {key}")

        # Stop the camera preview before timelapse capture starts
        cam.stop_preview()
        print("Camera preview stopped.")

        # Turn LED off
        sb.illumination.cc_led = 0.0

        # Get timelapse settings from the user (using input() so Enter is required)
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
        folder_name = start_time.strftime("%Y-%m-%d_%H:%M:%S")
        os.makedirs(folder_name, exist_ok=True)
        print(f"Images will be saved to folder: {folder_name}")

        # Start the timelapse capture loop
        end_time = start_time + datetime.timedelta(seconds=total_duration)
        print("Starting timelapse capture...")
        while datetime.datetime.now() < end_time:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            filename = os.path.join(folder_name, f"{timestamp}.jpg")
            # Turn LED on
            sb.illumination.cc_led = LED_BRIGHTNESS
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