import time
import sys

# Определяем имя файла на основе аргумента (или по умолчанию)
bot_name = sys.argv[1] if len(sys.argv) > 1 else "test_bot"
log_file = f"{bot_name}.log"

def main():
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n--- [{bot_name.upper()} STARTED] ---\n")
    
    count = 1
    try:
        while True:
            msg = f"[{time.strftime('%H:%M:%S')}] {bot_name}: Heartbeat tick {count}. RAM stable.\n"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(msg)
            count += 1
            time.sleep(2)
    except KeyboardInterrupt:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {bot_name}: Process terminated.\n")

if __name__ == "__main__":
    main()