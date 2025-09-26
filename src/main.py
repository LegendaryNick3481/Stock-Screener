import datetime
import web_socket
import web_socket_if_late

def main():
    """
    This function runs the appropriate trading bot script based on the current time.

    If the current time is before 9:15 AM, it runs the `web_socket.py` script.
    Otherwise, it runs the `web_socket_if_late.py` script.
    """
    now = datetime.datetime.now().time()

    # Ask the user for their choice
    print("Please choose which script to run:")
    print("1. Run automatically based on current time")
    print("2. Run web_socket.py (for starting before market open)")
    print("3. Run web_socket_if_late.py (for starting after market open)")

    choice = input("Enter your choice (1, 2, or 3): ")

    if choice == '1':
        if now < datetime.time(9, 15):
            print("Running web_socket.py")
            app = web_socket.FyersLiveTracker()
            app.run()
        else:
            print("Running web_socket_if_late.py")
            app = web_socket_if_late.FyersLiveTracker()
            app.run()
    elif choice == '2':
        print("Running web_socket.py")
        app = web_socket.FyersLiveTracker()
        app.run()
    elif choice == '3':
        print("Running web_socket_if_late.py")
        app = web_socket_if_late.FyersLiveTracker()
        app.run()
    else:
        print("Invalid choice. Please run the script again and enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
