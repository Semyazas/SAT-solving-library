from task1.Syntax_tree import read_file

def read_DIMACS(filename: str) -> tuple[list[list[int]], list[int]]:
    clauses = []
    variables = []
    lines = read_file(filename)

    for line in lines:
    
        if line.startswith('p'):
            num_vars, num_clauses = int(line.split()[2]),int(line.split()[3])
            variables = [i+1 for i in range(num_vars)]

        if line.split()[0].lstrip("+-").isnumeric():
            clause = list(map(int, line.split()[:-1]))
            clauses.append(clause)
    return clauses, variables


if __name__ == '__main__':
    print(read_DIMACS("test_file_dimacs.txt"))


        
        