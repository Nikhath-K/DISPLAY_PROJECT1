from pymodbus.client.sync import ModbusSerialClient
from typing import Optional, List, Tuple, Dict

class TechnoModbusLiftController:
    def __init__(self):
        self.techno_client = None
        self.techno_com_port = None
        self.techno_floor_count = 23
        self.techno_slave_id = 1  # Default slave ID
        self.floor_numebr = None

    # 1. Sets the RS485 USB COM port
    def techno_set_com_port(self, port: str) -> bool:
        self.techno_client = ModbusSerialClient(method="rtu", port=port, baudrate=9600, timeout=1)
        if self.techno_client.connect():
            self.techno_com_port = port
            return True
        return False

    # 2. Retrieves the current RS485 USB COM port
    def techno_get_com_port(self) -> Optional[str]:
        return self.techno_com_port

    # 3. Checks if the board is online
    def techno_get_board_status(self) -> bool:
        if not self.techno_client or not self.techno_client.connect():
            return False
        try:
            techno_response = self.techno_client.read_holding_registers(0, 1, unit=self.techno_slave_id)
            return not techno_response.isError()
        finally:
            self.techno_client.close()

    # 4. Retrieves the current floor number
    def techno_get_floor_number(self) -> int:
        if not self.techno_client or not self.techno_client.connect():
            return -1
        try:
            techno_response = self.techno_client.read_holding_registers(21, 1, unit=self.techno_slave_id)
            self.floor_number = techno_response
            # print("type =", type(techno_response))
            # print((techno_response.registers[0]))
            return techno_response.registers[0] if not techno_response.isError() else -1
        finally:
            self.techno_client.close()

    # 5. Stores the lift's maximum floor count
    def techno_set_floor_count(self, techno_floor_count: int) -> bool:
        self.techno_floor_count = techno_floor_count
        return True

    # 6. Indicates whether the door is open
    def techno_get_door_status(self) -> str:
        if not self.techno_client or not self.techno_client.connect():
            return "unknown"

        try:
            techno_response = self.techno_client.read_holding_registers(address=17, count=2, unit=self.techno_slave_id)
            if techno_response.isError():
                return "unknown"

            techno_door_open = techno_response.registers[0]
            techno_door_close = techno_response.registers[1]

            if techno_door_open == 1 and techno_door_close == 0:
                return "open"
            elif techno_door_open == 0 and techno_door_close == 1:
                return "closed"
            elif techno_door_open == 0 and techno_door_close == 0:
                return "unknown"
            else:
                return "error"

        finally:
            self.techno_client.close()

    # 7. Shows if the lift is moving up, down, or stationary
    def techno_get_movement_status(self) -> str:
        if not self.techno_client or not self.techno_client.connect():
            return "unknown"

        try:
            techno_response = self.techno_client.read_holding_registers(address=19, count=2, unit=self.techno_slave_id)
            if techno_response.isError():
                return "unknown"

            print("floor:", self.floor_number, techno_response.registers[0], techno_response.registers[1])
            techno_up_status = techno_response.registers[0]
            techno_down_status = techno_response.registers[1]

            if techno_up_status == 1 and techno_down_status == 0:
                return "up"
            elif techno_up_status == 0 and techno_down_status == 1:
                return "down"
            elif techno_up_status == 0 and techno_down_status == 0:
                return "stationary"
            else:
                return "error"

        finally:
            self.techno_client.close()

    # 8. Provides an array of any detected faults
    def techno_read_faults(self) -> List[Tuple[str, int]]:
        if not self.techno_client or not self.techno_client.connect():
            return []

        techno_fault_labels = [
            'MIMO', 'FAULT(ALARM MESSAGE)', 'FM RETURN', 'FM EMERGENCY',
            'FIREMAN OPERATION', 'MAINTENANCE', 'OVERLOAD', 'INDEPENDENT',
            'ATTENDANT', 'MANUAL', 'STOP/RUN'
        ]

        try:
            techno_response = self.techno_client.read_holding_registers(address=0x00006, count=17, unit=self.techno_slave_id)
            if techno_response.isError():
                return []

            techno_faults = [(techno_fault_labels[i], techno_response.registers[i]) for i in range(len(techno_fault_labels))]
            return techno_faults

        finally:
            self.techno_client.close()

    # Set the slave ID for Modbus communication
    def techno_set_slaveid(self, techno_slave_id: int) -> bool:
        if 0 < techno_slave_id <= 247:
            self.techno_slave_id = techno_slave_id
            return True
        return False

    # Get the current slave ID
    def techno_get_slaveid(self) -> int:
        return self.techno_slave_id

    # 9. Returns an array containing all lift details
    def techno_get_lift_details(self) -> Dict[str, any]:
        return {
            "com_port": self.techno_get_com_port(),
            "board_status": self.techno_get_board_status(),
            "floor_number": self.techno_get_floor_number(),
            "floor_count": self.techno_floor_count,
            "door_status": self.techno_get_door_status(),
            "movement_status": self.techno_get_movement_status(),
            "faults": self.techno_read_faults(),
            "slave_id": self.techno_get_slaveid()
        }
