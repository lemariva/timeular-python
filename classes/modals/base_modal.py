import tkinter as tk

class ModalWindow(tk.Toplevel):
	"""
	The basic modal window which all others are inherited from.
	"""
	def __init__(self, parent, title=None):
		tk.Toplevel.__init__(self, parent)
		self.transient(parent)
		self.sock = None
		self.server = None
		self.error_message = None

		if title:
			self.title(title)

		self.parent = parent
		self.result = None

		body = tk.Frame(self)

		self.initial_focus = self.body(body)
		body.pack(padx=5,pady=5)

		self.button_box()

		self.grab_set()

		if not self.initial_focus:
			self.initial_focus = self

		self.protocol('WM_DELETE_WINDOW', self.cancel)
		self.geometry("+%d+%d" % (
			parent.winfo_rootx()+50,
			parent.winfo_rooty()+50))

		self.initial_focus.focus_set()
		self.wait_window(self)

	def cancel(self, event=None):
		"""
		Destroys modal when called
		"""
		self.destroy()
