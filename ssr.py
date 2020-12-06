import sys, queue
import re
import time
import datetime

from threading import Thread
import RPi.GPIO as GPIO



# （threadで runしている classの）外のName空間で、SSRアルゴリズムを定義する。 {201129}
sys_config={
            "items":("key: =group_numnerof heater and thermo-couple", ("ssr_pins"),("tc num")),
            "g1":( (2, 4), (0, 2) ),
            "g2":( (3, 9), (1, 3) ),    
           }
g="g1"
print(f"sys_config= {sys_config[g]}")
g="g2"
print(f"sys_config= {sys_config[g]}")
        

def group1(pin_num, list_tc_temp):
        tc_temp_max= max(list_tc_temp)
        tc_temp_av = sum(list_tc_temp) / len(list_tc_temp) #{201122}
        print(f"SSR({pin_num}) Tc: {tc_temp_av:.2f}") #{201122}
        target_temp=40
        print("tc_temp_max=", tc_temp_max)
        """
        温度上昇速度が、「自然冷却で温度を下げられる速度」より、速くなると、
        計測の目標温度をオーバーシュートする。（通常の制御ではこれを許容する）
        ただし、十分に、注意すべし。
        """
        pwm_width = round( (target_temp - tc_temp_max) / 10 )
        print(f"group1 pwm_width= {pwm_width}") 
        return pwm_width

        
def group2(pin_num, list_tc_temp):
        tc_temp_max= max(list_tc_temp)
        tc_temp_av = sum(list_tc_temp) / len(list_tc_temp) #{201122}
        print(f"SSR({pin_num}) Tc: {tc_temp_av:.2f}") #{201122}
        target_temp=40
        print("tc_temp_max=", tc_temp_max)
        pwm_width = round( (target_temp - tc_temp_max) / 10 )
        return pwm_width
        

class SsrController(Thread):
    """
    プログラム構造
    　main 
    　　　　=> TempReader
    　　　　=> SsrController
    　以下 SSR pin の番号で順番に処理している（と想定している）
    　  for each pin-number of SSR:
    　  SsrController
    　    　==> run 
    　    　      append(float(self.q_tc_temp.get()
    　    　      ==> pwm_width = self.get_pwm_width
    　    　          ==>  ((_goup1), (group2), (group3))
    　    　      ==> set_pwm_width(pwm_width)
    
    """

    def __init__(self, pin_num, q_tc_temp):
        Thread.__init__(self)
        print(f"init SSR PIN({pin_num})")

        self.q_tc_temp = q_tc_temp
        self.running = True
        self.pin_num = pin_num
        self.d_temp = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin_num, GPIO.OUT)
        time.sleep(0.1)
        GPIO.output(self.pin_num, False)
        
        
       
    def run(self):
        """
        ここはスレッドの中、SSR pin 番号ごとに処理している。
        """
        time.sleep(0.2)
        print(f"start SSR PIN({self.pin_num})")
   
        target_temp = 20 #room temperature  {201117}
  
        while self.running:
            try:
                list_tc_temp = []
                while not self.q_tc_temp.empty():
                    time_stamp_image=self.q_tc_temp.get()[0]    #{201130}
                    time_seconds=time_stamp_image.total_seconds()
                    print("time_seconds",time_seconds)
                    list_tc_temp.append(float(self.q_tc_temp.get()[1]))   #{201116} {201130}
                    list_tc_temp.append(float(self.q_tc_temp.get()[2])) 
                    list_tc_temp.append(float(self.q_tc_temp.get()[3])) 
                    list_tc_temp.append(float(self.q_tc_temp.get()[4])) 
                    #list_tc_temp.append(float(self.q_tc_temp.get()))

                    #tc_temp_av = sum(list_tc_temp) / len(list_tc_temp) #{201122}
                    #print(f"SSR({self.pin_num}) Tc: {tc_temp_av:.2f}") #{201122}

                    pwm_width = self.get_pwm_width(target_temp, list_tc_temp) #group1

                    print("#### self.pin_num, pwm_width=",self.pin_num, pwm_width, "     ####")

                    self.set_pwm_width(pwm_width)
                # time.sleep(1)
            except KeyboardInterrupt:
                print (f'exiting thread-1 in temp_read({self.pin_num})')
                self.close()

    
    def get_pwm_width(self, target_temp, list_tc_temp):
        """
        グループのデータベース（機器の設計で固定される）を sys_config_ssr_Tc で記述する
        """
        sys_config_ssr_Tc_group1= ((2, 3, 4, 5), (0, 1, 2, 3))
        """
        {201122}
        pin_numが、どのグループに属するかを調べて、そのグループのTcの値を見て、その
        グループのロジックで pwm_width を算出する
        （インデックスの取り回し方は、グループの情報で、どうにでも作れば良い）
        （どのグループに属するかを調べて、そのグループのロジック関数を呼び出す）
        """
        print(f"sys_config_ssr_Tc_group1= {sys_config_ssr_Tc_group1}")
        print(f"pin_num = {self.pin_num} in get_pwm_width")

        tc_temp = [] #{201117}
        if len(list_tc_temp) > 0:
           print(f"list_tc_temp {list_tc_temp}")     #{201116}
           tc_temp =[list_tc_temp[0],list_tc_temp[1],list_tc_temp[2],list_tc_temp[3]]

        # SSR ごとに、異なる運用を行わなければならない {201117}
        # ここから、以下が、SSR（加熱）の制御を、グループ別に行うロジックを置くところ：
                
        pwm_width = 0
        if self.pin_num in [2,3]:
          print("calculate_pwm_width for 2,4 using tc of 0,2")
          pwm_width=group1(self.pin_num, list_tc_temp)
          print(f"after group1, pin_num= {self.pin_num}, pwm_width={pwm_width}")

        if self.pin_num in [4,5]:
          print("calculate_pwm_width for 3,9 using tc of 1,3")
          pwm_width=group2(self.pin_num, list_tc_temp)
        
        
        # below is original before group1, group2 were introduced.
        """
        tc_temp_max= max(list_tc_temp)
        tc_temp_av = sum(list_tc_temp) / len(list_tc_temp) #{201122}
        print(f"SSR({self.pin_num}) Tc: {tc_temp_av:.2f}") #{201122}

        target_temp=50
        print("tc_temp_max=", tc_temp_max)
        
        pwm_width = round( (target_temp - tc_temp_max) / 10 )
        """

        # ここまで、以上が、SSR（加熱）の制御を、グループ別に行うロジックを置くところ unquote


        print(f"pwm_width = {pwm_width} before limit")
        if pwm_width > 10:
            pwm_width = 10
        elif pwm_width < 0:   #{201130}
            pwm_width = 0

        return pwm_width


    def set_pwm_width(self, pwm_width):
        
        pwm_total_time = 1.0
        on_time = pwm_total_time * pwm_width / 10
        off_time = pwm_total_time * (10 - pwm_width) / 10
        # print(f"on: {on_time}, off: {off_time}")
        GPIO.output(self.pin_num, True)
        time.sleep(on_time)
        GPIO.output(self.pin_num, False)
        time.sleep(off_time)

        print(f"SSR({self.pin_num}) pwm_width = {pwm_width}")



    def close(self):
        print(f"close SSR: {self.pin_num}")
        self.running = False

