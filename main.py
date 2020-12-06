#import keyboard
import time
import json
from ssr import SsrController
from temp_reader import TempReader
from threading import Event
import sys
import queue

import RPi.GPIO as GPIO


def main():

    """
    with open("./config.json", mode="r") as fr:
        conf_dict = json.load(fr)
 
    print(conf_dict)
    exit()
    """

    q_tc_temp = queue.Queue()
    # stop_event = Event()
    # stop_event.clear()
    str_port_list = ["/dev/ttyUSB0"]
    list_temp_reader = []
    rate = 115200
    for i, str_port in enumerate(str_port_list):
        save_file = f"output_{i}.txt"
        temp_reader = TempReader(str_port=str_port, rate=rate, save_file=save_file, q_tc_temp=q_tc_temp)
        temp_reader.start()
        list_temp_reader.append(temp_reader)
    time.sleep(1)


    # SSR制御スレッド
    # pin number is as on the RsPi4 board
    #ssr_pins = [2, 3, 4, 10, 9,11, 5,6,13,19,26, 14,15,18]     # SSR PWM output pins
    ssr_pins = [2, 3, 4, 9]  #{201122}
    
    #system configulation {201117}
    sys_config={
    "items":("key: =group_numnerof heater and thermo-couple", ("ssr_pins"),("Tc's") ),
    "g1":( (2, 4), (0, 2) ),
    "g2":( (3, 9), (1, 3) ),    
    }
    g="g1"
    print(f"sys_config= {sys_config[g]}")

    # スレッド起動
    list_ssr = []
    for i, pin_num in enumerate(ssr_pins):
        ssr = SsrController(pin_num, q_tc_temp=q_tc_temp)
        ssr.start()
        list_ssr.append(ssr)

    try:
        while True:
            time.sleep(1)

            # print(f"que_len: {q_tc_temp.qsize()}")
            pass
    except KeyboardInterrupt:
        # Ctrl-C
        print('interrupted!')

        # SSR を先に止める
        for i, ssr in enumerate(list_ssr):
            # print (f"exiting at ssr.join({i})")
            ssr.close()
            time.sleep(0.1)

        time.sleep(1)

        for i, temp_reader in enumerate(list_temp_reader):
            # print (f"exiting at temp_reader.join({i})")
            temp_reader.close()
            time.sleep(0.1)


        GPIO.cleanup()
        time.sleep(1)

        print("call exit!")
        exit()


if __name__ == "__main__":
    
    # setting.init()
    main()
