escapeChar = frozenset(['_', '\\'])


def main():
    while True:
        code = input("请输入待转化的LaTeX代码\n")
        if code == "":
            break
        else:
            print("".join(map(do_escape, code)))


def do_escape(c):
    if c in escapeChar:
        return "\\" + c
    else:
        return c


if __name__ == "__main__":
    main()
