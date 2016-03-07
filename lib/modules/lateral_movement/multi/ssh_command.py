from lib.common import helpers

class Module:
    def __init__(self, mainMenu, params=[]):
        # metadata info about the module, not modified during runtime
        self.info = {
            # name for the module that will appear in module menus
            'Name': 'SSHCommand',

            # list of one or more authors for the module
            'Author': ['Paul Mikesell', '@424f424f'],

            # more verbose multi-line description of the module
            'Description': 'This module will send an ssh command and display the output.',

            # True if the module needs to run in the background
            'Background' : False,

            # File extension to save the file as
            'OutputExtension' : "",

            # if the module needs administrative privileges
            'NeedsAdmin' : False,

            # True if the method doesn't touch disk/is reasonably opsec safe
            'OpsecSafe' : True,

            # list of any references/other comments
            'Comments': [
                'http://blog.clustrix.com/2012/01/31/scripting-ssh-with-python/'
                            ]
        }

        # any options needed by the module, settable during runtime
        self.options = {
            # format:
            #   value_name : {description, required, default_value}
            'Agent' : {
                # The 'Agent' option is the only one that MUST be in a module
                'Description'   :   'Agent to use ssh from.',
                'Required'      :   True,
                'Value'         :   ''
            },
            'Login' : {
                'Description'   :   'user@127.0.0.1',
                'Required'      :   True,
                'Value'         :   ''
            },
            'Password' : {
                'Description'   :   'Password',
                'Required'      :   True,
                'Value'         :   ''
            },
            'Command' : {
                'Description'   :   'Command to execute',
                'Required'      :   True,
                'Value'         :   'id'
            }
        }

        # save off a copy of the mainMenu object to access external functionality
        #   like listeners/agent handlers/etc.
        self.mainMenu = mainMenu

        # During instantiation, any settable option parameters
        #   are passed as an object set to the module and the
        #   options dictionary is automatically set. This is mostly
        #   in case options are passed on the command line
        if params:
            for param in params:
                # parameter format is [Name, Value]
                option, value = param
                if option in self.options:
                    self.options[option]['Value'] = value

    def generate(self):
        login = self.options['Login']['Value']
        parts = login.split('@')
        if len(parts) != 2:
            print "please enter login in 'user@host' format"
            return ""
        user = parts[0]
        host = parts[1]

        password = self.options['Password']['Value']
        command = self.options['Command']['Value']
        
        script = """

def run_cmd(ip, passwd, cmd, user, port=22):
    import pty, re, os, sys, stat

    class SSHError(Exception):
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return repr(self.value)

    class SSH: 
        def __init__(self, ip, passwd, user, port):
            self.ip = ip
            self.passwd = passwd
            self.user = user
            self.port = port

        def run_cmd(self, c):
            (pid, f) = pty.fork()
            if pid == 0:
                os.execlp("ssh", "ssh", '-p %%d' %% self.port,
                          self.user + '@' + self.ip, c)
            else:
                return (pid, f)

        def push_file(self, src, dst):
            (pid, f) = pty.fork()
            if pid == 0:
                os.execlp("scp", "scp", '-P %%d' %% self.port,
                          src, self.user + '@' + self.ip + ':' + dst)
            else:
                return (pid, f) 

        def push_dir(self, src, dst):
            (pid, f) = pty.fork()
            if pid == 0:
                os.execlp("scp", "scp", '-P %%d' %% self.port, "-r", src,
                          self.user + '@' + self.ip + ':' + dst)
            else:
                return (pid, f)

        def _read(self, f):
            x = ""
            try:
                x = os.read(f, 1024)
            except Exception, e:
                # this always fails with io error
                pass
            return x

        def ssh_results(self, pid, f):
            output = ""
            got = self._read(f)         # check for authenticity of host request
            m = re.search("authenticity of host", got)
            if m:
                os.write(f, 'yesn') 
                # Read until we get ack
                while True:
                    got = self._read(f)
                    m = re.search("Permanently added", got)
                    if m:
                        break

                got = self._read(f)         # check for passwd request
            m = re.search("assword:", got)
            if m:
                # send passwd
                os.write(f, self.passwd + '\\n')
                # read two lines
                tmp = self._read(f)
                tmp += self._read(f)
                m = re.search("Permission denied", tmp)
                if m:
                    raise Exception("Invalid passwd")
                # passwd was accepted
                got = tmp
            while got and len(got) > 0:
                output += got
                got = self._read(f)
            os.waitpid(pid, 0)
            os.close(f)
            return output

        def cmd(self, c):
            (pid, f) = self.run_cmd(c)
            return self.ssh_results(pid, f)

        def push(self, src, dst):
            s = os.stat(src)
            if stat.S_ISDIR(s[stat.ST_MODE]):
                (pid, f) = self.push_dir(src, dst)
            else:
                (pid, f) = self.push_file(src, dst)
            return self.ssh_results(pid, f)

    def ssh_cmd(ip, passwd, cmd, user, port=22):
        s = SSH(ip, passwd, user, port)
        return s.cmd(cmd)

    def ssh_push(ip, passwd, src, dst, user, port=22): 
        s = SSH(ip, passwd, user, port)
        return s.push(src, dst)

    print ssh_cmd(ip, passwd, cmd, user, port=22)

run_cmd('%s', '%s', '%s', user='%s')

""" %(host, password, command, user)

        return script
