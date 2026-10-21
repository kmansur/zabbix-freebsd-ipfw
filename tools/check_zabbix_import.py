#!/usr/bin/env python3
"""Import and reimport a template in a disposable Zabbix frontend only."""
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request


def main():
    url, source = sys.argv[1:]
    token = None

    def rpc(method, params):
        headers = {'Content-Type': 'application/json-rpc'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        request = urllib.request.Request(url, json.dumps(
            {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': 1}).encode(), headers)
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.load(response)
        if 'error' in result:
            raise RuntimeError(json.dumps(result['error']))
        return result['result']

    for attempt in range(100):
        try:
            token = rpc('user.login', {'username': 'Admin', 'password': 'zabbix'})
            break
        except (OSError, ValueError, RuntimeError):
            if attempt == 99:
                raise RuntimeError('Disposable Zabbix frontend did not become ready') from None
            time.sleep(3)
    rules = {name: {'createMissing': True, 'updateExisting': True}
             for name in ('templates', 'items', 'discoveryRules', 'graphs', 'triggers',
                          'templateDashboards', 'valueMaps')}
    rules['template_groups'] = {'createMissing': True}
    for _ in range(2):
        if rpc('configuration.import', {'format': 'yaml', 'source': Path(source).read_text(),
                                        'rules': rules}) is not True:
            raise RuntimeError('Import failed')
    templates = rpc('template.get', {'filter': {'host': 'FreeBSD IPFW by Zabbix Agent'},
                                     'output': ['templateid'], 'selectMacros': 'extend'})
    if len(templates) != 1:
        raise RuntimeError('Expected one template after reimport')
    template_id = templates[0]['templateid']
    discovery = rpc('discoveryrule.get', {'templateids': [template_id], 'output': ['key_', 'type'],
                                         'selectFilter': 'extend'})
    if not any(d['key_'] == 'ipfw.tables.discovery' and str(d['type']) == '18' for d in discovery):
        raise RuntimeError('Dependent table discovery missing')
    items = rpc('item.get', {'templateids': [template_id], 'output': ['key_']})
    if not {'ipfw.raw', 'ipfw.tables.raw', 'ipfw.inventory.raw'} <= {i['key_'] for i in items}:
        raise RuntimeError('Required master items missing')
    if not {'ipfw.rules.other', 'ipfw.reject.packets', 'ipfw.reject.bytes',
            'ipfw.reject.pps', 'ipfw.reject.bytes_per_second'} <= {i['key_'] for i in items}:
        raise RuntimeError('Additional rule/reject metrics missing')
    macros = {m['macro']: m['value'] for m in templates[0]['macros']}
    if macros.get('{$IPFW.TABLE.NAME.MATCHES}') != '.*' or macros.get('{$IPFW.TABLES.INTERVAL}') != '5m':
        raise RuntimeError('Configurable collection/discovery defaults missing')
    if not any(len(d['filter']['conditions']) == 4 for d in discovery):
        raise RuntimeError('Table name/set discovery filters missing')
    dashboards = rpc('templatedashboard.get', {'templateids': [template_id],
                                              'output': ['name'], 'selectPages': 'extend'})
    ipfw_dashboard = [d for d in dashboards if d['name'] == 'IPFW']
    if len(ipfw_dashboard) != 1 or len(ipfw_dashboard[0]['pages']) != 3:
        raise RuntimeError('Expected exactly one IPFW dashboard with three pages after reimport')
    print('PASS: import/reimport, master items, dependent discovery and three-page dashboard')


if __name__ == '__main__':
    main()
