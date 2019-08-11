Processing Network Node Web API Server
==============

Thhis Web API Server for a data processing pipeline/network node provides interfaces to make a run request to and read results from a processing task in a processing node via web APIs.

_**Installation**_
for developers
```
cd /var
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
Install dependencies.

_**To Run FLASK Server**_

Edit pnsconfig.py if needed.

```
python3.6 pns/runflaskserver.py --username=<username> --password=<password> [--ip=<host ip>] [--port=<port>]
```
or
```
python3.6 pns/runflaskserver.py -u <username> -p <password> [-i <host ip>] [-o <port>]
```
in debugging mode:
```
python3.6 pns/runflaskserver.py --username=foo --password=bar -v
```
or just
```
./startserver
```
to use the defaults.

Do not run debugging mode for production use.

The username and password are used when making run requests.


_**Basic Configuration**_

When running Flask server, the host IP is 0.0.0.0 and port number 5000 by default. They are configurable in pnsconfig.py. Default configuration can be overrided by ~/local.py (in the same format. Copy pnsconfig.py to ~/local.py and edit to make local changes.)

_**To Test and Verify Installation**_


To run all tests in one go:

```
./test [-u <username> -p <password> [-i <host ip>] [-o <port>]] [options]
```

Tests can be done step-by-step:

1. Server Unit Test without needing the server to run:

```
/test -k server
```

2. Local Flask Server Functional Tests

Start the server fresh in one terminal and in another terminal run


test PUT initialization:
```
./test -k putinit
```
test POST In-server processing
```
./test -k post
```
test POST PTS processing
```
./test -k run
```
test GET Returning server init file, (config file, and prog file TBW)
```
./test -k getinit
```
test DELETE Clean-up the server by removing the input and output dirs
```
./test -k deleteclean
```

Run all tests in one go:
```
./test
```

3. Run the local tests with Apache

```
sudo service apache2 restart
```
then run the above with correct IP and port (edit ~/local.py or specifying in command line).

4. Run tests from a remote client

Install pns on a remote host, configure IP and port, then run the tests above.

_**PTS Configuration**_

To run a PTS shell script instead of the 'hello' demo, change the ```prog``` parameter in the config file

_**PTS API**_

---
Suppose the server address and port are 127.0.0.1 and 5000, respectively:

<b>Get public access APIs and information</b>

Run the Flask server in a terminal (see above) and open this in a browser:
http://127.0.0.1:5000/v0.4/
An online API documentation page similar to below is shown.

----------------------------------------
```
{
  "APIs": {
    "DELETE": [
      {
        "URL": "http://127.0.0.1:5000/v0.4/clean", 
        "description": " Removing traces of past runnings the Processing Task Software.\n    "
      }
    ], 
    "GET": [
      {
        "URL": "http://127.0.0.1:5000/v0.4/init", 
        "description": "initPTS file"
      }, 
      {
        "URL": "http://127.0.0.1:5000/v0.4/config", 
        "description": "configPTS file"
      }, 
      {
        "URL": "http://127.0.0.1:5000/v0.4/input", 
        "description": " returns names and contents of all files in the dir, 'None' if dir not existing. "
      }, 
      {
        "URL": "http://127.0.0.1:5000/v0.4/output", 
        "description": " returns names and contents of all files in the dir, 'None' if dir not existing. "
      }
    ], 
    "POST": [
      {
        "URL": "http://127.0.0.1:5000/v0.4/data", 
        "description": " generate post test product.\n    put the 1st input (see maketestdata in test_all.py)\n    parameter to metadata\n    and 2nd to the product's dataset\n    "
      }, 
      {
        "URL": "http://127.0.0.1:5000/v0.4/echo", 
        "description": "Echo"
      }, 
      {
        "URL": "http://127.0.0.1:5000/v0.4/run", 
        "description": " Generates a product by running script defined in the config as prog ('hello' for testing). Execution on the server host is in the pnshome directory and run result and status are returned.\n    "
      }
    ], 
    "PUT": [
      {
        "URL": "http://127.0.0.1:5000/v0.4/init", 
        "description": " Initialize the Processing Task Software by running the init script defined in the config. Execution on the server host is in the pnshome directory and run result and status are returned.\n    "
      }, 
      {
        "URL": "http://127.0.0.1:5000/v0.4/config", 
        "description": " Configure the Processing Task Software by running the config script. Ref init PTS.\n    "
      }, 
      {
        "URL": "http://127.0.0.1:5000/v0.4/pnsconf", 
        "description": " Configure the PNS itself\n    "
      }
    ]
  }, 
  "timestamp": 1565255652.912552
}
```
----------------------------------------

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
