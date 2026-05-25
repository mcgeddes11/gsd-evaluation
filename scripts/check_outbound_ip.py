import subprocess


def check_wan_ip():
    # The router fucking hard codes the WAN IP in the page javascript, incredible
    HARD_CODED_WAN_IP_ADDRESS = '75.155.243.79'
    # We just have to ensure the output matches
    result = subprocess.run(['curl', '-4', 'ifconfig.me'], capture_output=True, text=True)

    if result.stdout == HARD_CODED_WAN_IP_ADDRESS:
        print("WAN IP matches")
        return True
    else:
        print("WAN IP does NOT match")
        return False

if __name__ == '__main__':
    check_wan_ip()
