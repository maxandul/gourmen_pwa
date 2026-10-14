"""Explicit form-opening helper for pre-existing successful mutation tests."""
import re


def confirmed_post(client, path, *, data, password, **kwargs):
    page = client.get(path)
    match = re.search(r'name="action_token" value="([^"]+)"', page.text)
    payload = dict(data)
    if match:
        payload['action_token'] = match.group(1)
        payload['action_password'] = password
    return client.post(path, data=payload, **kwargs)
