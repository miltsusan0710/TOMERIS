"""Code-drawn soft cyan orb; no external assets or dependencies."""
import math
import tkinter as tk

class Orb(tk.Canvas):
    def __init__(self,parent,app,**kwargs):
        super().__init__(parent,bg='#edf5f8',highlightthickness=0,**kwargs)
        self.app=app;self.phase=0;self.photo=None;self.arc=None;self.resize_job=None
        self.bind('<Configure>',self.schedule_draw)
        self.tick_job=self.after(100,self.tick)
    def schedule_draw(self,event=None):
        if self.resize_job: self.after_cancel(self.resize_job)
        self.resize_job=self.after(80,self.draw)
    def draw(self):
        self.resize_job=None
        if not self.winfo_exists():return
        w,h=self.winfo_width(),self.winfo_height();size=max(30,min(h-8,150));r=size*.28;c=(size-1)/2
        pixels=bytearray()
        background=(237,245,248)
        for y in range(size):
            for x in range(size):
                d=math.hypot(x-c,y-c)
                halo=.16*math.exp(-(d/(r*1.35))**2)
                color=[int(v+(t-v)*halo) for v,t in zip(background,(104,199,215))]
                if d<r:
                    light=math.exp(-(((x-c+r*.15)/(r*.65))**2+((y-c+r*.2)/(r*.65))**2))
                    rim=max(0,1-(d/r)**2)**.4
                    color=[int(a+(b-a)*(.35*rim+.65*light)) for a,b in zip((42,124,147),(167,235,241))]
                pixels.extend(color)
        self.photo=tk.PhotoImage(data=f'P6\n{size} {size}\n255\n'.encode()+bytes(pixels),format='PPM')
        self.delete('all');cx=w/2;cy=h/2
        self.create_image(cx,cy,image=self.photo)
        rr=size*.44
        self.create_oval(cx-rr,cy-rr,cx+rr,cy+rr,outline='#c1dce5',width=1.5)
        self.arc=self.create_arc(cx-rr,cy-rr,cx+rr,cy+rr,start=30,extent=40,style='arc',outline='#459eb3',width=2)
        self.create_oval(cx+rr-3,cy-3,cx+rr+3,cy+3,fill='#8cc6d5',outline='')
    def tick(self):
        if not self.winfo_exists():return
        if self.arc:
            busy=self.app.busy and not self.app.closing
            if busy:self.phase=(self.phase+5)%360
            self.itemconfigure(self.arc,start=self.phase,outline='#459eb3' if busy else '#a7ceda')
        self.tick_job=self.after(100,self.tick)

    def destroy(self):
        for job in (getattr(self,'tick_job',None),self.resize_job):
            if job:
                try:self.after_cancel(job)
                except tk.TclError:pass
        super().destroy()
