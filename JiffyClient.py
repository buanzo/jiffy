#!/usr/bin/python3

__author__ = "Arturo 'Buanzo' Busleiman <buanzo@buanzo.com.ar> PUBKEY:6857704D@keys.gnupg.net"
__version__ = "0.1.0"

import configparser
import requests
import gnupg
import sys
import time
import logging
import re
import uuid
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from datetime import datetime

class JiffyClient:

  def __init__(self):
    self.SERVER_URL = ''
    self.CONFIG = configparser.ConfigParser()
    self.GPG = None
    self.regex_SIGNEDTEXT = re.compile('-----BEGIN PGP SIGNED MESSAGE-----\nHash:(.*)\n\n(.*)\n-----BEGIN PGP SIGNATURE-----\nVersion: (.*)\n\n')
    self.lastInSigTimestamp = None #WARNING: UTC TZ. make sure HOW you use this, btw.
    self.lastInSigTimestamp_text = '' # same as above but in text version
    self.SERVER_VERSION = ''
    self.defaultRequestHeaders = {'User-Agent':'JiffyClient/0.1'}
    self.sessionUUIDS = ''
    self.HTTPSESSION = requests.Session()

  def extractSignedText(self,verified,text):
    self.lastInSigTimestamp = None
    self.lastInSigTimestamp_text = ''
    if verified.trust_level is not None and verified.trust_level >= verified.TRUST_FULLY:
      try:
        m = self.regex_SIGNEDTEXT.search(text)
      except:
        return None
      self.lastInSigTimestamp_text = time.asctime(time.gmtime(float(verified.sig_timestamp)))
      self.lastInSigTimestamp = verified.sig_timestamp
      return m.group(2)
    else:
      return None

  def readConfig(self):
    try:
      self.CONFIG.read('JiffyClient.conf')
    except:
      print("JiffyClient: JiffyClient.conf could not be read from current directory.")
      sys.exit(1)
    self.SERVER_URL=self.CONFIG['DEFAULT']['Server'] or 'https://jiffy.mailfighter.net:11443'
    self.SERVER_KEY=self.CONFIG['DEFAULT']['ServerPubkeyId'] or None
    try:
      self.CLIENT_KEY=self.CONFIG['jiffyclient']['LocalPubkeyId'] or None
    except:
      print("Please edit the LocalPubkeyId parameter of the jiffyclient section of JiffyClient.conf")
      sys.exit(7)
    if self.SERVER_URL.endswith('/'): self.SERVER_URL=self.SERVER_URL[:-1]
    if self.SERVER_KEY==None or self.CLIENT_KEY==None:
      print("JiffyClient: JiffyClient.conf lacks Local or Server pubkey IDs. Exiting.")
      sys.exit(1)
    
  def checkGPGSetup(self):
