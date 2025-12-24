import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from logger import LoggerHelper
import threading

class JobScraperGUI:
    def clear_url(self):
        self.url_entry.delete(0, tk.END)

    def __init__(self, master):
        self.master = master
        self.master.title("Job Scraper GUI")
        self.master.geometry("450x250")

        # Radio button variable
        self.choice_var = tk.StringVar(value="Linkedin_job")

        # -----------------------------
        # Radiobuttons (LinkedIn, DOU, Indeed)
        # -----------------------------
        ttk.Label(master, text="Select Job Source:", font=("Arial", 12)).pack(pady=5)

        radio_frame = ttk.Frame(master)
        radio_frame.pack()

        ttk.Radiobutton(radio_frame, text="LinkedIn", variable=self.choice_var,
                        value="Linkedin_job").grid(row=0, column=0, padx=10)

        ttk.Radiobutton(radio_frame, text="DOU", variable=self.choice_var,
                        value="Dou_job").grid(row=1, column=0, padx=10)
        
        ttk.Radiobutton(radio_frame, text="Djinni", variable=self.choice_var,
                        value="Djinni_job").grid(row=2, column=0, padx=10)

        ttk.Radiobutton(radio_frame, text="Indeed", variable=self.choice_var,
                        value="Indeed_job").grid(row=3, column=0, padx=10)

        # -----------------------------
        # URL input
        # -----------------------------
        ttk.Label(master, text="Start URL (optional):", font=("Arial", 12)).pack(pady=5)

        url_frame = ttk.Frame(master)
        url_frame.pack(pady=5)

        self.url_entry = ttk.Entry(url_frame, width=40)
        self.url_entry.grid(row=0, column=0, padx=(0, 5))

        clear_button = ttk.Button(
           url_frame,
           text="Clear",
           command=self.clear_url
        )
        clear_button.grid(row=0, column=1)

        # -----------------------------
        # Run Button
        # -----------------------------
        self.run_button = ttk.Button(master, text="Run Scraper", command=self.run_scraper)
        self.run_button.pack(pady=15)

    # ---------------------------------------------------------
    # Run the console script through subprocess
    # ---------------------------------------------------------
    def run_scraper(self):
        choice = self.choice_var.get()
        url = self.url_entry.get().strip()

        cmd = ["python", "main.py", "-gui=yes", f"-choice={choice}"]

        self.logger = LoggerHelper.get_logger(choice.lower()+"_gui")
        if url:
            cmd.append(f"-url={url}")
        self.logger.info(f"cmd: {cmd}")

        try:
            self.logger.info("Scraper is starting...")
            self.run_button.config(state=tk.DISABLED)

            def stream_reader(stream, prefix):
                for line in iter(stream.readline, ""):
                    line = line.rstrip()
                    if line:
                        self.logger.info(f"{prefix} {line}")
                stream.close()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,             # line-buffered
            )

            # Read STDOUT/STDERR live
            t1 = threading.Thread(target=stream_reader, args=(process.stdout, "[OUT]"))
            t2 = threading.Thread(target=stream_reader, args=(process.stderr, "[ERR]"))
            t1.start()
            t2.start()

            process.wait()
            t1.join()
            t2.join()

            self.run_button.config(state=tk.NORMAL)
            messagebox.showinfo("Done", "Scraper has finished. Check console/log output.")

        except Exception as e:
            self.logger.info(f"Failed to start scraper:\n{e}")
            messagebox.showerror("Error", f"Failed to start scraper:\n{e}")


# ---------------------------------------------------------
# Run GUI
# ---------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    gui = JobScraperGUI(root)
    root.mainloop()