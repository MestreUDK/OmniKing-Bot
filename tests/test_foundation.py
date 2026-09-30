import base64
import json
import logging
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from telegram import Update
from telegram.ext import TypeHandler
from telegram.request import BaseRequest
from bot import create_application
from config import APP_NAME
from kingcore.settings import Settings, ConfigError
from kingcore.cache import TTLCache
from kingcore.database import DatabaseProbe
from kingcore.logging_setup import SafeFormatter
from kingcore.commands import status
from kingcore.runtime import on_error

TOKEN = "123456789:" + "x" * 35
ENV = {"BOT_TOKEN": TOKEN, "ADMIN_IDS": "123"}

def settings(**kwargs):
    return Settings.from_env(APP_NAME, {**ENV, **kwargs})

class SettingsTests(unittest.TestCase):
    def test_no_secret_in_repr(self):
        value = settings(SUPABASE_URL="https://example.supabase.co", SUPABASE_KEY="private-value")
        self.assertNotIn(TOKEN, repr(value))
        self.assertNotIn("private-value", repr(value))

    def test_allowlist_and_legacy_id(self):
        self.assertEqual(settings(ADMIN_IDS="123, 456,123", ADMIN_ID="789").admin_ids, {123,456,789})

    def test_invalid_config(self):
        for env in [dict(ADMIN_IDS=""), dict(ADMIN_IDS="0"), dict(ADMIN_IDS="abc"),
                    dict(ADMIN_IDS="-10"), dict(ADMIN_IDS="１２３"), dict(BOT_TOKEN=""),
                    dict(SUPABASE_URL="https://example.supabase.co"), dict(SUPABASE_KEY="key"),
                    dict(FORCE_IPV4="maybe"), dict(LOG_LEVEL="all"),
                    dict(SUPABASE_URL="http://example.org", SUPABASE_KEY="key"),
                    dict(SUPABASE_URL="https://a:b@example.org", SUPABASE_KEY="key"),
                    dict(SUPABASE_URL="https://example.org/path", SUPABASE_KEY="key"),
                    dict(SUPABASE_URL="https://[broken", SUPABASE_KEY="key")]:
            with self.subTest(env_keys=list(env)):
                with self.assertRaises(ConfigError): settings(**env)

    def test_role_detection(self):
        jwt = "eyJtest." + base64.urlsafe_b64encode(b'{"role":"service_role"}').decode().rstrip("=") + ".signature"
        for key in [jwt, "sb_secret_fake"]:
            env = {**ENV, "SUPABASE_URL":"https://example.org", "SUPABASE_KEY":key}
            with self.assertRaises(ConfigError): Settings.from_env("OmniKing", env)
            self.assertEqual(Settings.from_env("AdminKing", env).supabase_key, key)

    def test_key_decode_is_not_role_authorization(self):
        # Unknown/opaque keys pass syntax validation, not security attestation.
        self.assertEqual(settings(SUPABASE_URL="https://example.org", SUPABASE_KEY="opaque").supabase_key, "opaque")

    def test_log_redaction(self):
        formatter = SafeFormatter((TOKEN, "secret-value"))
        record = logging.LogRecord("test", logging.ERROR, "", 1, "token=%s key=secret-value", (TOKEN,), None)
        text = formatter.format(record)
        self.assertNotIn(TOKEN, text)
        self.assertNotIn("secret-value", text)

class CacheTests(unittest.TestCase):
    def test_expiry_and_invalidation(self):
        now = [0]
        cache = TTLCache(ttl=10, clock=lambda:now[0])
        cache.put("a", 1)
        now[0]=9
        self.assertEqual(cache.get("a"),1)
        now[0]=10
        self.assertIsNone(cache.get("a"))
        cache.put("b", 2)
        cache.invalidate("b")
        self.assertIsNone(cache.get("b"))
        cache.put("c", 3)
        cache.invalidate()
        self.assertIsNone(cache.get("c"))

    def test_bound_and_copy(self):
        cache = TTLCache(maxsize=2)
        value = {"x":[1]}
        cache.put("a", value)
        value["x"].append(2)
        read = cache.get("a")
        read["x"].append(3)
        self.assertEqual(cache.get("a"), {"x":[1]})
        cache.put("b", 2)
        cache.put("c", 3)
        self.assertIsNone(cache.get("a"))
        self.assertEqual(cache.get("c"),3)

