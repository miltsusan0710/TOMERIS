from pathlib import Path
p=Path('outputs/tomeris_plans.py')
s=p.read_text(encoding='utf-8-sig').replace("        response=LocalProvider(model=model)._request", "        if self.demo:\n            return validate(goal,budget,[{'title':'最初の作業を進める','minutes':budget}])\n        response=LocalProvider(model=model)._request")
p.write_text(s,encoding='utf-8')
