# Import the ModbusLiftController class
from techno_modbus_controller import TechnoModbusLiftController

# Step 1: Initialize the lift controller object
techno_lift_controller = TechnoModbusLiftController()

# Step 2: Set the COM port
print("Enter com port: ", end="")
techno_com_port = input()
connection_success = techno_lift_controller.techno_set_com_port(techno_com_port)

if connection_success:
    print(f"Connected successfully to {techno_com_port}")
else:
    print(f"Failed to connect to {techno_com_port}")
    # If connection fails, you may stop here or retry with a different COM port

# Step 3: Check if the board is online
if techno_lift_controller.techno_get_board_status():
    print("Lift control board is online.")
else:
    print("Lift control board is offline or not responding.")
    # If the board is offline, you may need to troubleshoot the connection


# Get current floor number
techno_current_floor = techno_lift_controller.techno_get_floor_number()
print(f"Current Floor: {techno_current_floor}")

# Get door status
techno_door_status = techno_lift_controller.techno_get_door_status()
print(f"Door Status: {techno_door_status}")

# Get movement status
techno_movement_status = techno_lift_controller.techno_get_movement_status()
print(f"Lift Movement: {techno_movement_status}")

# Get any faults
techno_faults = techno_lift_controller.techno_read_faults()
print("Detected Faults: ", end='')
for label, value in techno_faults:
    print(f"{value}", end=' ')
print()


# Get all lift details at once
techno_lift_details = techno_lift_controller.techno_get_lift_details()
print("Lift Details:", techno_lift_details)