class ProbeTests(unittest.IsolatedAsyncioTestCase):
    async def test_unconfigured_without_client(self):
        def forbidden(*args): raise AssertionError("Should not construct client")
        self.assertEqual((await DatabaseProbe(settings(),forbidden).check()).state,"unconfigured")

    async def test_select_only(self):
        calls=[]
        class Query:
            def table(self,value):calls.append(("table",value));return self
            def select(self,value):calls.append(("select",value));return self
            def limit(self,value):calls.append(("limit",value));return self
            def execute(self):calls.append(("execute",));return SimpleNamespace(data=[])
        probe=DatabaseProbe(settings(SUPABASE_URL="https://example.org",SUPABASE_KEY="key"),lambda *_:Query())
        self.assertEqual((await probe.check()).state,"reachable")
        self.assertEqual(calls,[("table","animes"),("select","id"),("limit",0),("execute",)])

    async def test_real_sdk_uses_read_request_only(self):
        import httpx
        requests=[]
        def respond(client, request, **kwargs):
            requests.append(request)
            return httpx.Response(200, json=[], request=request)
        probe=DatabaseProbe(settings(SUPABASE_URL="https://example.supabase.co",SUPABASE_KEY="sb_publishable_fake"))
        with patch.object(httpx.Client,"send",respond):
            result=await probe.check()
        self.assertEqual(result.state,"reachable")
        self.assertEqual(len(requests),1)
        self.assertEqual(requests[0].method,"GET")
        self.assertEqual(requests[0].url.path,"/rest/v1/animes")
        self.assertEqual(requests[0].url.params["limit"],"0")

    async def test_failure_redacts_exception(self):
        def broken(*_): raise RuntimeError("secret private URL")
        probe=DatabaseProbe(settings(SUPABASE_URL="https://example.org",SUPABASE_KEY="key"),broken)
        result=await probe.check()
        self.assertEqual(result.state,"unavailable")
        self.assertNotIn("secret",result.message)

class FakeRequest(BaseRequest):
    def __init__(self):self.calls=[]
    @property
    def read_timeout(self):return 10
    async def initialize(self):pass
    async def shutdown(self):pass
    async def do_request(self,url,method,request_data=None,**kwargs):
        name=url.rsplit("/",1)[-1]
        params=request_data.parameters if request_data else {}
        self.calls.append((name,params))
        if name=="getMe":
            data={"id":123456789,"is_bot":True,"first_name":"Test","username":"KingTestBot"}
        elif name=="sendMessage":
            chat_id=int(params["chat_id"])
            data={"message_id":99,"date":0,"chat":{"id":chat_id,"type":"private"},"text":params["text"]}
        elif name=="answerCallbackQuery":data=True
        else: raise AssertionError(f"Unexpected API method: {name}")
        return 200,json.dumps({"ok":True,"result":data}).encode()

def make_update(bot,uid=123,text="/start",kind="message",chat_type="private",chat_id=None,is_bot=False):
    user={"id":uid,"is_bot":is_bot,"first_name":"Test"}
    chat={"id":uid if chat_id is None else chat_id,"type":chat_type}
    message={"message_id":1,"date":0,"chat":chat,"from":user,"text":text,
             "entities":[{"type":"bot_command","offset":0,"length":len(text.split()[0])}]}
    data={"update_id":1}
    if kind=="callback_query":
        data[kind]={"id":"callback","from":user,"chat_instance":"test","message":message,"data":"ak:foundation:status"}
    elif kind=="inline_callback":
        data["callback_query"]={"id":"callback","from":user,"chat_instance":"test","inline_message_id":"1","data":"ak:foundation:status"}
    elif kind=="inline_query":data[kind]={"id":"inline","from":user,"query":"test","offset":""}
    else:data[kind]=message
    return Update.de_json(data,bot)

class ApplicationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.request=FakeRequest()
        self.app=create_application(settings(),request=self.request,updates_request=FakeRequest())
        self.errors=[]
        async def capture(update,context):self.errors.append(context.error)
        self.app.add_error_handler(capture)
        await self.app.initialize()
        self.request.calls.clear()

    async def asyncTearDown(self):
        await self.app.shutdown()
        self.assertEqual(self.errors,[])

    async def test_start_and_health(self):
        for command in ["/start","/health"]:
            await self.app.process_update(make_update(self.app.bot,text=command))
        self.assertEqual(len([c for c in self.request.calls if c[0]=="sendMessage"]),2)

    async def test_status_does_not_write_or_leak(self):
        await self.app.process_update(make_update(self.app.bot,text="/status"))
        text=self.request.calls[-1][1]["text"]
        self.assertIn("não configurado",text)
        self.assertNotIn(TOKEN,text)

    async def test_unauthorized_status_never_queries_database(self):
        db=SimpleNamespace(check=AsyncMock(side_effect=AssertionError("Unauthorized DB access")))
        self.app.bot_data["db"]=db
        await self.app.process_update(make_update(self.app.bot,uid=999,text="/status"))
        db.check.assert_not_awaited()

    async def test_arbitrary_update_guard(self):
        if APP_NAME!="AdminKing":self.skipTest("AdminKing-specific gate")
        reached=[]
        async def domain(update,context):reached.append(update.update_id)
        self.app.add_handler(TypeHandler(Update,domain),group=1)
        cases=[dict(uid=999),dict(uid=999,kind="edited_message"),dict(uid=999,kind="callback_query"),
               dict(uid=123,chat_type="group",chat_id=-100),dict(uid=123,kind="inline_query"),
               dict(uid=123,kind="inline_callback"),dict(uid=123,kind="channel_post",chat_type="channel",chat_id=-100),
               dict(uid=123,is_bot=True),dict(uid=123,chat_id=456)]
        for case in cases:
            with self.subTest(case=case):
                await self.app.process_update(make_update(self.app.bot,**case))
                self.assertEqual(reached,[])
                self.assertEqual(self.request.calls,[])
        await self.app.process_update(make_update(self.app.bot))
        self.assertEqual(reached,[1])

    async def test_admin_callback(self):
        if APP_NAME!="AdminKing":self.skipTest("AdminKing-specific menu")
        await self.app.process_update(make_update(self.app.bot,kind="callback_query"))
        self.assertEqual([c[0] for c in self.request.calls],["answerCallbackQuery","sendMessage"])

    async def test_public_has_no_admin_commands(self):
        if APP_NAME!="OmniKing":self.skipTest("OmniKing-specific routes")
        for command in ["/admin","/cadastro","/edit","/broadcast"]:
            await self.app.process_update(make_update(self.app.bot,text=command))
        self.assertEqual(self.request.calls,[])

    async def test_link_is_not_falsely_reported_as_delivered(self):
        if APP_NAME!="OmniKing":self.skipTest("OmniKing-specific links")
        await self.app.process_update(make_update(self.app.bot,text="/start get_123"))
        self.assertIn("fundação de testes",self.request.calls[-1][1]["text"])

    async def test_error_reference_hides_raw_exception(self):
        reply=AsyncMock()
        context=SimpleNamespace(error=ValueError("token="+TOKEN))
        await on_error(SimpleNamespace(effective_message=SimpleNamespace(reply_text=reply)),context)
        text=reply.await_args.args[0]
        self.assertIn("Referência:",text)
        self.assertNotIn(TOKEN,text)

if __name__=="__main__":unittest.main()
