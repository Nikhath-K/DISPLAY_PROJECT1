from pymodbus.client.sync import ModbusSerialClient
from typing import Optional, List, Tuple, Dict

class TechnoModbusLiftController:
    def __init__(self):
        self.techno_client = None
        self.techno_com_port = None
        self.techno_floor_count = 23
        self.techno_slave_id = 1  # Default slave ID
        self.floor_number = None

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


    
    # 9. Returns an array containing all lift details
    def techno_get_lift_details(self) -> Dict[str, any]:
        if not self.techno_client or not self.techno_client.connect():
            return {"error": "Connection failed"}
        try:
            techno_response = self.techno_client.read_holding_registers(1, 22, unit=self.techno_slave_id)
            if techno_response.isError():
                return {"error": "Read error"}
            details = {
                "floor_number": techno_response.registers[20],
                "up_arrow": techno_response.registers[19],
                "down_arrow": techno_response.registers[18],
                "door_open": techno_response.registers[17],
                "door_close": techno_response.registers[16],
                "lift_running": techno_response.registers[15],
                "error_manual": techno_response.registers[14],
                "error_attendant": techno_response.registers[13],
                "error_independent": techno_response.registers[12],
                "error_overload": techno_response.registers[11],
                "error_maintenance": techno_response.registers[10],
                "error_fireman_operation": techno_response.registers[9],
                "error_fm_emergency": techno_response.registers[8],
                "error_fm_return": techno_response.registers[7],
                "error_fault_alarm_msg": techno_response.registers[6],
                "error_mimo": techno_response.registers[5]
            }
            return details
        finally:
            self.techno_client.close()


if __name__ == '__main__':
    obj = TechnoModbusLiftController()
    if obj.techno_set_com_port('COM1'):
        details = obj.techno_get_lift_details()
        print(details)
    else:
        print("Failed to connect to COM3")

