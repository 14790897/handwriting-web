import sympy

# 将 LaTeX 转换为 SymPy 表达式
expression = sympy.sympify("x**2 + 2*x + 1", evaluate=False)

# 将 SymPy 表达式转换为文字描述
text_description = sympy.pretty(expression, use_unicode=True)

print(text_description)


from sympy.parsing.latex import parse_latex

expression = parse_latex(r"\frac{x}{y} + \sqrt{x^2+1}")

# 打印 SymPy 表达式
print(expression)

# 转换为更可读的格式
text_description = sympy.pretty(expression, use_unicode=True)
print(text_description)
