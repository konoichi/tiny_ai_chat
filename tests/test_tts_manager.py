import unittest
from tts.cache import InMemoryCache
from tts.manager import TTSManager
from tts.base import BaseTTSEngine

# Dummy Engine for testing
class DummyEngine(BaseTTSEngine):
    def list_voices(self):
        return ['voice1', 'voice2']

    def synthesize(self, text: str, voice: str, rate: float) -> bytes:
        return f"{text}-{voice}-{rate}".encode('utf-8')

# Dummy config object
class DummyConfig:
    class CacheCfg:
        enabled = True
        maxsize = 2
        ttl_seconds = None

    enabled = True
    default_engine = 'dummy'
    cache = CacheCfg()
    engines = {
        'dummy': type('E', (), {'type': 'dummy', 'endpoint': None, 'auth': None})()
    }

# Monkey-patch import for dummy engine
import sys
sys.modules['tts.engines.dummy'] = type(sys)('dummy_module')
setattr(sys.modules['tts.engines.dummy'], 'DummyEngine', DummyEngine)

class TestTTSManager(unittest.TestCase):
    def setUp(self):
        self.manager = TTSManager(DummyConfig)

    def test_list_engines(self):
        self.assertListEqual(self.manager.list_engines(), ['dummy'])

    def test_list_voices(self):
        voices = self.manager.list_voices()
        self.assertListEqual(voices, ['voice1', 'voice2'])

    def test_synthesize_and_cache(self):
        text, voice, rate = 'hello', 'voice1', 1.0
        first = self.manager.synthesize(text, voice, rate)
        second = self.manager.synthesize(text, voice, rate)
        self.assertEqual(first, second)
        self.assertEqual(first, b'hello-voice1-1.0')

    def test_disable(self):
        self.manager.disable()
        with self.assertRaises(RuntimeError):
            self.manager.synthesize('hi', 'voice1', 1.0)

if __name__ == '__main__':
    unittest.main()
