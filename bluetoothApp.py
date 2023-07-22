import numpy as np
import serial
import serial.tools.list_ports
import keyboard
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
import threading
import asyncio

# class handling the async thread that reads data from the serial port
class AsyncSerialPortReader():
    def __init__(self, serialobj : serial.Serial):
        self.ser = serialobj
        
        # populate the memory view dict with empty data
        self.memory_view = dict()
        banks = ['A']*16 + ['B']*16
        addresses = [x for x in range(16)] * 2
        for adr,bank in zip(addresses, banks):
            self.memory_view[f'{adr}{bank}'] = 0
    
    # continuously reads data from the serial port, and decodes it
    async def read_serial_data(self):
        while True:
            if self.ser.in_waiting > 0:
                # read a line
                line = self.ser.readline().decode().rstrip('\r\n')
                # begin decoding the values
                line = int(line, base=16)
                bank = 'A' if (line & (1<<12))>0 else 'B'
                
                adrbin = bin((line & int('0x0F00', base=16)) | int('0x8000', base=16))
                # reverse adrbin because it is in big endian
                adr = int(adrbin[9:5:-1], base=2)
                
                valbin = bin((line & int('0x00FF', base=16))| int('0x8000', base=16))
                # reverse val because it is in big endian
                val = int(valbin[-1:9:-1], base=2)
                
                # update the value in our memory_view dict
                self.memory_view[f'{adr}{bank}'] = val
            
            # await asyncio.sleep(0.1)
    
    # creates the asyncio event loop
    async def start_reading(self):
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.read_serial_data())
        await task
    
    # starts the event loop in a separate thread
    async def start_event_loop(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.start_reading())
        loop.run_forever()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("800x800")
        self.title("VDNX PP-1 ESP32 Interface")
        
        self.ser = serial.Serial()
        
        root = tk.Frame(self)
        root.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        
        # bluetooth menu frame
        bluetooth_frame = tk.Frame(root)
        bluetooth_frame.grid(row=0, column=0, sticky='ew')
        
        ##################
        # Begin Bluetooth Menu Frame
        
        # bluetooth port selection
        portlabel = tk.Label(bluetooth_frame, text="Bluetooth Serial Port:")
        portlabel.grid(row=0, column=0)
        
        self.port_var = tk.StringVar()
        self.port_dropdown = ttk.Combobox(bluetooth_frame, textvariable=self.port_var)
        self.port_dropdown.grid(row=0, column=1)
        self.update_ports()
        
        # refresh ports button
        refresh_port_button = tk.Button(bluetooth_frame, text='Refresh', command=self.update_ports)
        refresh_port_button.grid(row=0, column=2)
        
        # connect/disconnect buttons
        connect_port_button = tk.Button(bluetooth_frame, text='Connect', command=self.connect_port)
        connect_port_button.grid(row=0, column=3)
        disconnect_port_button = tk.Button(bluetooth_frame, text='Disconnect', command=self.disconnect_port)
        disconnect_port_button.grid(row=0, column=4)
        
        # connection status
        self.port_status = tk.StringVar(value='Status: Disconnected')
        self.port_status_label = tk.Label(bluetooth_frame, textvariable=self.port_status)
        self.port_status_label.grid(row=0, column=5)
        
        ##################
        # End Bluetooth Menu Frame
        
        # separator
        ttk.Separator(root, orient='horizontal').grid(row=1, column=0, sticky='ew', pady=5)
        
        # Mode Selection Menu Frame
        mode_select_frame = tk.Frame(root)
        mode_select_frame.grid(row=2, column=0, sticky='ew')
        
        ##################
        # Begin Mode Selection Menu Frame
        
        # mode select menu label
        mode_label = tk.Label(mode_select_frame, text='Mode Select:')
        mode_label.grid(row=0,column=0)
        
        # mode select radio buttons
        self.mode_var = tk.StringVar(value='listen')
        listen_rbutton = ttk.Radiobutton(mode_select_frame, text='Listen', variable=self.mode_var, value='listen', command=self.mode_change)
        listen_rbutton.grid(row=1,column=0)
        hijack_rbutton = ttk.Radiobutton(mode_select_frame, text='Hijack', variable=self.mode_var, value='hijack', command=self.mode_change)
        hijack_rbutton.grid(row=2, column=0)
                
        ##################
        # End Mode Selection Menu Frame
    
    def mode_change(self):
        if self.mode_var.get() == 'listen':
            print('listen mode')
        elif self.mode_var.get() == 'hijack':
            print('hijack mode')
        else:
            raise ValueError('mode_var has invalid value')
    
    def connect_port(self):
        if self.ser.is_open:
            self.ser.close()
        try:
            self.ser = serial.Serial(self.port_var.get(), timeout=1.0)
            self.ser.flush()
            self.port_status.set(f'Status: Connected to {self.port_var.get()}')
            # print('connected', self.port_var.get())
        except serial.SerialException:
            self.bell()
        except serial.SerialTimeoutException:
            self.bell()
        

    def disconnect_port(self):
        if self.ser.is_open:
            self.ser.close()
            self.port_status.set('Status: Disconnected')
            # print('disconnected')
        else:
            self.bell()
     
    def update_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        ports.sort()
        ports = tuple(ports)
        self.port_dropdown['values'] = ports

if __name__ == "__main__":
    app = App()
    app.mainloop()