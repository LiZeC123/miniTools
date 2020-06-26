# coding=utf-8
import sys
from enum import Enum
from typing import List


class VarType(Enum):
    INVALID = -1
    EXIT = 0
    OPERATION = 1
    CONDITION = 2
    SUBROUTINE = 3
    START = 4
    END = 5
    SELECTED = 6  # 包含选择的条件语句 即yes分支或者no分支


class ConnectType(Enum):
    NONE = 0,
    NORMAL = 1,
    YSE = 2,
    NO = 3,
    LEFT = 4,
    RIGHT = 5,
    TOP = 6,
    BOTTOM = 7


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
        elif self.varType == VarType.SUBROUTINE:
            return f"sub{self.num}=>subroutine: {self.info}"
        elif self.varType == VarType.START:
            return f"st=>start: 开始"
        elif self.varType == VarType.END:
            return f"ed=>end: 结束"

    def toConnectName(self):
        if self.varType == VarType.CONDITION:
            return f"cnd{self.num}"
        elif self.varType == VarType.OPERATION:
            return f"opt{self.num}"
        elif self.varType == VarType.SUBROUTINE:
            return f"sub{self.num}"
        elif self.varType == VarType.START:
            return f"st"
        elif self.varType == VarType.END:
            return f"ed"
        if self.varType == VarType.SELECTED:
            return f"cnd{self.num}({self.select})"


class Node:
    def __init__(self, info: str, varType: VarType, connectType: ConnectType):
        self.info = info
        self.varType = varType
        self.connectType = connectType


class VarTable:
    # 特殊节点, 输出时进行特出处理, 因此只需要保证类型正确即可
    NoneVar = Var(-1, VarType.INVALID, "")  # 无效节点
    StartVar = Var(0, VarType.START, "")  # 开始节点
    EndVar = Var(1, VarType.END, "")  # 结束节点

    def __init__(self):
        self.table: List[Var] = [self.StartVar, self.EndVar]
        self.currentID = 1

    def addVar(self, info, varType: VarType) -> Var:
        self.currentID += 1
        var = Var(self.currentID, varType, info)
        self.table.append(var)
        return var

    def getVarByNode(self, node: Node) -> Var:
        if node.varType == VarType.START:
            return self.StartVar.copy()
        elif node.varType == VarType.END:
            return self.EndVar.copy()

        for v in self.table:
            if v.info == node.info and v.varType == node.varType:
                return v.copy()

        return self.addVar(node.info, node.varType)

    def getVarByID(self, ID: int):
        return self.table[ID]

    def getVarNum(self):
        return len(self.table)

    def genCode(self, f):
        for var in self.table:
            f.write(var.toDef())
            f.write("\n")


class ConnectTable:
    def __init__(self):
        self.length = 15
        self.graph: List[List[ConnectType]] = [[ConnectType.NONE for col in range(self.length)] for row in
                                               range(self.length)]
        self.ConnectNameDict = {
            ConnectType.YSE: "yes", ConnectType.NO: "no",
            ConnectType.LEFT: "left", ConnectType.RIGHT: "right",
            ConnectType.TOP: "top", ConnectType.BOTTOM: "bottom"
        }

    def resize(self, toSize: int):
        differ = toSize - self.length
        for row in self.graph:
            for i in range(differ):
                row.append(ConnectType.NONE)
        self.length = toSize

    def addConnect(self, head: int, tail: int, conType: ConnectType):
        if head >= self.length or tail >= self.length:
            self.resize(max(head, tail))
        self.graph[head][tail] = conType

    def getNameByCon(self, con: ConnectType):
        return self.ConnectNameDict[con]

    def genCode(self, varTable: VarTable, f):
        code = []
        self.DFS(varTable, 0, code)
        for c in self.reduceCode(code):
            f.write(c)

    def DFS(self, varTable: VarTable, row, code):
        for col in range(len(self.graph[row])):
            con = self.graph[row][col]
            if con != ConnectType.NONE:
                if con == ConnectType.NORMAL:
                    name = f"{varTable.getVarByID(row).toConnectName()}"
                else:
                    name = f"{varTable.getVarByID(row).toConnectName()}({self.getNameByCon(con)})"
                code.append(name)
                code.append("->")
                code.append(f"{varTable.getVarByID(col).toConnectName()}")
                code.append("\n")
                self.DFS(varTable, col, code)

    @staticmethod
    def reduceCode(code: List[str]):
        newCode = []
        length = len(code)
        i = 0
        while i < length:
            if code[i] != "\n":
                newCode.append(code[i])
            elif i + 1 < length and code[i - 1] == code[i + 1]:
                newCode.append("->")
                i += 2
            else:
                newCode.append("\n")
            i += 1

        # 由于部分分支节点需要多次遍历, 因此不能在深度优先算法中直接将遍历过的路径重置
        # 否则分支节点只会出现一次
        lineCode = []
        s = ""
        for c in newCode:
            s += c
            if c == "\n":
                lineCode.append(s)
                s = ""

        return frozenset(lineCode)

    def checkIntegrity(self, varTable: VarTable):
        """检查每个节点是否有入度, 每个条件节点是否有两个分支"""
        length = varTable.getVarNum()
        node = 2  # 跳过start和end节点
        while node < length:
            self.checkReference(node, varTable)
            if varTable.getVarByID(node).varType == VarType.CONDITION:
                self.checkBranch(node, varTable)
            node += 1

    def checkBranch(self, node, varTable: VarTable):
        yNode = False
        nNode = False
        for col in range(len(self.graph)):
            if self.graph[node][col] == ConnectType.YSE:
                yNode = True
            elif self.graph[node][col] == ConnectType.NO:
                nNode = True
        if not yNode:
            raise CheckException(f"Node ({varTable.getVarByID(node).info}) is missing a yes branch")
        elif not nNode:
            raise CheckException(f"Node ({varTable.getVarByID(node).info}) is missing a no branch")

    def checkReference(self, node, varTable: VarTable):
        referenced = False
        for row in range(len(self.graph)):
            if self.graph[row][node] != ConnectType.NONE:
                referenced = True
                break
        if not referenced:
            raise CheckException(f"Node ({varTable.getVarByID(node).info}) is not referenced by any node")


