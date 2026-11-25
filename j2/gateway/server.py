"""Read-only simulation gateway: no actuator interfaces or movement commands."""
import argparse, hmac, json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def reply(self,code,payload):
        data=json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        if self.path!="/v1/status":
            return self.reply(404,{"error":"not found"})
        auth=self.headers.get("Authorization","")
        if not hmac.compare_digest(auth.encode(),("Bearer "+self.server.token).encode()):
            return self.reply(401,{"error":"unauthorized"})
        return self.reply(200,{"mode":"simulation","motors_enabled":False,"robot":"Qmini-J2","hardware_connected":False})
    def do_POST(self):
        return self.reply(405,{"error":"read only; no actuation"})

def create_server(host,port,token):
    if not token or len(token)<24: raise ValueError("Use a token of at least 24 characters")
    s=ThreadingHTTPServer((host,port),Handler)
    s.token=token
    return s

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--host",default="127.0.0.1")
    p.add_argument("--port",type=int,default=8769)
    args=p.parse_args()
    with create_server(args.host,args.port,os.environ.get("QMINI_TOKEN","")) as server:
        server.serve_forever()

if __name__=="__main__": main()
