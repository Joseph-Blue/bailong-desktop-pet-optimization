"""Transient public tool status, shared by CLI and desktop observation."""

LABELS = {
    'commandExecution': ('正在运行命令', '命令执行结束'),
    'fileChange': ('正在修改文件', '文件修改结束'),
    'mcpToolCall': ('正在调用工具', '工具调用结束'),
    'dynamicToolCall': ('正在调用工具', '工具调用结束'),
    'webSearch': ('正在搜索网页', '网页搜索结束'),
    'imageGeneration': ('正在生成图片', '图片生成结束'),
    'imageView': ('正在查看图片', '图片查看结束'),
    'contextCompaction': ('正在压缩上下文', '上下文压缩结束'),
}
RUNNING = {'inProgress', 'running'}
ENDED = {'completed', 'failed', 'interrupted', 'cancelled', 'canceled', 'declined'}


def abbreviated(text, limit=320, lines=4):
    text = str(text or '').strip()
    short = '\n'.join(text.splitlines()[:lines])
    if len(short) > limit or short != text:
        return short[:limit - 1].rstrip() + '…'
    return short


def tool_activity(item):
    kind = item.get('type')
    if kind not in LABELS:
        return ''
    status = item.get('status')
    code = item.get('exitCode')
    failed = status == 'failed' or bool(item.get('error')) or code not in (None, 0)
    ended = failed or status in ENDED or item.get('completed') or item.get('completedAtMs') is not None
    title = LABELS[kind][bool(ended)]
    if failed:
        title = ('命令执行失败' if kind == 'commandExecution' else '本次调用失败')
        if code is not None:
            title += f'（返回码 {code}）'
    elif status in {'interrupted', 'cancelled', 'canceled', 'declined'}:
        title = '调用已拒绝' if status == 'declined' else '调用已中断'
    detail = ''
    if kind == 'commandExecution':
        actions = []
        for action in item.get('commandActions') or []:
            path = action.get('path') or action.get('name') or ''
            action_type = action.get('type')
            if action_type == 'read':
                actions.append('读取 ' + path)
            elif action_type == 'listFiles':
                actions.append('列出文件 ' + path)
            elif action_type == 'search':
                actions.append('搜索 ' + (action.get('query') or '') + ' ' + path)
        detail = '\n'.join(actions) or item.get('command') or ''
    elif kind == 'fileChange':
        detail = '\n'.join(change.get('path', '') for change in item.get('changes') or [])
    else:
        detail = '.'.join(str(part) for part in (item.get('namespace') or item.get('server'), item.get('tool')) if part)
        detail = detail or item.get('query') or ''
    # Output, tool arguments and private reasoning are deliberately not projected.
    return title + ('\n' + abbreviated(detail) if detail else '')
