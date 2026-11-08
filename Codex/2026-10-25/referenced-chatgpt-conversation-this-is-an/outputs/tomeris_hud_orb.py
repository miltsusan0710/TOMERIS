"""Code-drawn concentric HUD; animation only while the app is working."""
import math
import tkinter as tk

class Orb(tk.Canvas):
    def __init__(self,parent,app,**kwargs):
        super().__init__(parent,bg='#08131f',highlightthickness=0,**kwargs)
        self.app=app;self.phase=0;self.resize_job=None;self.arc=None;self.state_text=None
        self.bind('<Configure>',self.schedule_draw)
        self.tick_job=self.after(100,self.tick)
    def schedule_draw(self,event=None):
        if self.resize_job:self.after_cancel(self.resize_job)
        self.resize_job=self.after(60,self.draw)
    def draw(self):
        self.resize_job=None
        w,h=self.winfo_width(),self.winfo_height();cx=w/2;cy=h/2;r=max(22,min(h/2-5,68))
        self.delete('all')
        for k in range(24):
            angle=k*math.pi/12
            inner=r*.91 if k%3 else r*.86
            self.create_line(cx+inner*math.cos(angle),cy+inner*math.sin(angle),cx+r*math.cos(angle),cy+r*math.sin(angle),fill='#326074',width=1)
        for scale,color,width in ((.82,'#326074',1),(.69,'#66dfef',2),(.57,'#214555',1)):
            rr=r*scale;self.create_oval(cx-rr,cy-rr,cx+rr,cy+rr,outline=color,width=width)
        rr=r*.82
        self.arc=self.create_arc(cx-rr,cy-rr,cx+rr,cy+rr,start=25,extent=65,style='arc',outline='#84f4ff',width=3)
        for n in range(18,0,-1):
            radius=r*.42*n/18;t=1-n/18
            color='#%02x%02x%02x'%(int(13+50*t),int(48+141*t),int(66+145*t))
            self.create_oval(cx-radius,cy-radius,cx+radius,cy+radius,fill=color,outline='')
        rr=r*.12;self.create_oval(cx-rr,cy-rr,cx+rr,cy+rr,fill='#a1f5ff',outline='')
        # Decorative guide lines, not fabricated telemetry.
        left=max(18,cx-r-180);right=min(w-18,cx+r+180)
        self.create_line(left,cy,cx-r-14,cy,fill='#214b60')
        self.create_line(cx+r+14,cy,right,cy,fill='#214b60')
        if w>450:
            self.create_text(cx-r-24,cy-15,text='T O M E R I S',anchor='e',fill='#73dcec',font=('Segoe UI',10,'bold'))
            self.state_text=self.create_text(cx+r+24,cy-15,text='',anchor='w',fill='#b6d4e0',font=('Yu Gothic UI',9))
        else:self.state_text=None
        self.update_state()
    def update_state(self):
        busy=self.app.busy and not self.app.closing
        if self.arc:self.itemconfigure(self.arc,start=self.phase,outline='#84f4ff' if busy else '#4594a8')
        if self.state_text:self.itemconfigure(self.state_text,text='処理中' if busy else '待機中')
    def tick(self):
        if self.app.busy and not self.app.closing:self.phase=(self.phase+5)%360
        self.update_state();self.tick_job=self.after(100,self.tick)
    def destroy(self):
        for job in (getattr(self,'tick_job',None),self.resize_job):
            if job:
                try:self.after_cancel(job)
                except tk.TclError:pass
        super().destroy()
