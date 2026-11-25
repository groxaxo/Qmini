import unittest,threading,json,urllib.request,urllib.error,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"gateway"))
from server import create_server
class GatewayTest(unittest.TestCase):
    def setUp(self):
        self.token="a"*32
        self.s=create_server("127.0.0.1",0,self.token)
        self.t=threading.Thread(target=self.s.serve_forever,daemon=True)
        self.t.start()
        self.url="http://127.0.0.1:"+str(self.s.server_port)
    def tearDown(self):
        self.s.shutdown();self.s.server_close();self.t.join()
    def req(self,path="/v1/status",token=None,method="GET"):
        r=urllib.request.Request(self.url+path,method=method)
        if token:r.add_header("Authorization","Bearer "+token)
        try:
            with urllib.request.urlopen(r,timeout=2) as f:return f.status,json.load(f)
        except urllib.error.HTTPError as e:
            with e:return e.code,json.load(e)
    def test_read_only(self):
        code,body=self.req(token=self.token)
        self.assertEqual(code,200)
        self.assertFalse(body["motors_enabled"])
        self.assertFalse(body["hardware_connected"])
    def test_auth(self):
        self.assertEqual(self.req()[0],401)
        self.assertEqual(self.req(token="wrong")[0],401)
    def test_no_actuation(self):
        self.assertEqual(self.req("/v1/move",self.token,"POST")[0],405)
        self.assertEqual(self.req("/v1/move",self.token)[0],404)
    def test_weak_token(self):
        with self.assertRaises(ValueError):create_server("127.0.0.1",0,"short")
if __name__=="__main__":unittest.main()
