import subprocess  # nosec
import sys


def get_cpp_include_paths():
    # run `clang -v -E -x c++ - -v < /dev/null 2>&1` to get the include paths   # nosec
    result = subprocess.run(
        ["clang", "-v", "-E", "-x", "c++", "-", "-v"],
        input=b"",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )  # nosec
    output = result.stderr.decode(sys.getdefaultencoding())
    search_list = output.split("#include <...> search starts here:\n")[-1].split(
        "End of search list."
    )[0]
    include_paths = []
    for line in search_list.split("\n"):
        line = line.strip()
        if line != "":
            include_paths.append(line)

    return include_paths
