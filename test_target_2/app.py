"""
app.py

A second test application to verify reachability of Jinja2 and Urllib3.
"""

import jinja2
import urllib3


def start_app():
    print("Starting secure application...")
    html_content = render_page("Welcome to the workspace, {{ user }}!")
    print(html_content)


def render_page(template_str):
    # This function is reachable from start_app
    template = jinja2.Template(template_str)
    return template.render(user="Developer")


def download_asset():
    # This function is unreachable from start_app
    http = urllib3.PoolManager()
    response = http.request("GET", "https://example.com/asset.zip")
    return response.data
