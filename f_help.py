import sys

def help():
    ret = ( "Usage: \n"
            "  python obnc.py -a 0.0.0.0 -p 11337\n"
            "  nohup python obnc.py -a 0.0.0.0 -p 11337\n"
            "\n"
            "Options: \n"
            "  -a        # ip where program runs\n"
            "  -p        # port on what runs\n" )
    print ret
    sys.exit(0)
