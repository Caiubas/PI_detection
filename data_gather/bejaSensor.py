import numpy as np
from movella_dot_py.core.sensor import MovellaDOTSensor
import asyncio

class BejaSensor(MovellaDOTSensor):
    def __init__(self, config = None):
        super().__init__(config)
        self.stillness_sensibility = 0.8 ##todo separar sensibilidade para cada parametro
        self.gravity = 10.2 ##todo captar gravidade pelo proprio sensor (free fall acceleration?)
        self.calibrated = False

    def stillness_check(self, sender: int, data: bytearray):
        """Handle incoming sensor data notifications"""
        try:
            if self.data_collector:
                parsed_data = self.data_collector.parser.parse(data)
                self.data_collector.add_data(data)

                print(f"\nReal-time Sensor Data from {self._device_tag} ({self._device_address}):")

                if parsed_data.quaternion:
                    print(f"Quaternion (w,x,y,z): {parsed_data.quaternion.w:.3f}")

                if parsed_data.acceleration:
                    print(f"Acceleration (x,y,z): {np.sqrt(parsed_data.acceleration.x**2+parsed_data.acceleration.y**2+parsed_data.acceleration.z**2):.2f}")

                if np.sqrt(parsed_data.acceleration.x**2+parsed_data.acceleration.y**2+parsed_data.acceleration.z**2) + \
                    np.abs(parsed_data.quaternion.w) < self.stillness_sensibility + self.gravity: ##todo verificar se o quartenion eh velocidade ou posicao
                    self.calibrated = True
                    ##todo colocar time minimo para confirmar calibracao de todos simultaneamente


        except Exception as e:
            print(f"Error handling notification: {e}")

    async def calibrate(self):
        """Start measurement with notification handling"""
        print("Starting calibration...")
        self.calibrated = False

        payload_char = self._get_payload_characteristic(self.config.payload_mode)

        await self.client.start_notify(
            payload_char,
            self.stillness_check
        )

        await self.client.write_gatt_char(
            self.chars.MEASUREMENT_CONTROL,
            bytearray([1, 1, self.config.payload_mode])
        )


    def set_offset(self): #todo setar offsets para quando estiver calibrado
        pass