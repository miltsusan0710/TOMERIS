from pathlib import Path
p=Path('outputs/tomeris_desktop_v013.py')
s=p.read_text(encoding='utf-8-sig')
s=s.replace('        self.events=queue.Queue()', '        self.events=queue.Queue()\n        self.result_callbacks={}')
s=s.replace("                value=func()\n                self.events.put((kind,value))", "                value=func()\n                if kind=='plan_result':\n                    callback,result=value\n                    token=object()\n                    self.result_callbacks[token]=callback\n                    value=(token,result)\n                    callback=None\n                func=None; job=None\n                self.events.put((kind,value))")
s=s.replace("                        callback,result=value\n                        callback(result)", "                        token,result=value\n                        callback=self.result_callbacks.pop(token)\n                        callback(result)\n                        callback=None")
p.write_text(s,encoding='utf-8')
