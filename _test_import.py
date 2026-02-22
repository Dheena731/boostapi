import traceback, sys

with open("_err_full.txt", "w") as f:
    try:
        from boostapi import create_app
        f.write("OK - create_app imported\n")
    except Exception:
        traceback.print_exc(file=f)

with open("_err_full.txt") as f:
    print(f.read())
