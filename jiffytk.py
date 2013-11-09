#!/usr/bin/python3

__author__ = "Arturo 'Buanzo' Busleiman <buanzo@buanzo.com.ar> PUBKEY:6857704D@keys.gnupg.net"
__version__ = "0.1.0"

import gnupg
import configparser
import requests
import gnupg
import sys
import time
import logging
import re
import uuid
import xml.etree.ElementTree as ET
import tkinter
from tkinter import *
from tkinter import font
from urllib.parse import urlparse
from datetime import datetime

from JiffyClient import JiffyClient

#to enable logging to jiffyclient.log
#logging.basicConfig(level=logging.DEBUG, filename="jiffyclient.log",filemode="w", format="%(asctime)s %(levelname)-5s %(name)-10s %(threadName)-10s %(message)s")

print("JiffyClient: initializing")
jc = JiffyClient()
print("JiffyClient: reading configuration")
jc.readConfig()
print("JiffyClient: checking GnuPG Setup")
jc.checkGPGSetup()
print("JiffyClient: obtaining server version")
jc.getServerVersion()
print("JiffyClient: Starting session")
jc.startSession()


#example how to send a jiffy to self
#jiffies = [(jc.CLIENT_KEY,'HELLO SCREEN CAPTURE')]
#jc.sendJiffies(jiffies)
#if len(sys.argv)==4 and sys.argv[1]=="send":
#  rcpt=sys.argv[2]
#  msg=sys.argv[3]
#  jiffies = [(rcpt,msg)]
#  jc.sendJiffies(jiffies)
#  print("JiffyClient: Jiffy sent")
        
#jiffies = jc.receiveJiffies()

# Here comes the UI code. i suck at this.

def dblClickMethod(self):
  print("SELF",self.__dict__)
  print("\nSELF WIDGET",self.widget.__dict__)
  print("\nSELF WIDGET DATA",self.widget.curselection())
#print("\n.get() =",self.widget.get(self.widget.curselection()))
  index = self.widget.curselection()[0]
  print("DOUBLE CLICK TEXT=",self.widget.get(index))

top = Tk()

class Listbox(tkinter.Listbox):
  def autowidth(self,maxwidth):
    f = font.Font(font=self.cget("font"))
    pixels = 0
    for item in self.get(0, "end"):
      pixels = max(pixels, f.measure(item))
    # bump listbox size until all entries fit
    pixels = pixels + 10
    width = int(self.cget("width"))
    for w in range(0, maxwidth+1, 5):
      if self.winfo_reqwidth() >= pixels:
        break
      self.config(width=width+w)

Lb1 = Listbox(top)
Lb1.config(height=30)
# Create a contactlist out of the public keyring. Use a suitable format
# for items. we will use a regex to extract the proper long format keyid
jc.GPG.decode_errors='replace' # we need to do this because of foreign characters.
public_keys = jc.GPG.list_keys()
jc.GPG.decode_errors='strict'
i = 0
for key in public_keys:
  if key['trust']=='f' or key['trust']=='u':
    for uid in key['uids']:
      i += 1
      s = '['+key['keyid']+']'+uid
      Lb1.insert(i,s)

# autofix width
Lb1.autowidth(250)
Lb1.pack()

# dblClickMethod() binded to proper event on Listbox()
Lb1.bind('<Double-Button-1>', dblClickMethod)

# main UI loop
top.mainloop()

# end session
jc.endSession()
