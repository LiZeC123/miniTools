escapeChar = frozenset(['_','\\'])

def main():
    while True:
        code = input("请输入待转化的LaTeX代码\n")
        if code == "":
            break
        else:
            print("".join(map(doEscape,code)))

def doEscape(c):
    if c in escapeChar:
        return "\\"+c
    else:
        return c


if __name__ == "__main__":
    main()