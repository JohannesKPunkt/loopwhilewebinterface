#  Main.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#
#

from wsgiref.simple_server import make_server
from tg import TGController, expose 
from tg import MinimalApplicationConfigurator
from tg.configurator.components.statics import StaticsConfigurationComponent

from SessionManager import create_session, check_session
from ProcessManager import get_process, create_process, kill_process, get_process_status, remove_process_data
from IOTools import read_timeout
import DebuggerView
from InterpreterView import InterpreterView

_port = 8080

class RootController(TGController):
	
	# this function is implementing the /run side, that receives the program the user wants to execute
	# and returns a unique session id
    @expose(content_type="text/plain")
    def run(self, **kw):
        try:
            program_code = kw["program_code"]
            #debug_mode = kw[" TODO: TO BE IMPLEMENTED LATER
            sess_id = create_session()
            create_process(sess_id, program_code, False)
            return str(sess_id);
        except Exception as e:
            print("run(): The following exception occurred: " + str(e))
            return "0"
    
    # /stop is used to kill the interpreter process by user clicking the stop button
    @expose(content_type="text/plain")
    def stop(self, **kw):
        try:
            session_id = kw["session_id"]
            if not check_session(session_id):
                return "An error occurred: invalid session (id=" + str(session_id) + ")."
            kill_process(session_id)
            remove_process_data(session_id)
            return "OK"
        except Exception as e:
            print("stop(): Unexcepted exception in stop(): " + str(e))
            return "An unexpected server-sided exception occurred."
    
    # /shell receives a command line the user entered in the shell and returns a response string
    @expose(content_type="text/plain")
    def shell(self, **kw):
        try:
            shell_input = kw["input"]
            session_id = kw["session_id"]
            
            if not check_session(session_id):
                return "An error occurred: invalid session (id=" + str(session_id) + ")."
            
            proc = get_process(session_id)
            try:
                if shell_input != "":
                    to_write = (shell_input + "\n").encode()
                    print(to_write)
                    proc.stdin.write(to_write)
                    proc.stdin.flush()
                else:
                    print("DBG: empty write")
                output = read_timeout(proc.stdout, timeout=0.15)
                print("[DBG] shell - output = " + output)
                return output
            except Exception as e:
                print("[DBG] shell - Exception when write/read to child process: " + str(e))
                raise(e)
                return ""
        except KeyError as e:
            print("shell - " + str(e))
            return "An error occurred."
    
    # returns either "running", "terminated", "timeout" or "error"
    @expose(content_type="text/plain")
    def check_termination(self, **kw):
        try:
            session_id = kw["session_id"]
            if not check_session(session_id):
                return "error"
            return get_process_status(session_id)
        except Exception:
            return "error"


    # /debugger is the main side of the debugger mode
    @expose()#(content_type="text/html")
    def debugger(self, **kw):
        return DebuggerView.getSourceCodeView("""// Hier könnte Ihr Programm stehen
in: i0
out: o0

o0 := 42 * i0;
+ - * div   == 

34324324324324324324
wevfewcfe

while foobar do
    blabla;--
\teingerueckt mit tabs ;)
enddo""")

    # /interpreter is the main site of the interpreter mode
    @expose('templates/interpreter.xhtml', content_type="text/html")
    def interpreter(self):
	    #return dict(title="Hallo Welt 123!",text_before="<h1>LoopWhile interactive interpreter</h1>")
        return InterpreterView()


config = MinimalApplicationConfigurator()
config.register(StaticsConfigurationComponent)
config.update_blueprint({
    'root_controller': RootController(),
    'renderers': ['genshi'],
    'default_renderer': 'genshi',
    'paths': {
        'static_files': 'web'
    }
})

print("Listening on port " + str(_port) + ".")
httpd = make_server('', _port, config.make_wsgi_app())
httpd.serve_forever()
