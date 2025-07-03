def expand_url(url, new_length):
    # If length is less than current length, return current url unchanged.
    url_diff = new_length - len(url)
    if url_diff < 0:
        return url

    default_ports = {"http": "80", "https": "443"}

    # Split between protocol and url.
    protocol_split = url.split("://", maxsplit=1)

    # If current protocol does not exist, return current url unchanged.
    if protocol_split[0] not in default_ports:
        return url

    # Split url between domain:port and location.
    url_split = protocol_split[1].split("/", maxsplit=1)

    # Get location if any exists.
    location = ""
    if len(url_split) == 2:
        location = "/" + url_split[1]

    # Split domain:port.
    base_split = url_split[0].split(":", maxsplit=1)

    # Grab existing port if there's one or fall back to default ports.
    if len(base_split) == 2:
        port = base_split[1]
    else:
        port = default_ports[protocol_split[0]]
        url_diff -= (
            len(port) + 1
        )  # Discount the : and port characters that were not included in the original url.

    # Build new url.
    new_url = (
        protocol_split[0]
        + "://"
        + base_split[0]
        + ":"
        + "0" * url_diff
        + port
        + location
    )
    return new_url


