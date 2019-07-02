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

APIs	
DELETE	
Removing traces of past runnings the Processing Task Software. 	"http://127.0.0.1:5000/v0.4/clean"
GET	
returns names and contents of all files in the dir, 'None' if dir not existing. 	"http://127.0.0.1:5000/v0.4/output"
configPTS file	"http://127.0.0.1:5000/v0.4/config"
initPTS file	"http://127.0.0.1:5000/v0.4/init"
POST	
Generates a product by running script defined in the config as prog ('hello' for testing). Execution on the server host is in the pnshome directory and run result and status are returned. 	"http://127.0.0.1:5000/v0.4/run"
generate post test product. put the 1st input (see maketestdata in test_all.py) parameter to metadata and 2nd to the product's dataset 	"http://127.0.0.1:5000/v0.4/data"
Echo	"http://127.0.0.1:5000/v0.4/echo"
PUT	
Configure the Processing Task Software by running the config script. Ref init PTS. 	"http://127.0.0.1:5000/v0.4/config"
Initialize the Processing Task Software by running the init script defined in the config. Execution on the server host is in the pnshome directory and run result and status are returned. 	"http://127.0.0.1:5000/v0.4/init"

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
