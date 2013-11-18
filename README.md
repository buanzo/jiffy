jiffy
=====

Jiffy is a secure instant messaging system developed using OpenPGP and TLS, and based on Enigform/mod_openpgp.

The only jiffy server currently running is https://jiffy.mailfighter.net:11443

I have not yet released the JiffyServer code. Will try to do so in the next week weeks (that is, before the end of nov/2013)

0) make sure you have a working GnuPG setup (gpg4win and the standard gnupg packages are known to work fine).
1) Edit the JiffyClient.conf file. The default jyffy server and server public key IDs are https://jiffy.mailfighter.net:11443 / pub   4096R/74BA73D7 2013-10-22
      Key fingerprint = E4FC 80C3 54E7 CB3C 686E  D504 0C39 B831 74BA 73D7

2) Then:
	Jiffy by default uses the gpg-agent. Make sure it is available to JiffyClient.py's environment when you run it.
	If you use gpg4win make sure you are following proper procedure. As I do not intend to heavily support
	a closed source, propietary operating system such as Microsoft's Windows(R), I'll leave this up to you.

	Under Linux and other POSIX OSes you may just run this on any Bourne compatible shell:
		eval $(gpg-agent --daemon)

	Then you can run gpg-agent. It'll tell you if the Agent is indeed running and available. Now try ./JiffyClient.py

IMPORTANT:

The jiffy server needs to trust your keyid.

YOU need to trust the server's keyid.

In this initial release, the server does not know how to forward jiffies to other servers. We need to bootstrap a community of trusted servers
and develop federation/routing.

SO: Anyone you want to IM with using Jiffy, need to do that (add the server's keyid and trust it, or at least --lsign it).

You can always jiffy me at 025A4EB06857704D thru the aforementioned server, considering we establish trust beforehand.

There are no rate controls, no anti-spam, no nothing, cause all that works off gpg's trust model. ok? Oh, well, truth be told,
if you implement the jiffyserver behind a hardened Apache/nginx/lighttpd then nothing else is necessary.

Please send pull requests :)



