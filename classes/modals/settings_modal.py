from classes.modals import base_modal
import tkinter as tk
from tkinter import messagebox
import json

class SettingsWindow(base_modal.ModalWindow):
	def body(self, master):
		"""
		Creates and formats everything pertaining to the modal except for
		the buttons.
		"""
		tk.Label(master, text="Device Mac Address:").grid(row=0)
		tk.Label(master, text="Timeular ApiKey:").grid(row=1)
		tk.Label(master, text="Timeular ApiSecure:").grid(row=2)

		self.read_data()

		self.address = tk.Entry(master)
		self.address.insert(0, self.address_value)
		self.address.grid(row=0, column=1)
		
		self.apikey = tk.Entry(master)
		self.apikey.insert(0, self.apikey_value)
		self.apikey.grid(row=1, column=1)

		self.apisecret = tk.Entry(master)
		self.apisecret.insert(0, self.apisecret_value)
		self.apisecret.grid(row=2, column=1)

		return self.address # initial focus

	def read_data(self):
		try:
			with open('data.json') as json_file:
				data = json.load(json_file)
				self.address_value = data['device_mac']
				self.apikey_value = data['apiKey']
				self.apisecret_value = data['apiSecret']
		except Exception:
			self.address_value = ""
			self.apikey_value = ""
			self.apisecret_value = ""
			pass

	def button_box(self):
		"""
		Creates the format and style of our buttons
		"""
		box = tk.Frame(self)

		save_button = tk.Button(box, text="Save", width=10,
			command=self.save,
			default=tk.ACTIVE)
		save_button.pack(side=tk.LEFT, padx=5,pady=5)
		cancel_button = tk.Button(box, text="Cancel", width=10,
			command=self.cancel)
		cancel_button.pack(side=tk.LEFT, padx=5, pady=5)
		self.bind("<Return>", self.save)
		box.pack()

	def save(self, event=None):
		"""
		"""
		data = {}
		data['device_mac'] = self.address.get()
		data['apiKey'] = self.apikey.get()
		data['apiSecret'] = self.apisecret.get()

		with open('data.json', 'w') as outfile:
			json.dump(data, outfile)

		self.cancel()