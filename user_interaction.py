class UserInteraction:
    def wait_for_user_login(self):
        """Called when user must log in manually (e.g., LinkedIn)."""
        raise NotImplementedError
    def show_message(self, message):
        """Called to show message."""
        raise NotImplementedError

class ConsoleUserInteraction(UserInteraction):
    def wait_for_user_login(self):
        input("Please log in in the opened browser, then press Enter...")
    def show_message(self, message):
        print(message)

from tkinter import messagebox

class GUIUserInteraction(UserInteraction):
    def wait_for_user_login(self):
        messagebox.showinfo(
            "Login Required",
            "Please log in in the opened browser.\nClick OK when done."
        )
    def show_message(self, message):
        messagebox.showinfo(
            "Message",
            message
        )
