import re


def parse_user_agent(user_agent: str | None) -> dict[str, str]:
    """Lightweight User-Agent parser — no external dependency.

    Good enough for admin display (device/os/browser labels), not meant to
    be exhaustive.
    """

    if not user_agent:
        return {"device": "Unknown", "os": "Unknown", "browser": "Unknown"}

    ua = user_agent

    if re.search(r"iPad", ua):
        device = "Tablet"
    elif re.search(r"Tablet", ua):
        device = "Tablet"
    elif re.search(r"Mobile|iPhone|Android.*Mobile", ua):
        device = "Mobile"
    else:
        device = "Desktop"

    if re.search(r"Windows NT", ua):
        os_name = "Windows"
    elif re.search(r"Mac OS X", ua):
        os_name = "macOS"
    elif re.search(r"Android", ua):
        os_name = "Android"
    elif re.search(r"iPhone|iPad|iOS", ua):
        os_name = "iOS"
    elif re.search(r"Linux", ua):
        os_name = "Linux"
    else:
        os_name = "Unknown"

    if re.search(r"Edg/", ua):
        browser = "Edge"
    elif re.search(r"OPR/|Opera", ua):
        browser = "Opera"
    elif re.search(r"Chrome/", ua) and not re.search(r"Chromium", ua):
        browser = "Chrome"
    elif re.search(r"Firefox/", ua):
        browser = "Firefox"
    elif re.search(r"Safari/", ua) and re.search(r"Version/", ua):
        browser = "Safari"
    else:
        browser = "Unknown"

    return {"device": device, "os": os_name, "browser": browser}
