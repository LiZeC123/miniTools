# coding=utf-8
from enum import Enum
from typing import List

'''
由于输入的数据很多, 所以采取编译模式
输入一个简单格式的文件, 转化为流程图的格式

输入文件格式如下
--- 定义段 ---
[] 操作节点
<> 判断节点
...
--- 操作段 ---
st 1 2 3 4
2y 5 
2n 8
8 ed
...

st和ed是内置变量, 分别表示开始节点和结束节点

使用行号作为变量名, 所以文件的绝对位置不可改变, 否则会导致操作段的引用失效

'''

'''
<语句>        -> <声明> | <操作>
<声明>        -> <声明类型> <声明取值>
<声明类型>    -> <> | [] | {}
<声明取值>    -> string
<操作>        -> <标识符><变量表>
<变量表>      -> <变量><变量表> | e
<变量>        -> <数字><分支选项>
<分支选项>    -> y | n | e

由于结构十分简单, 因此不需要词法分析, 可以直接处理
'''

segmentFirst = frozenset(['<', '>', '[', ']', '{', '}'])


class VarType(Enum):
    INVALID = -1
    EXIT = 0
    OPERATION = 1
    CONDITION = 2
    START = 3
    END = 4
    SELECTED = 5  # 包含选择的条件语句 即yes分支或者no分支


class Var:
    def __init__(self, num: int, varType: VarType, info: str, select: str = "N/A"):
        self.num = num
        self.varType = varType
        self.info = info
        self.select = select

    def copy(self):
        return Var(self.num, self.varType, self.info, self.select)

    def toDef(self):
        if self.varType == VarType.CONDITION:
            return f"cnd{self.num}=>condition: {self.info}"
        elif self.varType == VarType.OPERATION:
            return f"opt{self.num}=>operation: {self.info}"
        elif self.varType == VarType.START:
            return f"st=>start: 开始"
        elif self.varType == VarType.END:
            return f"ed=>end: 结束"

    def toConnectName(self):
        if self.varType == VarType.CONDITION:
            return f"cnd{self.num}"
        elif self.varType == VarType.OPERATION:
            return f"opt{self.num}"
        elif self.varType == VarType.START:
            return f"st"
        elif self.varType == VarType.END:
            return f"ed"
        if self.varType == VarType.SELECTED:
            return f"cnd{self.num}({self.select})"


# 特殊节点, 输出时进行特出处理, 因此只需要保证类型正确即可
NoneVar = Var(0, VarType.INVALID, "")   # 无效节点
StartVar = Var(0, VarType.START, "")    # 开始节点
EndVar = Var(0, VarType.END, "")        # 结束节点


class Line:
    def __init__(self, num: int, value: str):
        self.num = num
        self.value = value


class Parser:
    def __init__(self, filename: str):
        self.varTable: List[Var] = [StartVar, EndVar]
        self.connectTable: List[List[Var]] = []
        self.filename = filename

    def parseFile(self):
        with open(self.filename, "r", encoding="utf8") as f:
            num = 0
            for line in f.readlines():
                num += 1
                if not line.isspace():
                    self.parseLine(Line(num, line.replace("\n", "")))

    def parseLine(self, line: Line):
        if line.value[0] in segmentFirst:
            self.parseDef(line)
        else:
            self.parseStatement(line)

    def genCode(self):
        for var in self.varTable:
            print(var.toDef())
        print("\n")
        for con in self.connectTable:
            print("->".join(v.toConnectName() for v in con))

    def parseDef(self, line: Line):
        if line.value[0] == '<':
            info = line.value.replace("<>", "")
            self.varTable.append(Var(line.num, VarType.CONDITION, info))
        elif line.value[0] == '[':
            info = line.value.replace("[]", "")
            self.varTable.append(Var(line.num, VarType.OPERATION, info))
        else:
            print("不支持以{}开始的声明")

    def parseStatement(self, line: Line):
        connects: List[Var] = []
        s = line.value.split()
        for var in s:
            if var == "st":
                connects.append(StartVar.copy())
            elif var == "ed":
                connects.append(EndVar.copy())
            else:
                self.parseNum(connects, var)
        self.connectTable.append(connects)

    def parseNum(self, connects, var):
        select = "N/A"
        if var[-1] == "y":
            select = "yes"
        elif var[-1] == "n":
            select = "no"

        var = var.replace("y", "").replace("n", "")
        try:
            varId = int(var)
            v = self.findVarById(varId)
            connects.append(self.setTypeBySelect(v, select))
        except ValueError:
            print(f"标识符{var}无效")

    def findVarById(self, varId: int) -> Var:
        for var in self.varTable:
            if var.num == varId:
                return var.copy()
        return NoneVar

    @staticmethod
    def setTypeBySelect(var: Var, select: str) -> Var:
        if select == "N/A":
            return var
        else:
            var.select = select
            var.varType = VarType.SELECTED
            return var


if __name__ == "__main__":
    parser = Parser("flowInput")
    parser.parseFile()
    parser.genCode()