#    self.GPG = gnupg.GPG(use_agent=True,verbose=self.CONFIG['DEFAULT'].getboolean('VerboseGPG'))
    self.GPG = gnupg.GPG(use_agent=True,verbose=False)
    self.GPG.encoding = 'utf-8'
    if len(self.GPG.list_keys(True)) <= 0:
      print("JiffyClient: No GnuPG Private key available. Please setup gnupg.")
      sys.exit(2)
    else:
      print("JiffyClient: GnuPG Private Keys available.")

  def gpgDecryptAndVerify(self,textToDecrypt): #used only for SERVER signed messages
    decrypted = self.GPG.decrypt(textToDecrypt)
    if decrypted.trust_level is not None and decrypted.trust_level >= decrypted.TRUST_FULLY and decrypted.key_id==self.SERVER_KEY:
      #print("[JiffyClient] Signing key matches ServerPubKey:",decrypted.key_id)
      return(decrypted)
    else:
      return None

  def gpgDecryptWithTrustCheck(self,textToDecrypt): #used only for incoming jiffies
    decrypted = self.GPG.decrypt(textToDecrypt)
    if decrypted.trust_level is not None and decrypted.trust_level >= decrypted.TRUST_FULLY:
      #print("[JiffyClient] Signing key matches ServerPubKey:",decrypted.key_id)
      return(decrypted)
    else:
      return None

  def gpgVerifyAndExtractText(self,data):
    verified = self.GPG.verify(data)
    if not verified:
      print("JiffyClient: ERROR: gpgVerify: signed response cannot be verified. Exiting...")
      sys.exit(3)
    else:
      return(self.extractSignedText(verified,data))

  def gpgSignAndEncrypt(self,recipient,data):
    encAsciiData = self.GPG.encrypt(data,recipient,sign=self.CLIENT_KEY)
    return(str(encAsciiData))

  def getServerVersion(self):
    try:
      r = self.HTTPSESSION.get(self.SERVER_URL+"/JiffyVersion",verify=True,headers=self.defaultRequestHeaders)
    except:
      print("JiffyClient: [ERROR] - Cannot connect to server ",self.SERVER_URL)
      sys.exit(4)
    self.SERVER_VERSION = self.gpgVerifyAndExtractText(data=r.text)
    print("JiffyClient: Server",self.SERVER_URL," -",self.SERVER_VERSION," (Signature Timestamp:",self.lastInSigTimestamp_text,")")

  def startSession(self):
    initialRSTR = str(uuid.uuid4())
    payload = {'data': self.gpgSignAndEncrypt(recipient=self.SERVER_KEY,data=initialRSTR)}
    r = self.HTTPSESSION.post(self.SERVER_URL+"/JiffySession",data=payload,headers=self.defaultRequestHeaders,timeout=5)
    self.sessionUUIDS=self.gpgDecryptAndVerify(r.text)
    if self.sessionUUIDS == None:
      print("JiffyClient: [ERROR]. Is the GPG Agent running? \"eval $(gpg-agent --daemon)\". Alternatively, verify entire trust chain.")
      sys.exit(5)
    self.startSession2()
    return None
    
  def startSession2(self):
    payload = {'data': self.gpgSignAndEncrypt(recipient=self.SERVER_KEY,data=str(self.sessionUUIDS))}
    r = self.HTTPSESSION.post(self.SERVER_URL+"/JiffySession2",data=payload,headers=self.defaultRequestHeaders,timeout=5)
    
  def endSession(self):
    payload = {'session': self.gpgSignAndEncrypt(recipient=self.SERVER_KEY,data=str(self.sessionUUIDS))}
    r = self.HTTPSESSION.post(self.SERVER_URL+"/JiffyBye",data=payload,headers=self.defaultRequestHeaders,timeout=5)
    self.sessionUUIDS=None

  def sendJiffies(self,jiffies):
    jTop = ET.Element('Jiffies')
    for jiffie in jiffies:
      nodo = ET.SubElement(jTop, 'jiffy')
      nodo.text=self.gpgSignAndEncrypt(recipient=jiffie[0],data=jiffie[1])
      nodo.set('rcpt',jiffie[0]) # TODO: With extra attributes we can have routing and federation, etc
    el_xml = ET.tostring(jTop,encoding="utf-8", method="xml")
    payload = {'session':self.gpgSignAndEncrypt(recipient=self.SERVER_KEY,data=str(self.sessionUUIDS)),'data': self.gpgSignAndEncrypt(recipient=self.SERVER_KEY,data=el_xml)}
    r = self.HTTPSESSION.post(self.SERVER_URL+"/JiffySend",data=payload,headers=self.defaultRequestHeaders,timeout=30)

  def returnJiffy(self,jiffy):
    decrypted = self.gpgDecryptWithTrustCheck(jiffy.text)
    fecha=str(datetime.fromtimestamp(int(decrypted.sig_timestamp)))
    return([decrypted.key_id,fecha,str(decrypted)])
    
  def receiveJiffies(self):
    jiffies = []
    payload = {'session': self.gpgSignAndEncrypt(recipient=self.SERVER_KEY,data=str(self.sessionUUIDS))}
    r = self.HTTPSESSION.post(self.SERVER_URL+"/JiffyRecv",data=payload,headers=self.defaultRequestHeaders,timeout=30)
    decrypted = self.gpgDecryptAndVerify(r.text)
    if decrypted==None:
      # request new session
      self.startSession()
      r = self.HTTPSESSION.post(self.SERVER_URL+"/JiffyRecv",data=payload,headers=self.defaultRequestHeaders,timeout=30)
      decrypted = self.gpgDecryptAndVerify(r.text)
      if decrypted==None:
        return None # by default we return [] so None can be used as error flag
    if decrypted.trust_level is not None and decrypted.trust_level >= decrypted.TRUST_FULLY:
      jTop = ET.fromstring(str(decrypted))
      if jTop.tag=='Jiffies':
        jCount = jTop.get('count') #number of jiffies
#        print("There are "+jCount+" Jiffies available")
        for jiffy in jTop.findall('jiffy'):
          jiffies.append(self.returnJiffy(jiffy))
        return(jiffies)     
