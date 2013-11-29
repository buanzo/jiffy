#!/usr/bin/python3
#TODO: multithreading. receive jiffies and dispatch message windows, etc.
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
import threading
import queue
from tkinter import *
from tkinter import font
from urllib.parse import urlparse
from datetime import datetime

from JiffyClient import JiffyClient

global jc
global top
global dataQueues
global workQueue
global chatWindows
global KEY_TO_INDEX
global AWA

AWA = True

# the index will correspond to Lb1 item index and will be a tk reference to a chat window or data queue
dataQueues = {}
workQueue = queue.Queue()
chatWindows = {} 
KEY_TO_INDEX = {}

JIFFYRECEIVEPOLLTIME=5

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
#jiffies = [(jc.CLIENT_KEY,'HELLO SCREEN CAPTURE'),(jc.CLIENT_KEY,'another message'),(jc.CLIENT_KEY,'third and final')]
#jc.sendJiffies(jiffies)
#if len(sys.argv)==4 and sys.argv[1]=="send":
#  rcpt=sys.argv[2]
#  msg=sys.argv[3]
#  jiffies = [(rcpt,msg)]
#  jc.sendJiffies(jiffies)
#  print("JiffyClient: Jiffy sent")
        
#jiffies = jc.receiveJiffies()

# Here comes the UI code. i suck at this.


def on_after_chatWindow(ndx):
  ndx=int(ndx)
  index=int(ndx)+1
  while dataQueues[index].qsize() > 0:
    jiffy = dataQueues[index].get(timeout=0.2)
    datum = jiffy[1]
    msg = jiffy[2]
    chatWindows[ndx].t1.insert(END,'%s: %s\n' % (datum,msg))
    chatWindows[ndx].t1.yview(END)
  chatWindows[ndx].after(500,on_after_chatWindow,ndx)

def onEnter(self):
  index = int(self.widget.name.split('|')[0])
  uid = self.widget.name.split('[')[1].split(']')[0]
  msg = self.widget.get()
  chatWindows[index].t1.insert(END,"---> %s\n" % msg)
  chatWindows[index].t1.yview(END)
  self.widget.delete(0,END)
  jiffies = [(uid,msg)]
  workQueue.put(jiffies)

def dblClickMethod(self):
  index = int(self.widget.curselection()[0])
  wmTitle = "Jiffy Chat: "+self.widget.get(index)
  chatWindows[index] = Toplevel()
  chatWindows[index].t1 = Text(chatWindows[index],width=60)
  chatWindows[index].t1.pack()
  chatWindows[index].t1.insert(END,"*** %s ***\n\n" % wmTitle)
  chatWindows[index].t1.yview(END)
  chatWindows[index].l1 = Label(chatWindows[index],text="REPLY:")
  chatWindows[index].l1.pack(side=LEFT)
  chatWindows[index].e1 = Entry(chatWindows[index],bd=1,width=48)
  chatWindows[index].e1.pack(side=LEFT)
  chatWindows[index].e1.name=str(index)+"|"+wmTitle
  chatWindows[index].e1.bind('<Return>',onEnter)
  chatWindows[index].e1.focus()
  chatWindows[index].after(500,on_after_chatWindow,index)
  chatWindows[index].wm_title(wmTitle)
    

top = Tk()

# overload the tkinter.Listbox class with a new autowidth() method
# taken from somewhere, TODO: add url
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

# Create a contactlist out of the public keyring. Use a suitable format
# for items. we will use a regex to extract the proper long format keyid
Lb1 = Listbox(top)
Lb1.config(height=30)

# we need to do this because of foreign characters
jc.GPG.decode_errors='replace'
public_keys = jc.GPG.list_keys()
jc.GPG.decode_errors='strict'

# only load fully/ultimately trusted keys. first UID only.
i = 0
for key in public_keys:
  if key['trust']=='f' or key['trust']=='u':
    i += 1
    s = '['+key['keyid']+']'+key['uids'][0]
    # insert the contact list item...
    Lb1.insert(i,s)
    # ... and create corresponding dataQueues[i]
    dataQueues[i]=queue.Queue(maxsize=0)
    KEY_TO_INDEX[key['keyid']]=int(i)

# autofix width
Lb1.autowidth(250)
Lb1.pack()

# threaded function that will poll for incoming jiffies
# and put()s jiffies into the corresponding dataqueue
def threaded_jiffyReceiveDispatcher():
  jiffies = []
  while AWA==True:
    try:
      jiffies = jc.receiveJiffies()
    except:
      pass
    if jiffies==None: #NONE flags error. len(jiffies)==0 means no jiffies.
      top.quit()
    if len(jiffies) > 0:
      # we got jiffies, let's send the data to the proper dataqueue
      for jiffy in jiffies:
        if jiffy[0] in KEY_TO_INDEX: # incoming jiffy's key is in local contact list
          dataQueues[KEY_TO_INDEX[jiffy[0]]].put(jiffy)
    time.sleep(JIFFYRECEIVEPOLLTIME)
    
# threaded function that sends jiffies
def threaded_jiffySendDispatcher():
  while AWA==True:
    if workQueue.qsize() > 0:
      jiffies = workQueue.get(timeout=0.2)
      try:
        jc.sendJiffies(jiffies)  
      except:
        pass
    time.sleep(0.5)

def on_after_LB1():
  for i in dataQueues.keys():
    if dataQueues[i].qsize() > 0:
      Lb1.itemconfig(i-1, bg='white', fg='red')
    else:
      Lb1.itemconfig(i-1,bg='white',fg='black')
  Lb1.after(500,on_after_LB1)
 
# dblClickMethod() binded to proper event on Listbox()
# FIX: before binding this event, we might have to setup the threading/queue processing
# FIX: and if an incoming jiffie is received, create a chat window... or maybe turn the
# FIX: corresponding Lb1/contaclist item to bold ?
Lb1.bind('<Double-Button-1>', dblClickMethod)
Lb1.after(100,on_after_LB1)

th = threading.Thread(target=threaded_jiffyReceiveDispatcher)
th.start()
wth = threading.Thread(target=threaded_jiffySendDispatcher)
wth.start()

def quit(event):
  top.quit()

# main UI loop
top.wm_title("Jiffy Client GUI (tkinter)")
top.bind('<Control-c>', quit)
try:
  top.mainloop()
except KeyboardInterrupt:
  top.quit()

print("JiffyClient: exiting... please wait.")

# We use the global boolean "AWA" inside the threaded function for exit control
# Yes, AWA means Are We Alive?
AWA=False

# end session
jc.endSession()

# Wait for threads to finish...
th.join()
wth.join()

