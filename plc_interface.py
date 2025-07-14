from pycomm3 import CommError, LogixDriver
import time

PLC_IP = '192.168.1.10'

def require_connection(func):
    def wrapper(self, *args, **kwargs):
        if self.plc is None:
            print(f"❌ PLC not connected: can't run '{func.__name__}'")
            return False
        return func(self, *args, **kwargs)
    return wrapper

class PLCInterface:
    def __init__(self, ip):
        self.ip = ip
        self.plc = None

    def read_array(self, base_tag, length):
        return [self.read(f'{base_tag[:-1]}{i}]') for i in range(length)]




    def connect(self):
        try:
            self.plc = LogixDriver(self.ip)
            self.plc.open()  # 🔥 REQUIRED: registers session
            print(f"Connected to PLC at {self.ip}")
        except CommError as e:
            print(f"PLC connection failed: {e}")
            self.plc = None

    def disconnect(self):
        if self.plc:
            self.plc.close()
            self.plc = None


    @require_connection
    def start_pretension(self):
        writing = self.plc.write(('matlabPretensionEnable', 1))
        if writing and writing.value ==1:
            print("🚀 Pretension routine started.")
            return True
        else:
            print("❌ Pretension Failed")
            return False
        
    @require_connection
    def read(self,tag_name):
        try:
            if self.plc:
                return self.plc.read(tag_name)
        except Exception as e:
            print(f"Error reading tag {tag_name}: {e}")
        return None


    @require_connection
    def read_data_cache(self):

        data_flag = self.plc.read('NewDataFlag')
        if data_flag and data_flag.value == 1:
            data_matrix = []
            for row in range(6):
                row_data = []
                for col in range(10):
                    tag_name = f'DataCacheMatlab[{row},{col}]'
                    value = self.plc.read(tag_name)
                    row_data.append(value.value if value else None)
                data_matrix.append(row_data)
            self.plc.write(('NewDataFlag', 0))
            return data_matrix
        return None
    

    @require_connection
    def write_spinbox_values(self, spinbox_dict):
            print(spinbox_dict)
            try:
                mappings = {
                    "Pretension (Nm)": "matlabPretension",
                    "Torque Target (Nm)": "matlabTorqueSetpoint",
                    "Min Torque Threshold (Nm)": "matlabTorqueSetpoint",  
                    "Range of Motion (deg)": "matlabRange"
                }

                for label, tag in mappings.items():
                    if label in spinbox_dict:
                        val = float(spinbox_dict[label].get())
                        self.write(tag, val)

            except Exception as e:
                print(f"❌ Failed to write spinbox values: {e}")

    @require_connection
    def enable_test_mode(self, mode_value):
        try:
            self.plc.write('matlabTestMode', mode_value)
            self.plc.write('matlabTestingEnabled', 1)
            print(f"✅ Test Mode {mode_value} Enabled")
            return True
        except Exception as e:
            print(f"❌ Failed to enable test mode: {e}")
            return False
        
    @require_connection
    def disable_test_mode(self):
        try:
            self.plc.write('matlabTestingEnabled', 0)
            print("🛑 Test Mode Disabled")
            return True
        except Exception as e:
            print(f"❌ Failed to disable test mode: {e}")
            return False



    @require_connection
    def write(self, tag, value):
        try:
            result = self.plc.write((tag, value))
            if result and result.value == value:
                print(f"✅ Successfully wrote {value} to {tag}")
            else:
                print(f"⚠️ Wrote {value} to {tag}, but verification may have failed")
            return True
        except Exception as e:
            print(f"❌ Failed to write to {tag}: {e}")
            return False



    

