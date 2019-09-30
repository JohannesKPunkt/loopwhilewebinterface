function handle_run_button()
{
	button = document.getElementById("run_button");
	if(button.firstChild.data == "run")
	{
		var program_code = editor.getValue();
		//TODO
		var data = new FormData();
		data.append("program_code", program_code);
		var request = new XMLHttpRequest();
		request.onreadystatechange = function()
		{
			if (this.readyState == 4 && this.status == 200)
			{
				// server is now running the program
				var id = parseInt(this.responseText, 10);
				if (isNaN(id))
				{
					alert("illegal response from server");
					session_id = 0;
				}
				else
				{
					session_id = id;
				}
			}
			else if (this.readyState == 4)
			{
				alert("connection error " + this.status);
				alert(this.responseText); //TODO only for debug
			}
		};
		request.timeout = 2000;
		request.open("POST", "run", true);
		request.send(data);
		button.firstChild.data = "stop";
		window.reload_terminal_agent = setTimeout(reload_terminal, 500);
		window.await_termination_agent = setInterval(check_termination, 500);
		
	}
	else
	{
		//TODO
		
		var data = new FormData();
		data.append("session_id", session_id);
		var requesta = new XMLHttpRequest();
		requesta.onreadystatechange = function()
		{
			if (this.readyState == 4 && this.status == 200)
			{
				if (this.responseText != "OK")
				{
					alert(this.responseText)
				}
			}
			else if (this.readyState == 4)
			{
				alert("connection error " + this.status);
			}
		};
		requesta.timeout = 2000;
		requesta.open("POST", "stop", true);
		requesta.send(data);
		
		session_id = 0;
		clearTimeout(window.reload_terminal_agent);
		button.firstChild.data = "run";
	}
}

function check_termination()
{
	var data = new FormData();
	data.append("session_id", session_id);
	var requesta = new XMLHttpRequest();
	requesta.onreadystatechange = function()
	{
		if (this.readyState == 4 && this.status == 200)
		{
			if (this.responseText != "running")
			{
				clearInterval(window.await_termination_agent);
				session_id = 0;
				clearTimeout(window.reload_terminal_agent);
				button.firstChild.data = "run";
				if (this.responseText == "timeout")
				{
					alert("Timeout");
				}
			}
		}
		
	};
	requesta.timeout = 2000;
	requesta.open("POST", "check_termination", true);
	requesta.send(data);
}

function handle_debug_mode_button()
{
	button = document.getElementById("debug_mode_button");
	if(button.firstChild.data == "enter debug mode")
	{
		//TODO
		button.firstChild.data = "leave debug mode";
        //window.open("debugger", "_self");
        var form = document.createElement("form");
        form.target = "_self";
        form.method = "POST";
        form.action = "debugger";
        var input = document.createElement("input");
        input.type = "hidden";//test text
        input.name = "program_code";
        input.value = editor.getValue();
        
        form.appendChild(input);
        document.body.appendChild(form);
        form.submit();
	}
	else
	{
		//TODO
		button.firstChild.data = "enter debug mode";
	}
}

function breakpoint_action(id)
{
    var elem = document.getElementById(id);
    if (elem.getAttribute("src") == "/img/transparentdot.png")
    {
        var data = new FormData();
        data.append("session_id", session_id);
        data.append("line_no", id.slice(3));
        var requesta = new XMLHttpRequest();
        requesta.onreadystatechange = function()
        {
            if (this.readyState == 4 && this.status == 200)
            {
                if (this.responseText == "OK")
                {
                    elem.setAttribute("src", "/img/reddot.png");
                }
            }
            
        };
        requesta.timeout = 2000;
        requesta.open("POST", "set_breakpoint", true);
        requesta.send(data);
     }
     else
     {
        var data = new FormData();
        data.append("session_id", session_id);
        data.append("line_no", id.slice(3));
        var requesta = new XMLHttpRequest();
        requesta.timeout = 2000;
        requesta.open("POST", "remove_breakpoint", true);
        requesta.send(data);
        elem.setAttribute("src", "/img/transparentdot.png");
     }
}


function handle_continue_button()
{
    handle_action("continue");
}

function handle_step_over_button()
{
    handle_action("stepover");
}

function handle_step_into_button()
{
    handle_action("stepinto");
}

function handle_step_out_button()
{
    handle_action("stepout");
}

function handle_action(action)
{
    var data = new FormData();
	data.append("session_id", session_id);
	data.append("action", action);
	var request = new XMLHttpRequest();
	request.onreadystatechange = function()
	{
		if (this.readyState == 4 && this.status == 200)
		{
			if(this.responseText == "FAIL" || this.responseText == "DIED")
            {
                if(active_line != "")
                {
                    var elem = document.getElementById(active_line);
                    elem.setAttribute("class", "debuggerCodeViewLine");
                    active_line = ""
                }
            }
            else
            {
                if(active_line != "")
                {
                    var elem = document.getElementById(active_line);
                    elem.setAttribute("class", "debuggerCodeViewLine");
                }
                var elem = document.getElementById(this.responseText);
                elem.setAttribute("class", "debuggerCodeViewLineActive");
                active_line = this.responseText
            }
		}
		
	};
	request.timeout = 2000;
	request.open("POST", "debugger_action", true);
	request.send(data);
}