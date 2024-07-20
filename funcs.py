def load_proxies():
    proxy_list = []
    try:
        with open("proxies.txt", "r") as file:
            for line in file:
                proxy_list.append(line.strip())
    except FileNotFoundError:
        print("Error: proxies.txt file not found.")
    except IOError:
        print("Error: Unable to read proxies.txt file.")
    return proxy_list


import random

proxies = load_proxies()


def get_random_proxy_string():
    proxy = random.choice(proxies)
    ans = proxy.split(":")
    username = ans[0]
    rest = ans[1]
    password = rest.split("@")[0]
    host = rest.split("@")[1]
    port = ans[2]
    return f"http://{username}:{password}@{host}:{port}"