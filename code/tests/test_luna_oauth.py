import unittest
import os
import uuid
import tempfile
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock, patch

from llm import luna_oauth as oauth
from llm.luna_oauth import LunaClient, OAuthError, validate_callback


class LunaTests(unittest.TestCase):
    def test_failure_codes_preserved_without_sensitive_messages(self):
        sdk=Mock()
        sdk.responses.create.return_value=iter([N(type='response.failed',
            response=N(error=N(code='subscription_sharing_usage_limit_exceeded',message='secret-token')))])
        with self.assertRaises(OAuthError) as caught:
            LunaClient(lambda:sdk).complete('prompt')
        self.assertEqual(caught.exception.category,'quota_or_rate_limit')
        self.assertEqual(caught.exception.error_code,'subscription_sharing_usage_limit_exceeded')
        self.assertNotIn('secret-token',str(caught.exception))
        self.assertIsNone(oauth.request_failure('Bearer secret-token').error_code)

    def test_supported_host_id(self):
        host = oauth.new_host_id()
        self.assertTrue(host.startswith('urn:uuid:'))
        self.assertEqual(uuid.UUID(host[9:]).version, 4)

    @unittest.skipUnless(os.name == 'nt', 'Windows credential store')
    def test_credential_encrypted_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(oauth,'STATE_PATH',Path(tmp)/'account.bin'):
            record = {'access_token':'secret-access','refresh_token':'secret-refresh'}
            with oauth.account_lock():
                oauth.save_account(record)
                self.assertEqual(oauth.load_account(), record)
            self.assertNotIn(b'secret',oauth.STATE_PATH.read_bytes())

    def test_refresh_rotates_and_persists_before_use(self):
        account = dict(access_token='old',refresh_token='refresh',client_id='issued',expires_at=0)
        replacement = dict(access_token='new',refresh_token='rotated',expires_in=3600)
        with tempfile.TemporaryDirectory() as tmp, patch.object(oauth,'STATE_PATH',Path(tmp)/'a'), \
             patch.object(oauth,'load_account',return_value=account), \
             patch.object(oauth,'exchange',return_value=replacement) as exchange, \
             patch.object(oauth,'save_account') as save, patch.object(oauth,'OpenAI') as sdk:
            oauth.sdk_client()
            exchange.assert_called_once_with(dict(grant_type='refresh_token',client_id='issued',
                refresh_token='refresh',resource=oauth.RESOURCE))
            self.assertEqual(save.call_args.args[0]['refresh_token'],'rotated')
            self.assertEqual(sdk.call_args.kwargs['api_key'],'new')

    def test_prompt_and_model_preserved(self):
        sdk = Mock()
        sdk.responses.create.return_value = iter([
            N(type='response.output_text.delta', delta='{"x":'),
            N(type='response.output_text.delta', delta='1}'),
            N(type='response.completed', response=N(status='completed')),
        ])
        client = LunaClient(lambda: sdk)
        self.assertEqual(client.complete('original prompt'), '{"x":1}')
        sdk.responses.create.assert_called_once_with(
            model='gpt-6-luna', input=[{'role':'user','content':'original prompt'}],
            store=False, stream=True)

    def test_partial_failed_incomplete_never_returned(self):
        for end in [None, 'response.failed', 'response.incomplete', 'error']:
            sdk = Mock()
            events = [N(type='response.output_text.delta', delta='partial')]
            if end:
                events.append(N(type=end))
            sdk.responses.create.return_value = iter(events)
            with self.assertRaises(OAuthError):
                LunaClient(lambda: sdk).complete('prompt')

    def test_callback_state_client_and_denial(self):
        good = {'state':['state'], 'code':['code'], 'client_id':['oaiapp_test']}
        self.assertEqual(validate_callback(good, 'state', None), ('code','oaiapp_test'))
        for values in [dict(good,state=['wrong']), dict(good,error=['access_denied']),
                       dict(good,client_id=['dynamic_agent_client'])]:
            with self.assertRaises(OAuthError):
                validate_callback(values, 'state', None)
        with self.assertRaises(OAuthError):
            validate_callback(good, 'state', 'oaiapp_other')


if __name__ == '__main__':
    unittest.main()
