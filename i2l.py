def main():
    expr = input("请输入矩阵表达式的形式:")
    doPrint(list(map(doExprParse,expr)))    
    input("输入任意键结束程序")

def doExprParse(element:str):
    """解析表达式, 如果是矩阵符号则要求用户输入矩阵, 否则保持不变"""
    if element.isalpha():
        print("请输入矩阵",element)
        return getMatrix()
    else:
        return element

def getMatrix():
    matrix = []
    raw = input()
    while raw != "":
        matrix.append(list(map(doMacro,raw.split())))
        raw = input()
    return matrix

def doMacro(element):
    """解析宏, 如果是宏则进行相应的替换,否则保持不变"""
    if element == "|":
        return r"\vdots"
    elif element == "-":
        return r"\\cdots"
    elif element == "\\":
        return r"\ddots"
    else:
        return element


def doPrint(expr):
    print("$$")
    for v in expr:
        if type(v) == type(""):
            print(v)
        else:
            printMatrix(v)
    print("$$")

def printMatrix(matrix):
    print(r"\begin{bmatrix}")
    for line in matrix:
        # 元素之间插入分割符, 末尾添加换行符
        print(" & ".join(line), r"\\\\") # 插入分隔符的标准做法
    print(r"\end{bmatrix}")



if __name__ == "__main__":
    main()