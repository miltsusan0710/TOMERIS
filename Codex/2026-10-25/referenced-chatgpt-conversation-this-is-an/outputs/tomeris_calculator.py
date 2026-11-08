"""Bounded exact arithmetic. No eval, code execution, files, or network."""
import ast
from decimal import Decimal, localcontext
from fractions import Fraction
import re
import unicodedata

class CalculationError(ValueError): pass

def expression_from(text):
    text=unicodedata.normalize('NFKC',text).strip()
    explicit=text.startswith(('計算:','計算：','計算して')) or text.endswith(('を計算して','を計算してください'))
    text=re.sub(r'^(計算[:：]|計算して[:：]?)[ ]*','',text)
    text=re.sub(r'(を計算してください|を計算して|は[?？]?|=[?？]?|[?？])$','',text).strip()
    percent=re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)\s*(?:円)?の\s*([0-9]+(?:\.[0-9]+)?)\s*%',text)
    if percent: return f'{percent[1]}*{percent[2]}/100'
    text=text.replace('×','*').replace('÷','/').replace('^','**').replace('−','-')
    if re.fullmatch(r'[0-9.\s+*/()%-]+',text) and re.search(r'\d',text): return text
    if explicit: raise CalculationError('数式で入力してください。例：計算: (1200 + 800) * 1.1 ／ 12000の15%')
    return None

def calculate(expression):
    if len(expression)>200: raise CalculationError('計算式は200文字以内にしてください。')
    try: tree=ast.parse(expression,mode='eval')
    except (SyntaxError,ValueError): raise CalculationError('計算式を読み取れません。括弧や記号を確認してください。') from None
    if len(list(ast.walk(tree)))>100: raise CalculationError('計算式が複雑すぎます。')
    def visit(node):
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):
            token=ast.get_source_segment(expression,node)
            if not token or not re.fullmatch(r'(?:\d+(?:\.\d*)?|\.\d+)',token) or len(token)>40: raise CalculationError('数値は40桁以内の整数・小数で入力してください。')
            value=Fraction(token)
        elif isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            value=visit(node.operand); value=-value if isinstance(node.op,ast.USub) else value
        elif isinstance(node,ast.BinOp):
            a,b=visit(node.left),visit(node.right)
            if isinstance(node.op,ast.Add): value=a+b
            elif isinstance(node.op,ast.Sub): value=a-b
            elif isinstance(node.op,ast.Mult): value=a*b
            elif isinstance(node.op,ast.Div): value=a/b
            elif isinstance(node.op,ast.Pow):
                if b.denominator!=1 or abs(b)>100: raise CalculationError('累乗の指数は-100〜100の整数にしてください。')
                value=a**int(b)
            else: raise CalculationError('使える演算は + - * / と累乗、括弧です。')
        else: raise CalculationError('関数やプログラムは実行できません。数式だけ入力してください。')
        if max(abs(value.numerator).bit_length(),value.denominator.bit_length())>2048: raise CalculationError('計算結果が大きすぎます。式を小さくしてください。')
        return value
    try: value=visit(tree.body)
    except ZeroDivisionError: raise CalculationError('0では割れません。') from None
    with localcontext() as ctx:
        ctx.prec=28
        number=Decimal(value.numerator)/Decimal(value.denominator)
    exact=Fraction(number)==value
    result=format(number,'f')
    if len(result)>120: result=str(number)
    if '.' in result and 'E' not in result: result=result.rstrip('0').rstrip('.')
    return f'計算式：{expression}\n結果：{result}'+('' if exact else f'（約・有効数字28桁）\n正確な分数：{value}')+'\n計算処理で求めました。AIによる推測ではありません。'
