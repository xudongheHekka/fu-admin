import requests

def get_ip_info(ip_address):
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        data = response.json()

        if response.status_code == 200:
            return {
                "IP": ip_address,
                "City": data.get("city", "N/A"),
                "Region": data.get("region", "N/A"),
                "Country": data.get("country", "N/A")
            }
        else:
            return {"Error": "Unable to fetch data"}
    except Exception as e:
        return {"Error": str(e)}

ip_addresses = [
    "61.243.168.223", "61.243.168.74", "39.144.55.173", "39.144.55.180",
    "39.144.55.143", "61.243.170.84", "61.243.170.243", "116.140.152.102",
    "39.144.55.157", "39.144.55.153", "175.167.139.97", "42.6.104.3",
    "175.167.139.146", "39.144.59.48", "175.167.139.208", "39.144.57.192",
    "175.167.139.228", "116.140.48.15", "182.200.76.10", "116.140.51.72",
    "175.167.145.244", "175.167.155.11", "116.140.48.154", "42.179.201.102",
    "42.84.232.96", "175.167.145.5", "175.167.155.71", "175.167.155.177",
    "175.167.145.21", "61.243.169.170", "42.84.234.84", "175.167.129.194",
    "175.167.139.188", "175.167.139.52", "175.167.155.199", "175.167.155.249",
    "175.167.145.173", "175.167.155.27", "175.167.145.50", "175.167.139.94",
    "175.167.155.208", "175.167.145.122", "175.167.155.245", "175.167.155.221",
    "175.167.145.170", "39.144.59.150", "175.167.139.57", "39.144.39.29",
    "39.144.59.24", "175.167.139.79", "175.167.129.95", "175.167.139.178",
    "175.167.129.127", "39.144.59.96", "39.144.59.129", "39.144.59.97",
    "39.144.59.57", "39.144.59.123", "39.144.59.38", "175.167.155.214",
    "39.144.57.227", "39.144.59.124", "175.167.139.56", "175.167.139.230",
    "39.144.59.176", "39.144.60.200", "39.144.60.229", "39.144.60.227",
    "175.167.130.32", "175.167.129.214", "175.167.155.91", "175.167.129.240",
    "175.167.155.72", "175.167.129.79", "175.167.155.226", "61.243.168.216",
    "116.140.49.39", "42.6.107.99", "42.6.113.70", "175.167.155.151",
    "175.167.128.211", "175.167.145.194", "175.167.129.16", "175.167.155.190",
    "175.167.139.14", "175.167.145.138", "175.167.139.161", "175.167.155.205",
    "175.167.155.7", "175.167.129.86", "175.167.155.86", "175.167.139.92",
    "175.167.145.218", "175.167.139.163", "175.167.155.118", "175.167.145.137",
    "60.19.191.179", "42.84.233.174"
]

with open("ip_info.txt", "w") as file:
    for ip in ip_addresses:
        info = get_ip_info(ip)
        record = f"IP: {info.get('IP')}, City: {info.get('City')}, Region: {info.get('Region')}, Country: {info.get('Country')}\n"
        file.write(record)
