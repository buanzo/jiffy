#!/usr/bin/python3
"""Tkinter-based client for Jiffy.

The original implementation relied heavily on global variables and
"from tkinter import *" imports.  This rewrite encapsulates state inside a
``main`` function, uses explicit ``tkinter`` imports and keeps only the
required symbols.
"""

__author__ = "Arturo 'Buanzo' Busleiman <buanzo@buanzo.com.ar> PUBKEY:6857704D@keys.gnupg.net"
__version__ = "0.1.0"

import sys
import time
import threading
import queue
import tkinter as tk
from tkinter import font

from JiffyClient import JiffyClient, JiffyConfigError, JiffyVerificationError


JIFFYRECEIVEPOLLTIME = 5


def main() -> None:
    """Run the Tkinter user interface."""

    print("JiffyClient: initializing")
    jc = JiffyClient()
    print("JiffyClient: reading configuration")
    try:
        jc.readConfig()
    except JiffyConfigError as e:
        print(f"JiffyClient: configuration error: {e}")
        sys.exit(1)
    print("JiffyClient: checking GnuPG Setup")
    jc.checkGPGSetup()
    print("JiffyClient: obtaining server version")
    try:
        jc.getServerVersion()
    except JiffyVerificationError as e:
        print(f"JiffyClient: server version verification failed: {e}")
        sys.exit(1)
    print("JiffyClient: Starting session")
    jc.startSession()

    dataQueues: dict[int, queue.Queue] = {}
    workQueue: queue.Queue = queue.Queue()
    chatWindows: dict[int, tk.Toplevel] = {}
    KEY_TO_INDEX: dict[str, int] = {}
    AWA = True

    top = tk.Tk()

    class Listbox(tk.Listbox):
        def autowidth(self, maxwidth: int) -> None:
            f = font.Font(font=self.cget("font"))
            pixels = 0
            for item in self.get(0, "end"):
                pixels = max(pixels, f.measure(item))
            pixels += 10
            width = int(self.cget("width"))
            for w in range(0, maxwidth + 1, 5):
                if self.winfo_reqwidth() >= pixels:
                    break
                self.config(width=width + w)

    def on_after_chatWindow(ndx: int) -> None:
        ndx = int(ndx)
        index = int(ndx) + 1
        while dataQueues[index].qsize() > 0:
            jiffy = dataQueues[index].get(timeout=0.2)
            datum = jiffy[1]
            msg = jiffy[2]
            chatWindows[ndx].t1.insert(tk.END, f"{datum}: {msg}\n")
            chatWindows[ndx].t1.yview(tk.END)
        chatWindows[ndx].after(500, lambda idx=ndx: on_after_chatWindow(idx))

    def onEnter(event: tk.Event) -> None:
        index = int(event.widget.name.split("|")[0])
        uid = event.widget.name.split("[")[1].split("]")[0]
        msg = event.widget.get()
        chatWindows[index].t1.insert(tk.END, f"---> {msg}\n")
        chatWindows[index].t1.yview(tk.END)
        event.widget.delete(0, tk.END)
        jiffies = [(uid, msg)]
        workQueue.put(jiffies)

    def dblClickMethod(event: tk.Event) -> None:
        index = int(event.widget.curselection()[0])
        wmTitle = "Jiffy Chat: " + event.widget.get(index)
        chatWindows[index] = tk.Toplevel()
        chatWindows[index].t1 = tk.Text(chatWindows[index], width=60)
        chatWindows[index].t1.pack()
        chatWindows[index].t1.insert(tk.END, f"*** {wmTitle} ***\n\n")
        chatWindows[index].t1.yview(tk.END)
        chatWindows[index].l1 = tk.Label(chatWindows[index], text="REPLY:")
        chatWindows[index].l1.pack(side=tk.LEFT)
        chatWindows[index].e1 = tk.Entry(chatWindows[index], bd=1, width=48)
        chatWindows[index].e1.pack(side=tk.LEFT)
        chatWindows[index].e1.name = str(index) + "|" + wmTitle
        chatWindows[index].e1.bind("<Return>", onEnter)
        chatWindows[index].e1.focus()
        chatWindows[index].after(500, lambda idx=index: on_after_chatWindow(idx))
        chatWindows[index].wm_title(wmTitle)

    Lb1 = Listbox(top)
    Lb1.config(height=30)

    jc.GPG.decode_errors = "replace"
    public_keys = jc.GPG.list_keys()
    jc.GPG.decode_errors = "strict"

    i = 0
    for key in public_keys:
        if key["trust"] in ("f", "u"):
            i += 1
            s = "[" + key["keyid"] + "]" + key["uids"][0]
            Lb1.insert(i, s)
            dataQueues[i] = queue.Queue()
            KEY_TO_INDEX[key["keyid"]] = int(i)

    Lb1.autowidth(250)
    Lb1.pack()

    def threaded_jiffyReceiveDispatcher() -> None:
        jiffies = []
        while AWA:
            try:
                jiffies = jc.receiveJiffies()
            except Exception:
                pass
            if jiffies is None:  # NONE flags error. len(jiffies)==0 means no jiffies.
                top.quit()
            if jiffies and len(jiffies) > 0:
                for jiffy in jiffies:
                    if jiffy[0] in KEY_TO_INDEX:
                        dataQueues[KEY_TO_INDEX[jiffy[0]]].put(jiffy)
            time.sleep(JIFFYRECEIVEPOLLTIME)

    def threaded_jiffySendDispatcher() -> None:
        while AWA:
            if workQueue.qsize() > 0:
                jiffies = workQueue.get(timeout=0.2)
                try:
                    jc.sendJiffies(jiffies)
                except Exception:
                    pass
            time.sleep(0.5)

    def on_after_LB1() -> None:
        for idx in dataQueues.keys():
            if dataQueues[idx].qsize() > 0:
                Lb1.itemconfig(idx - 1, bg="white", fg="red")
            else:
                Lb1.itemconfig(idx - 1, bg="white", fg="black")
        Lb1.after(500, on_after_LB1)

    def quit_app(event: tk.Event | None = None) -> None:
        top.quit()

    Lb1.bind("<Double-Button-1>", dblClickMethod)
    Lb1.after(100, on_after_LB1)

    th = threading.Thread(target=threaded_jiffyReceiveDispatcher)
    th.start()
    wth = threading.Thread(target=threaded_jiffySendDispatcher)
    wth.start()

    top.wm_title("Jiffy Client GUI (tkinter)")
    top.bind("<Control-c>", quit_app)
    try:
        top.mainloop()
    except KeyboardInterrupt:
        top.quit()

    print("JiffyClient: exiting... please wait.")
    # We use the boolean "AWA" inside the threaded function for exit control
    # Yes, AWA means Are We Alive?
    AWA = False

    jc.endSession()

    th.join()
    wth.join()


if __name__ == "__main__":
    main()