class Line:
    def __init__(self, num: int, value: str):
        self.num = num
        self.value = value


NoneLine = Line(0, "NoneLine")


class Parser:
    connectNameDict = {
        "y": ConnectType.YSE, "n": ConnectType.NO,
        "l": ConnectType.LEFT, "r": ConnectType.RIGHT,
        "t": ConnectType.TOP, "b": ConnectType.BOTTOM
    }

    def __init__(self, filename: str):
        self.varTable: VarTable = VarTable()
        self.connectTable: ConnectTable = ConnectTable()
        self.filename = filename
        self.currentLine = NoneLine

    def compile(self, filename: str = "flowOutput"):
        try:
            self.parseFile()
            # 代码生成前, 先检查关系完整性
            self.connectTable.checkIntegrity(self.varTable)
            self.genCode(filename)
            print("Compile Finish.\n0 Error 0 Warning.")
        finally:
            pass
        # except Exception as e:
        #     sys.stderr.write("Compile Failed.\n")
        #     sys.stderr.write(str(e))

    def parseFile(self):
        with open(self.filename, "r", encoding="utf8") as f:
            num = 0
            for line in f.readlines():
                num += 1
                if not line.isspace():
                    self.parseLine(Line(num, line.replace("\n", "")))

    def parseLine(self, line: Line):
        self.currentLine = line
        nodes = line.value.split()

        if len(nodes) < 2:
            raise CheckException(f"Error: Line {line.num}: The num of nodes less than 2")

        for i in range(len(nodes) - 1):
            node = self.parseNode(nodes[i])
            varFst: Var = self.varTable.getVarByNode(node)
            varSnd: Var = self.varTable.getVarByNode(self.parseNode(nodes[i + 1]))
            self.connectTable.addConnect(varFst.num, varSnd.num, node.connectType)

    def parseNode(self, varStr: str) -> Node:
        # 只要此部分代码被执行, 在if中定义的变量离开if语句依然有效
        if varStr[0] == '<':
            varType = VarType.CONDITION
        elif varStr[0] == '[':
            varType = VarType.OPERATION
        elif varStr[0] == '{':
            varType = VarType.SUBROUTINE
        elif varStr == "st":
            return Node("", VarType.START, ConnectType.NORMAL)
        elif varStr == "ed":
            return Node("", VarType.END, ConnectType.NORMAL)
        else:
            raise CheckException(f"Undefined type of {varStr}")

        varStr = self.removeBrackets(varStr)  # 移除两端的括号
        if ":" in varStr:
            info, typename = varStr.split(":")
            return Node(info, varType, self.connectNameDict[typename])
        else:
            return Node(varStr, varType, ConnectType.NORMAL)

    @staticmethod
    def removeBrackets(s: str):
        colonIdx = s.find(":")
        if colonIdx != -1:
            s = s[1:colonIdx - 1] + s[colonIdx:]
        else:
            s = s[1:-1]
        return s

    def genCode(self, filename: str):
        with open(filename, "w", encoding="utf8") as f:
            self.varTable.genCode(f)
            f.write("\n")
            self.connectTable.genCode(self.varTable, f)


class CheckException(Exception):
    def __init__(self, info):
        Exception.__init__(self, info)


if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) >= 2:
        parser = Parser(sys.argv[1])
        parser.compile(sys.argv[1] + "_out")
    else:
        parser = Parser("flowTest/hashMapMain")
        parser.compile("flowOutput")

    # 优化方案
    # 分支节点选择最长的路径作为向下的路径
    # 即从分支节点出发, 到两个分支的交汇点, 选择路径最长的分支
    # 但是如果某个路径为0, 则依然选择0路径为向下路径
