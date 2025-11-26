from time import sleep
from game.network_client import NetworkClient

def main():
    client = NetworkClient()
    client.connect("127.0.0.1", 5000)

    # 1) Join phòng mới (host)
    client.send_message({"type": "join", "game_id": None})

    while True:
        msgs = client.poll_messages()
        for m in msgs:
            print("RECV:", m)
        sleep(0.1)

if __name__ == "__main__":
    main()