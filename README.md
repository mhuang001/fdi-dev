Processing Network Node Web API Server
==============

Thhis Web API Server for a data processing pipeline/network node provides interfaces to make a run request to and read results from a processing task in a processing node via web APIs.

_**Installation**_
for developers
```
cd /tmp
git clone ssh://git@mercury.bao.ac.cn:9005/mh/pns.git
cd pns
pip3 install -e .
```
for users
```
cd /tmp
git clone http://mercury.bao.ac.cn:9006/mh/pns.git
cd pns
pip3 install -e .
```

_**To Run Server**_

```
python3 pns.py --username=<username> --password=<password> [--ip=<host ip>] [--port=<port>]
```
or
```
python3 pns.py -u <username> -p <password> [-i <host ip>] [-o <port>]
```
in debugging mode:
```
python3 pns.py --username=foo --password=bar -v
```
or just
```
./startserver
```
to use the defaults.

Do not run debugging mode for production use.

The username and password are used when making run requests.

_**To Test**_


Start the server fresh in one terminal and in another terminal
```
./test [-u <username> -p <password> [-i <host ip>] [-o <port>]]
```
with default ip and port

_**Configuration**_
Host IP is 0.0.0.0 and port number 5000 by default. They are configurable in pnsconfig.py 

API
---
Suppose the server address and port are 127.0.0.1 and 5000, respectively:

<b>Get public information and access APIs</b>

<b>Return on Common Errors</b>

400
```
{'error': 'Bad request.', 'timestamp': ts}
```
401
```
{'error': 'Unauthorized. Authentication needed to modify.', 'timestamp': ts}
```
404
```
{'error': 'Not found.', 'timestamp': ts}
```
409
```
{'error': 'Conflict. Updating.', 'timestamp': ts}
```


Resources
---------

TBW
