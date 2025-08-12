import argparse
import importlib
import sys

def main():
    parser = argparse.ArgumentParser(description="Run SSTV either from your webcam or from your screen.")
    parser.add_argument("module", choices=["cam", "screen"], help="Specify which module to run: 'cam' or 'screen'")

    args = parser.parse_args()

    if args.module == "cam":
        try:
            cam_module = importlib.import_module("cam")
            cam_module.cam_main()
        except ImportError:
            print("Could not import 'cam.py'. Make sure it exists and is in the same directory.")
            sys.exit(1)

    elif args.module == "screen":
        try:
            screen_module = importlib.import_module("screen")
            screen_module.screen_main()
        except ImportError:
            print("Could not import 'screen.py'. Make sure it exists and is in the same directory.")
            sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # show help
        parser = argparse.ArgumentParser(description="Run SSTV either from your webcam or from your screen.")
        parser.add_argument("module", choices=["cam", "screen"], help="Specify which module to run: 'cam' or 'screen'")
        parser.print_help()
    else:
        main()
