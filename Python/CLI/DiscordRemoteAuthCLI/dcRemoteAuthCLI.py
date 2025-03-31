#!/usr/bin/env python3
"""
This is a simple script wrapper for the "remote-auth" discord protocol.
It lets you generate a new discord session on command.
It was made quickly and is very crude and not very clean.

Docs on the protocol: https://github.com/discord-userdoccers/discord-userdoccers/blob/master/pages/remote-authentication/mobile.mdx

Author: https://github.com/bytequill
Made as part of https://github.com/bytequill/smallscripts series
"""
try:
    import os, sys, json
    import dotenv, requests
    from rich.console import Console
except ImportError as e:
    print("✘ Could not find package "+e.name+". Please install it from the "+sys.argv[0]+".requirements or if unavailable. use the requirements provided below:\n"+"""requests==2.32.3
rich==14.0.0
python-dotenv==1.1.0""")
    exit(1)

API_URL="https://discord.com/api/v9"
DC_TOKEN: str

P_ERR = "[red]✘[/red] "
P_CHK = "[green]✓[/green] "
P_INF = "[blue]I[/blue] "
P_INP = "[yellow]/[/yellow] "

def prompt_bool(con: Console, msg: str, default: bool) -> bool:
    yn: str
    if default:
        yn = "- Y/n "
    else:
        yn = "- y/N "

    res = con.input(msg+yn)
    if res == "":
        return default
    elif res.lower() == "y":
        return True
    elif res.lower() == "n":
        return False
    else:
        con.print(P_ERR+"Invalid value. Please use '' or y or n")
        return prompt_bool(con, msg, default)

def contentfulInput(con: Console, msg: str) -> str:
    i = con.input(msg + ": ")
    if i and len(i) > 0:
        return i
    else:
        con.print(P_ERR+"Please enter a value. It cannot be blank")
        return contentfulInput(con, msg)

def do_dcAPIreq(s: requests.Session, endpoint: str, method: str, body: dict) -> tuple[int, dict]:
    r = requests.Request(method, API_URL+endpoint)
    if body: r.data = json.dumps(body)
    r = r.prepare()

    r.headers["authorization"] = DC_TOKEN
    if body: r.headers["Content-Type"] = "application/json"
    res = s.send(r)
    
    if res.status_code != 204:
        try:
            return (res.status_code, res.json())
        except Exception as e:
            return (500, {"err": e})
    else:
        return (res.status_code, None)

def main():
    global DC_TOKEN

    con = Console()
    s = requests.Session()
    dotenv.load_dotenv()
    DC_TOKEN = os.getenv("DC_TOKEN")
    if DC_TOKEN and  len(DC_TOKEN) > 0:
        con.print(P_CHK+"Got token from env")
    else:
        con.print(P_ERR+"Could not get token from env. Create a .env with the variable DC_TOKEN")
        DC_TOKEN = con.input(P_INP+"[yellow]Fallback[/yellow] Please enter the token manually. It is reccomended to verify it: ")
        if not DC_TOKEN and len(DC_TOKEN) == 0:
            exit(1)
        con.print(P_INF+"Token is "+DC_TOKEN)
    
    res = prompt_bool(con,P_INP+"Do you want to verify token?", False)
    if res:
        rcode, rdata = do_dcAPIreq(s, "/users/@me", "GET", None)
        if rcode != 200:
            con.print(P_ERR+"Could not verify token. Status="+str(rcode))
            exit(1)
        else:
            con.print(P_CHK+"Token verified as working. Username="+rdata["username"]+" id="+rdata["id"])

    fingerprint = contentfulInput(con,P_INP+"Please enter remote auth fingerprint")
    
    con.print(P_INF+"Fingerprint is "+fingerprint)

    rcode, rdata = do_dcAPIreq(s, "/users/@me/remote-auth", "POST", {"fingerprint": fingerprint})
    handshake: str
    if rcode != 200:
       con.print(P_ERR+"Invalid respose from discord. Status="+str(rcode)+" rdata="+str(rdata))
       exit(1)

    if rdata["handshake_token"] and len(rdata["handshake_token"]) > 0:
        handshake = rdata["handshake_token"]
    else:
        con.print(P_ERR+"Invalid handshake_token respose from discord. rdata="+str(rdata))
        exit(1)

    if prompt_bool(con, P_INP+"Are you sure you want to [green]accept[/green] the creation of a new session", True):
        rcode, rdata = do_dcAPIreq(s, "/users/@me/remote-auth/finish", "POST", {"handshake_token": handshake, "temporary_token": False})
        if rcode != 204:
            con.print(P_ERR+"Could not create a new session. status="+str(rcode)+" rdata="+str(rdata))
            exit(1)
    else:
        rcode, rdata = do_dcAPIreq(s, "/users/@me/remote-auth/cancel", "POST", {"handshake_token": handshake})
        if rcode != 204:
            con.print(P_ERR+"Could not cancel succesfully. status="+str(rcode)+" rdata="+str(rdata))
            exit(1)
    con.print(P_CHK+"done")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception:
        Console().print_exception()
