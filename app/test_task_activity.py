import unittest
from chat_backend import CodexSession
from task_activity import tool_activity


class ToolActivityTests(unittest.TestCase):
    def test_failed_command_has_status_without_guessing_error_from_output(self):
        value = tool_activity({'type': 'commandExecution', 'status': 'completed',
                               'exitCode': 1, 'command': 'rg files',
                               'aggregatedOutput': "self.assertIn('denied', result)"})
        self.assertEqual(value, '命令执行失败（返回码 1）\nrg files')
        self.assertNotIn('denied', value)

    def test_command_actions_and_long_details(self):
        value = tool_activity({'type': 'commandExecution', 'status': 'inProgress',
                               'command': 'raw wrapper',
                               'commandActions': [{'type': 'search', 'query': 'swap', 'path': 'app'}]})
        self.assertEqual(value, '正在运行命令\n搜索 swap app')
        value = tool_activity({'type': 'commandExecution', 'command': 'long ' * 1000})
        self.assertLess(len(value), 350)
        self.assertTrue(value.endswith('…'))

    def test_mcp_dynamic_and_web_status(self):
        for kind in ('mcpToolCall', 'dynamicToolCall'):
            value = tool_activity({'type': kind, 'status': 'completed', 'namespace': 'functions',
                                   'tool': 'exec', 'arguments': 'PRIVATE', 'result': 'PRIVATE'})
            self.assertEqual(value, '工具调用结束\nfunctions.exec')
        self.assertEqual(tool_activity({'type': 'webSearch', 'status': 'inProgress', 'query': 'Qt'}),
                         '正在搜索网页\nQt')
        self.assertEqual(tool_activity({'type': 'reasoning', 'content': 'PRIVATE'}), '')

    def test_cli_routes_tools_as_transient_events_without_finishing_turn(self):
        events = []
        session = CodexSession('.', emit=lambda kind, value: events.append((kind, value)))
        session.finished_turn = None
        for method in ('item/started', 'item/completed'):
            session.event({'method': method, 'params': {'item': {
                'type': 'mcpToolCall', 'server': 'example', 'tool': 'read',
                'arguments': 'PRIVATE', 'aggregatedOutput': 'PRIVATE'}}})
        self.assertEqual(events, [('activity', '正在调用工具\nexample.read'),
                                  ('activity', '工具调用结束\nexample.read')])
        self.assertIsNone(session.finished_turn)
        self.assertEqual(session.transcript(), '')


if __name__ == '__main__':
    unittest.main()
