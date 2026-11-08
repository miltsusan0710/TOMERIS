from pathlib import Path
root=Path('outputs')
s=(root/'tomeris_desktop_v010.py').read_text(encoding='utf-8-sig')
s=s.replace('v0.10','v0.11')
s=s.replace('from tomeris_plans import DesktopService as PlanService, validate, today','from tomeris_plans import validate, today\nfrom tomeris_plan_progress import DesktopService as PlanService\nfrom tomeris_today_ui import TodayPanel')
s=s.replace("    def open_google(self):", "        panel=getattr(self,'today_panel',None)\n        if panel is not None:\n            panel.state()\n    def open_google(self):")
s=s.replace("    def view(self,kind):\n", "    def view(self,kind):\n        if kind=='today':\n            if not self.busy and not self.closing:\n                self.today_panel=TodayPanel(self)\n            return\n")
s=s.replace("                        if not google_open and not (", "                        today_open=getattr(self,'today_panel',None) and self.today_panel.window.winfo_exists()\n                        if not today_open and not google_open and not (")
(root/'tomeris_desktop_v011.py').write_text(s,encoding='utf-8')
