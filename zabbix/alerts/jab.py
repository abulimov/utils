#!/usr/bin/python -W ignore
import sys,xmpp

list = sys.argv[1:]
to = list[0];
subj = list[1];
body = list[2];
type_ = list[3];

#import string
#print string.join(list)
# Google Talk constants
FROM_GMAIL_ID = "info@jabber.lan"
GMAIL_PASS = "123456"
GTALK_SERVER = "jabber.lan"

jid=xmpp.protocol.JID(FROM_GMAIL_ID);
cl=xmpp.Client(jid.getDomain(),debug=[]);
if not cl.connect((GTALK_SERVER,5222)):
    raise IOError('Can not connect to server.')
if not cl.auth(jid.getNode(),GMAIL_PASS):
    raise IOError('Can not auth with server.')

cl.send( xmpp.Message( to+"@"+GTALK_SERVER ,subj+" "+body+" "+type_ ) );
cl.disconnect();
